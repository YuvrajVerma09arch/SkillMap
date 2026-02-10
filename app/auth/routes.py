from flask import Blueprint, render_template, redirect, url_for, flash, request,session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager ,oauth
from app.models import User

auth = Blueprint('auth', __name__)

# This helps Flask-Login find the user in the DB
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 1. ROLE SELECTION
@auth.route('/role-select')
def role_select():
    return render_template('auth/roleselect.html')

# 2. REGISTER (FIXED)
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    # Check if we are coming from Google Auth
    oauth_email = session.get('oauth_email')
    oauth_name = session.get('oauth_name')

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Create User
        user = User(name=username, email=email, role=role)
        
        # If it's a standard registration, hash the password
        # If it's Google (password might be empty/dummy), handle logic:
        if password:
            user.set_password(password)
        else:
            # If Google user didn't set a password (optional logic), set a random secure one
            import secrets
            user.set_password(secrets.token_urlsafe(16))

        db.session.add(user)
        db.session.commit()
        
        # Cleanup Session
        session.pop('oauth_email', None)
        session.pop('oauth_name', None)

        login_user(user)
        
        # Redirect to Setup
        return redirect(url_for('main.setup_profile'))

    # If GET request, pass oauth data to pre-fill the form
    return render_template('auth/login.html', oauth_email=oauth_email, oauth_name=oauth_name)

# 3. LOGIN
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            
            if user.role == 'recruiter':
               return redirect(url_for('main.recruiter_dashboard'))
            else:
             return redirect(url_for('jobs.job_feed'))
            
    return render_template('auth/login.html')

@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

# app/auth/routes.py

@auth.route('/login/google')
def google_login():
    # 1. CAPTURE THE ROLE (if provided)
    # This comes from the button link: /login/google?role=seeker
    role = request.args.get('role')
    
    if role:
        session['pending_role'] = role  # <--- SAVE TO SESSION
    
    client = oauth.create_client('google')
    if not client:
        flash("Google Login not configured.", "danger")
        return redirect(url_for('auth.login'))

    redirect_uri = url_for('auth.google_callback', _external=True)
    return client.authorize_redirect(redirect_uri)

@auth.route('/google/callback')
def google_callback():
    client = oauth.create_client('google')
    try:
        token = client.authorize_access_token()
        user_info = token.get('userinfo')
        
        email = user_info['email']
        name = user_info['name']

        # SCENARIO A: USER ALREADY EXISTS (LOGIN)
        user = User.query.filter_by(email=email).first()

        if user:
            login_user(user)
            # Check role and redirect to dashboard
            if user.role == 'recruiter':
                return redirect(url_for('main.recruiter_dashboard'))
            else:
                return redirect(url_for('jobs.job_feed'))
        
        else:
            # SCENARIO B: NEW USER (SIGNUP)
            # Check if we remember the role from before they left
            pending_role = session.get('pending_role')
            
            if pending_role:
                # WE KNOW THE ROLE! Create account immediately.
                new_user = User(name=name, email=email, role=pending_role)
                
                # Set a random password for security (since they use Google)
                import secrets
                new_user.set_password(secrets.token_urlsafe(16)) 
                
                db.session.add(new_user)
                db.session.commit()
                
                login_user(new_user)
                session.pop('pending_role', None) # Clean up
                
                flash("Account created! Let's build your profile.", "success")
                return redirect(url_for('main.setup_profile'))
            
            else:
                # WE DON'T KNOW THE ROLE -> Go to Select Page
                session['oauth_email'] = email
                session['oauth_name'] = name
                session['oauth_provider'] = 'google'
                
                return redirect(url_for('auth.role_select'))

    except Exception as e:
        flash(f"Google Auth Error: {str(e)}", "danger")
        return redirect(url_for('auth.login'))