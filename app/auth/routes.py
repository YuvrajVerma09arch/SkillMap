import secrets
from urllib.parse import urlsplit, urlunsplit

from flask import Blueprint, request, jsonify, session, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager, oauth, limiter
from app.models import User

auth = Blueprint('auth', __name__)

VALID_ROLES = {'seeker', 'recruiter'}


# This helps Flask-Login find the user in the DB
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _user_payload(user):
    """Serialize the current user for the SPA."""
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role,
        'tier': user.tier,
        'credits': user.credits,
        'has_seeker_profile': user.seeker_profile is not None,
        'has_recruiter_profile': user.recruiter_profile is not None,
        'resume_file': (
            user.seeker_profile.resume_file
            if user.seeker_profile and user.role == 'seeker' else None
        ),
    }


# ─── 1. CURRENT USER (session probe used by the SPA on boot) ────────────────
@auth.route('/api/auth/me')
def me():
    if current_user.is_authenticated:
        return jsonify({'authenticated': True, 'user': _user_payload(current_user)})
    return jsonify({'authenticated': False, 'user': None})


# ─── 2. REGISTER ────────────────────────────────────────────────────────────
@auth.route('/api/auth/register', methods=['POST'])
@limiter.limit('10 per minute')
def register():
    if current_user.is_authenticated:
        return jsonify({'user': _user_payload(current_user)}), 200

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = (data.get('role') or '').strip()

    if not username or not email or not password:
        return jsonify({'error': 'Name, email and password are required.'}), 400
    if role not in VALID_ROLES:
        return jsonify({'error': 'A valid role (seeker or recruiter) is required.'}), 400
    if '@' not in email:
        return jsonify({'error': 'A valid email address is required.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered. Please sign in instead.'}), 409

    user = User(name=username, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Cleanup any pending OAuth session keys
    session.pop('oauth_email', None)
    session.pop('oauth_name', None)
    session.pop('pending_role', None)

    login_user(user)
    return jsonify({'user': _user_payload(user)}), 201


# ─── 3. LOGIN ───────────────────────────────────────────────────────────────
@auth.route('/api/auth/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    if current_user.is_authenticated:
        return jsonify({'user': _user_payload(current_user)}), 200

    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        # Bug fix: previously failed logins re-rendered silently with no message.
        return jsonify({'error': 'Invalid email or password.'}), 401

    login_user(user)
    return jsonify({'user': _user_payload(user)}), 200


# ─── 4. LOGOUT ──────────────────────────────────────────────────────────────
@auth.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'ok': True})


# ─── 5. GOOGLE OAUTH (browser redirect flow; lands back on the SPA) ─────────
def _spa_redirect(path=''):
    """Send the browser back to the SPA after OAuth.

    Split-host deploys (SPA on e.g. Vercel, API here) have no frontend on
    this origin, so a relative redirect would 404 — prefix FRONTEND_URL when
    configured. Locally (no FRONTEND_URL) it stays a plain relative path.
    """
    base = current_app.config.get('FRONTEND_URL') or ''
    return redirect(f'{base}{path}')


@auth.route('/login/google')
def google_login():
    role = request.args.get('role')
    if role in VALID_ROLES:
        session['pending_role'] = role

    client = oauth.create_client('google')
    if not client:
        return _spa_redirect('/login?error=Google login is not configured.')

    # Pinned redirect URI: Google Console only registers the 127.0.0.1 host,
    # so url_for's Host-derived value (e.g. localhost:5000 via the Vite proxy)
    # would be rejected with redirect_uri_mismatch.
    redirect_uri = current_app.config.get('GOOGLE_REDIRECT_URI') or url_for(
        'auth.google_callback', _external=True
    )
    # Hop: if the browser entered on a different host than the pinned callback
    # host (localhost:5173 -> 127.0.0.1:5000), re-issue the request on the
    # registered host so the OAuth state cookie is set for the same origin
    # that will receive /google/callback.
    registered_host = urlsplit(redirect_uri).netloc
    if request.host != registered_host:
        pinned = urlsplit(redirect_uri)
        hop = urlunsplit((
            pinned.scheme, registered_host, request.path,
            request.query_string.decode(), '',
        ))
        return redirect(hop)
    return client.authorize_redirect(redirect_uri, prompt='select_account')


@auth.route('/google/callback')
def google_callback():
    client = oauth.create_client('google')
    try:
        token = client.authorize_access_token()
        user_info = token.get('userinfo') or {}

        email = (user_info.get('email') or '').strip().lower()
        name = user_info.get('name') or email.split('@')[0]

        if not email:
            return _spa_redirect('/login?error=Google account has no email.')

        # SCENARIO A: USER ALREADY EXISTS (LOGIN)
        user = User.query.filter_by(email=email).first()
        if user:
            login_user(user)
            return _spa_redirect('/')

        # SCENARIO B: NEW USER
        pending_role = session.get('pending_role')
        if pending_role in VALID_ROLES:
            new_user = User(name=name, email=email, role=pending_role)
            new_user.set_password(secrets.token_urlsafe(16))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            session.pop('pending_role', None)
            # Fresh accounts must complete profile setup first
            return _spa_redirect('/setup-profile?first=1')

        # SCENARIO C: ROLE UNKNOWN -> role-select page (SPA)
        session['oauth_email'] = email
        session['oauth_name'] = name
        session['oauth_provider'] = 'google'
        return _spa_redirect('/role-select?oauth=1')

    except Exception:
        current_app.logger.exception('google oauth callback failed')
        return _spa_redirect('/login?error=Google auth failed. Please try again.')


# ─── 6. OAUTH PREFILL DATA (SPA register form reads this) ───────────────────
@auth.route('/api/auth/oauth-prefill')
def oauth_prefill():
    if session.get('oauth_email'):
        return jsonify({
            'email': session.get('oauth_email'),
            'name': session.get('oauth_name'),
            'provider': session.get('oauth_provider', 'google'),
        })
    return jsonify({'email': None, 'name': None, 'provider': None})
