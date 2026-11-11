import json
import os
import re
import uuid

from flask import Blueprint, request, jsonify, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# --- DB & MODELS IMPORT ---
from app import db, limiter
from app.models import SeekerProfile, RecruiterProfile, JobPost, Application, User
from app.utils.email_service import send_roadmap_email

# --- ALGORITHMS IMPORT ---
from app.utils.heap import MaxHeap
from app.utils.matcher import calculate_match_score

main = Blueprint('main', __name__)


# ─── HELPERS ────────────────────────────────────────────────────────────────
def uploads_dir():
    """Absolute upload folder inside the app's instance dir (F1 fix).

    Uploads previously lived under static_folder/uploads, which Flask serves
    publicly at /static/uploads/<filename> — anyone could fetch any user's
    resume/profile picture without logging in (only filename entropy stood
    between an attacker and the whole PII store). Uploads now live OUTSIDE the
    static tree and are only reachable through the authenticated
    /api/files/... routes below, which check ownership/relationships.
    """
    folder = os.path.join(current_app.instance_path, 'uploads')
    os.makedirs(folder, exist_ok=True)
    return folder


RESUME_EXTENSIONS = {'.pdf', '.doc', '.docx'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}
MAX_RESUME_BYTES = 5 * 1024 * 1024
MAX_IMAGE_BYTES = 2 * 1024 * 1024

_MAGIC_CHECKS = {
    '.pdf': lambda head: head.startswith(b'%PDF'),
    '.png': lambda head: head.startswith(b'\x89PNG\r\n\x1a\n'),
    '.jpg': lambda head: head.startswith(b'\xff\xd8\xff'),
    '.jpeg': lambda head: head.startswith(b'\xff\xd8\xff'),
    '.webp': lambda head: head[:4] == b'RIFF' and head[8:12] == b'WEBP',
    '.doc': lambda head: head.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'),
    '.docx': lambda head: head.startswith(b'PK\x03\x04'),
}


def validate_upload(file, allowed_extensions, max_bytes):
    """Reject uploads whose extension/magic bytes/size don't match.

    Files saved under static/uploads are served back by Flask with no
    content sniffing, so an uploaded .html/.svg would execute script in our
    origin (stored XSS -> session theft). Extension allowlist + magic-byte
    check closes that.
    """
    filename = secure_filename(file.filename or '')
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        return None, f'File type not allowed. Allowed: {", ".join(sorted(allowed_extensions))}'
    head = file.stream.read(16)
    file.stream.seek(0)
    checker = _MAGIC_CHECKS.get(ext)
    if checker and not checker(head):
        return None, 'File content does not match its extension.'
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > max_bytes:
        return None, f'File too large. Max {max_bytes // (1024 * 1024)}MB.'
    if size == 0:
        return None, 'Empty file.'
    return filename, None


def seeker_profile_payload(profile, private=False):
    """Seeker profile for API responses.

    F1 fix: phone and resume_file are contact/document PII. They are only
    included for the profile owner (private=True) or for a recruiter who has
    an Application linking them to this seeker (see view_profile).
    """
    if not profile:
        return None
    payload = {
        'headline': profile.headline,
        'location': profile.location,
        'experience_years': profile.experience_years,
        'education_level': profile.education_level,
        'skills': profile.skills or [],
        'projects': profile.projects or [],
        'profile_pic': profile.profile_pic,
        'linkedin_url': profile.linkedin_url,
        'portfolio_url': profile.portfolio_url,
    }
    payload['phone'] = profile.phone if private else None
    payload['resume_file'] = profile.resume_file if private else None
    return payload


def recruiter_profile_payload(profile, include_contact=False):
    """Recruiter profile for API responses.

    F5 fix: work_email is only returned to the owner or to a seeker who has
    applied to that recruiter's job.
    """
    if not profile:
        return None
    return {
        'recruiter_name': profile.recruiter_name,
        'role_title': profile.role_title,
        'work_email': profile.work_email if include_contact else None,
        'company_name': profile.company_name,
        'industry': profile.industry,
        'company_size': profile.company_size,
        'location': profile.location,
        'website': profile.website,
        'is_verified': profile.is_verified,
    }


def recruiter_can_view_seeker(recruiter_user, seeker_user):
    """True only when an Application ties this recruiter's job to this seeker."""
    if recruiter_user.role != 'recruiter' or not recruiter_user.recruiter_profile:
        return False
    if seeker_user.role != 'seeker':
        return False
    return Application.query.join(
        JobPost, Application.job_id == JobPost.id
    ).filter(
        JobPost.recruiter_id == recruiter_user.recruiter_profile.id,
        Application.seeker_id == seeker_user.id,
    ).count() > 0


def seeker_can_view_recruiter(seeker_user, recruiter_user):
    """True only when this seeker applied to one of that recruiter's jobs."""
    if seeker_user.role != 'seeker':
        return False
    if recruiter_user.role != 'recruiter' or not recruiter_user.recruiter_profile:
        return False
    return Application.query.join(
        JobPost, Application.job_id == JobPost.id
    ).filter(
        JobPost.recruiter_id == recruiter_user.recruiter_profile.id,
        Application.seeker_id == seeker_user.id,
    ).count() > 0


def parse_education(education_level):
    """'Degree - College (Year)' -> {'degree','college','year'} (never crashes)."""
    parsed = {'degree': '', 'college': '', 'year': ''}
    if not education_level:
        return parsed
    try:
        parts = education_level.split(' - ', 1)
        parsed['degree'] = parts[0]
        if len(parts) > 1:
            rest = parts[1]
            college_part = rest.rsplit(' (', 1)
            if len(college_part) > 1:
                parsed['college'] = college_part[0]
                parsed['year'] = college_part[1].replace(')', '')
            else:
                parsed['college'] = rest
    except Exception:
        pass
    return parsed


# ─── HOME (metadata only; SPA renders the landing page) ─────────────────────
@main.route('/api/health')
def health():
    return jsonify({'ok': True, 'service': 'skillmap'})


# ─── 1. SEEKER PROFILE ──────────────────────────────────────────────────────
@main.route('/api/profile/seeker', methods=['GET'])
@login_required
def get_seeker_profile():
    profile = current_user.seeker_profile
    return jsonify({
        'profile': seeker_profile_payload(profile, private=True),
        'parsed_edu': parse_education(profile.education_level if profile else None),
        'user': {'name': current_user.name},
    })


@main.route('/api/profile/seeker', methods=['POST'])
@login_required
def save_seeker_profile():
    try:
        data = request.get_json(silent=True) or {}
        form = request.form

        def pick(key, default=None):
            if key in data:
                return data.get(key)
            if key in form:
                return form.get(key)
            return default

        full_name = (pick('full_name') or '').strip()
        phone = pick('phone')
        location = pick('location')
        experience_years = pick('experience_years')
        education_level = pick('qualification')
        college = pick('college')
        grad_year = pick('grad_year')
        linkedin = pick('linkedin')
        portfolio = pick('portfolio')
        headline = pick('headline')

        # skills: JSON array or repeated form field
        if 'skills' in data and isinstance(data.get('skills'), list):
            skills = [str(s).strip() for s in data['skills'] if str(s).strip()]
        else:
            skills = [s.strip() for s in form.getlist('skills') if s.strip()]

        if not full_name:
            return jsonify({'error': 'Full name is required.'}), 400

        project_title = pick('project_title')
        project_link = pick('project_link')
        projects_data = []
        if project_title and project_link:
            projects_data = [{'title': project_title, 'link': project_link}]
        elif isinstance(data.get('projects'), list):
            projects_data = data['projects']

        # Update User Name
        current_user.name = full_name
        db.session.add(current_user)

        # Get/Create Profile
        profile = SeekerProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = SeekerProfile(user_id=current_user.id)

        profile.phone = phone
        profile.location = location
        profile.experience_years = experience_years
        profile.education_level = f"{education_level or ''} - {college or ''} ({grad_year or ''})"
        profile.skills = skills
        profile.linkedin_url = linkedin
        profile.portfolio_url = portfolio
        profile.headline = headline

        if projects_data:
            profile.projects = projects_data

        folder = uploads_dir()

        if 'profile_pic' in request.files:
            pic = request.files['profile_pic']
            if pic and pic.filename != '':
                pic_filename, pic_error = validate_upload(pic, IMAGE_EXTENSIONS, MAX_IMAGE_BYTES)
                if pic_error:
                    return jsonify({'error': f'Profile picture: {pic_error}'}), 400
                pic_unique_name = f"pic_{current_user.id}_{uuid.uuid4().hex[:8]}_{pic_filename}"
                pic.save(os.path.join(folder, pic_unique_name))
                profile.profile_pic = pic_unique_name

        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '':
                filename, resume_error = validate_upload(file, RESUME_EXTENSIONS, MAX_RESUME_BYTES)
                if resume_error:
                    return jsonify({'error': f'Resume: {resume_error}'}), 400
                unique_name = f"{current_user.id}_{uuid.uuid4().hex[:8]}_{filename}"
                file.save(os.path.join(folder, unique_name))
                profile.resume_file = unique_name

        db.session.add(profile)
        db.session.commit()

        return jsonify({'profile': seeker_profile_payload(profile, private=True), 'user': {'name': current_user.name}})
    except Exception:
        db.session.rollback()
        current_app.logger.exception('seeker profile save failed')
        return jsonify({'error': 'Could not save profile. Please try again.'}), 500


# ─── 2. RECRUITER PROFILE ───────────────────────────────────────────────────
@main.route('/api/profile/recruiter', methods=['GET'])
@login_required
def get_recruiter_profile():
    return jsonify({'profile': recruiter_profile_payload(current_user.recruiter_profile, include_contact=True)})


@main.route('/api/profile/recruiter', methods=['POST'])
@login_required
def save_recruiter_profile():
    try:
        data = request.get_json(silent=True) or {}

        company_name = (data.get('company_name') or '').strip()
        if not company_name:
            return jsonify({'error': 'Company name is required.'}), 400

        profile = RecruiterProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = RecruiterProfile(user_id=current_user.id)

        profile.company_name = company_name
        profile.industry = data.get('industry')
        profile.company_size = data.get('size') or data.get('company_size')
        profile.location = data.get('location')
        profile.website = data.get('website')
        profile.recruiter_name = data.get('recruiter_name')
        profile.role_title = data.get('role_title')
        profile.work_email = data.get('work_email')

        if data.get('name'):
            current_user.name = data['name']
            db.session.add(current_user)

        db.session.add(profile)
        db.session.commit()
        return jsonify({'profile': recruiter_profile_payload(profile, include_contact=True)})
    except Exception:
        db.session.rollback()
        current_app.logger.exception('recruiter profile save failed')
        return jsonify({'error': 'Could not save profile. Please try again.'}), 500


# ─── 3. PUBLIC PROFILE VIEWS ────────────────────────────────────────────────
@main.route('/api/profiles/<int:user_id>', methods=['GET'])
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)

    is_owner = current_user.id == user.id
    # Recruiters can still browse the talent feed, but phone/resume only
    # unlock when an Application ties them to this seeker.
    has_relationship = recruiter_can_view_seeker(current_user, user)

    # Security: only the owner or a recruiter may view a seeker profile
    if not is_owner and current_user.role != 'recruiter':
        return jsonify({'error': 'Unauthorized.'}), 403

    profile = user.seeker_profile
    if user.role == 'seeker' and not profile:
        return jsonify({'error': 'This user has not set up their profile yet.', 'needs_setup': True}), 404

    return jsonify({
        'user': {'id': user.id, 'name': user.name, 'role': user.role},
        'profile': seeker_profile_payload(profile, private=is_owner or has_relationship),
        'is_own_profile': is_owner,
        'is_recruiter': current_user.role == 'recruiter',
        'parsed_edu': parse_education(profile.education_level if profile else None),
    })


@main.route('/api/companies/<int:user_id>', methods=['GET'])
@login_required
def view_company(user_id):
    # SECURITY: owner OR a job seeker may view a company profile.
    if current_user.id != user_id and current_user.role != 'seeker':
        return jsonify({'error': 'Unauthorized.'}), 403

    is_owner = current_user.id == user_id
    recruiter_user = User.query.get(user_id)
    include_contact = is_owner or (
        recruiter_user is not None and seeker_can_view_recruiter(current_user, recruiter_user)
    )

    profile = RecruiterProfile.query.filter_by(user_id=user_id).first_or_404()
    jobs = JobPost.query.filter_by(recruiter_id=profile.id, is_active=True).all()
    return jsonify({
        'profile': recruiter_profile_payload(profile, include_contact=include_contact),
        'jobs': [
            {
                'id': j.id, 'title': j.title, 'location': j.location,
                'job_type': j.job_type,
                'applicant_count': len(j.applications),
            }
            for j in jobs
        ],
        'is_owner': current_user.id == user_id,
        'total_applicants': sum(len(j.applications) for j in jobs),
    })


# ─── 3b. AUTHENTICATED FILE DOWNLOADS (F1 fix) ──────────────────────────────
# Uploads used to be served straight from /static/uploads with no auth at all.
# They now live outside the static tree and are only reachable here.
def _serve_upload(filename, download_name=None):
    """Send a file from the private uploads dir (basename-only, no traversal)."""
    from flask import send_from_directory

    safe_name = os.path.basename(filename or '')
    if not safe_name:
        return jsonify({'error': 'File not found.'}), 404
    folder = uploads_dir()
    if not os.path.isfile(os.path.join(folder, safe_name)):
        return jsonify({'error': 'File not found.'}), 404
    return send_from_directory(
        folder, safe_name, as_attachment=True,
        download_name=download_name or safe_name,
    )


@main.route('/api/files/resume/<path:filename>', methods=['GET'])
@login_required
def download_resume(filename):
    """Resume download: owner, OR a recruiter with an Application to the seeker."""
    safe_name = os.path.basename(filename or '')
    # Filenames are stored as '<user_id>_<hex>_<name>'; recover the owner id.
    owner_id_str = safe_name.split('_', 1)[0]
    owner_id = int(owner_id_str) if owner_id_str.isdigit() else None
    if owner_id is None:
        return jsonify({'error': 'File not found.'}), 404

    if current_user.id == owner_id:
        allowed = True
    else:
        owner = User.query.get(owner_id)
        allowed = owner is not None and recruiter_can_view_seeker(current_user, owner)

    if not allowed:
        return jsonify({'error': 'Unauthorized.'}), 403
    return _serve_upload(safe_name)


@main.route('/api/files/pic/<path:filename>', methods=['GET'])
@login_required
def download_profile_pic(filename):
    """Profile picture download: any logged-in user (public-ish avatar)."""
    safe_name = os.path.basename(filename or '')
    if not safe_name.startswith('pic_'):
        return jsonify({'error': 'File not found.'}), 404
    return _serve_upload(safe_name)


# ─── 4. RECRUITER DASHBOARD (heap-ranked candidates, with emails) ───────────
@main.route('/api/recruiter/dashboard', methods=['GET'])
@login_required
def recruiter_dashboard():
    if current_user.role != 'recruiter':
        return jsonify({'error': 'Recruiters only.'}), 403

    profile = current_user.recruiter_profile
    if not profile:
        return jsonify({'needs_setup': True}), 404

    jobs = JobPost.query.filter_by(recruiter_id=profile.id).order_by(JobPost.posted_at.desc()).all()

    total_applicants = 0
    shortlisted_count = 0
    applicant_heap = MaxHeap()

    for job in jobs:
        job_apps = Application.query.filter_by(job_id=job.id).all()
        total_applicants += len(job_apps)

        for application in job_apps:
            if application.status == 'Shortlisted':
                shortlisted_count += 1

            seeker_profile = application.seeker
            if seeker_profile:
                seeker_user = seeker_profile.user
                score = calculate_match_score(seeker_profile.skills, job.required_skills)
                # Bug fix: template used to render candidate.email but the field
                # was never included -> always blank. Now included.
                candidate_data = {
                    'name': seeker_user.name,
                    'email': seeker_user.email,
                    'user_id': seeker_user.id,
                    'role': job.title,
                    'match_score': score,
                }
                applicant_heap.push((score, candidate_data))

    top_candidates = applicant_heap.get_top_n(5)

    return jsonify({
        'stats': {
            'total_applicants': total_applicants,
            'active_jobs': len(jobs),
            'interviews': shortlisted_count,
            'credits': current_user.credits,
        },
        'jobs': [
            {
                'id': j.id, 'title': j.title, 'location': j.location,
                'job_type': j.job_type, 'salary_range': j.salary_range,
                'applicant_count': len(j.applications),
                'posted_at': j.posted_at.isoformat() if j.posted_at else None,
            }
            for j in jobs
        ],
        'candidates': top_candidates,
    })


# ─── 5. TALENT FEED ─────────────────────────────────────────────────────────
@main.route('/api/talent', methods=['GET'])
@login_required
def talent_feed():
    if current_user.role != 'recruiter':
        return jsonify({'error': 'Recruiters only.'}), 403

    seekers = db.session.query(User).join(SeekerProfile).filter(User.role == 'seeker').all()
    return jsonify({
        'seekers': [
            {
                'id': u.id,
                'name': u.name,
                'headline': u.seeker_profile.headline,
                'location': u.seeker_profile.location,
                'skills': u.seeker_profile.skills or [],
            }
            for u in seekers
        ]
    })


# ─── 6. ROADMAP GENERATOR ───────────────────────────────────────────────────
@main.route('/api/tools/roadmap', methods=['POST'])
@login_required
def roadmap():
    from app.utils.roadmap_gen import generate_roadmap

    data = request.get_json(silent=True) or {}
    current_skills = (data.get('current_skills') or '').strip()
    target_role = (data.get('target_role') or '').strip()

    # Bug fix: validate BEFORE any credit is spent.
    if not current_skills or not target_role:
        return jsonify({'error': 'Current skills and target role are required.'}), 400

    if not current_user.has_credits(ROADMAP_COST):
        return jsonify({'error': 'Not enough credits. Please upgrade.', 'redirect': '/pricing'}), 402

    # F2 fix: charge atomically BEFORE the (slow) AI call so N concurrent
    # requests can never all pass the same pre-check and overdraw the balance.
    # The credit is refunded if the generation fails or returns nothing.
    if not current_user.deduct_credits(ROADMAP_COST):
        return jsonify({'error': 'Not enough credits. Please upgrade.', 'redirect': '/pricing'}), 402

    try:
        roadmap_data = generate_roadmap(current_skills, target_role)
    except Exception:
        current_app.logger.exception('roadmap generation failed')
        current_user.refund_credits(ROADMAP_COST)
        return jsonify({'error': 'Roadmap generation failed. Please try again.'}), 502

    # An empty/failed generation must NOT cost a credit.
    if not roadmap_data:
        current_user.refund_credits(ROADMAP_COST)
        return jsonify({'error': 'The AI returned no roadmap. Please try again.'}), 502

    session['latest_roadmap'] = roadmap_data
    session['target_role'] = target_role

    return jsonify({'roadmap': roadmap_data, 'target_role': target_role, 'credits': current_user.credits})


# ─── 7. RESUME CHECKER ──────────────────────────────────────────────────────
# Failure markers returned by analyze_resume that indicate no real analysis happened
_FAILED_MARKERS = ('API Key Missing', 'Unreadable PDF', 'AI Analysis Failed')

# Credit pricing (free tier grants 5 credits; a resume analysis costs 5)
RESUME_CHECK_COST = 5
ROADMAP_COST = 1


@main.route('/api/tools/resume-check', methods=['POST'])
@login_required
def resume_checker():
    from app.utils.resume_parser import analyze_resume

    data = request.get_json(silent=True) or {}
    form = request.form

    def pick(key, default=None):
        if key in data:
            return data.get(key)
        if key in form:
            return form.get(key)
        return default

    # The SPA posts multipart/form-data (file + fields); also accept JSON.
    job_description = pick('job_description')
    raw_existing = pick('use_existing')
    use_existing = (
        str(raw_existing).lower() in ('1', 'true', 'yes')
        if raw_existing is not None else False
    )

    folder = uploads_dir()
    save_path = None
    is_temp_file = False
    charged = False  # tracks whether a credit was taken (so failures refund it)

    try:
        if use_existing:
            if current_user.role != 'seeker' or not current_user.seeker_profile \
                    or not current_user.seeker_profile.resume_file:
                return jsonify({'error': 'No saved resume on your profile. Please upload one.'}), 400
            save_path = os.path.join(folder, current_user.seeker_profile.resume_file)
            if not os.path.exists(save_path):
                return jsonify({'error': 'Saved resume was cleared from the server. Please upload it again.'}), 400
        else:
            if 'resume' not in request.files:
                return jsonify({'error': 'Please upload a resume.'}), 400
            file = request.files['resume']
            if not file or file.filename == '':
                return jsonify({'error': 'Please upload a resume.'}), 400
            filename, upload_error = validate_upload(file, RESUME_EXTENSIONS, MAX_RESUME_BYTES)
            if upload_error:
                return jsonify({'error': upload_error}), 400
            save_path = os.path.join(folder, f"temp_{uuid.uuid4().hex[:6]}_{filename}")
            file.save(save_path)
            is_temp_file = True

        # Bug fix: a missing JD used to silently reach the AI as None.
        if not job_description or not str(job_description).strip():
            return jsonify({'error': 'A job description is required for analysis.'}), 400

        # F2 fix: charge atomically BEFORE the (slow) AI call so parallel
        # requests can't all pass a stale pre-check and overdraw the balance.
        # The credit is refunded on any failure path below.
        if not current_user.has_credits(RESUME_CHECK_COST):
            return jsonify({'error': 'Not enough credits. Please upgrade.', 'redirect': '/pricing'}), 402

        if not current_user.deduct_credits(RESUME_CHECK_COST):
            return jsonify({'error': 'Not enough credits. Please upgrade.', 'redirect': '/pricing'}), 402
        charged = True

        results = analyze_resume(save_path, str(job_description))
        if 'match_score' not in results:
            results['match_score'] = 0

        # Never charge a credit when the AI run actually failed.
        if any(m in (results.get('missing_required_skills') or []) for m in _FAILED_MARKERS):
            current_user.refund_credits(RESUME_CHECK_COST)
            charged = False
            return jsonify({'error': 'Analysis failed. You have not been charged.', 'results': results}), 502

        return jsonify({'results': results, 'credits': current_user.credits})

    except Exception:
        current_app.logger.exception('resume check failed')
        if charged:
            current_user.refund_credits(RESUME_CHECK_COST)
        return jsonify({'error': 'An error occurred while processing the file. Please try again.'}), 500
    finally:
        if is_temp_file and save_path and os.path.exists(save_path):
            try:
                os.remove(save_path)
            except Exception as cleanup_error:
                print(f'Failed to clean up temp file: {cleanup_error}')


# ─── 9. EMAIL ROADMAP ───────────────────────────────────────────────────────
@main.route('/api/emails/roadmap', methods=['POST'])
@login_required
def trigger_email():
    roadmap_data = session.get('latest_roadmap')
    target_role = session.get('target_role')

    if not roadmap_data:
        return jsonify({'error': 'No roadmap found to email. Please generate one first.'}), 400

    success, msg = send_roadmap_email(
        current_user.email, current_user.name, target_role, roadmap_data
    )
    if success:
        return jsonify({'sent': True, 'email': current_user.email})
    return jsonify({'sent': False, 'error': msg}), 502


# ─── 10. COMPANY PREP PACK (free, login-gated, cached per company+role) ──────
@main.route('/api/prep/companies', methods=['POST'])
@login_required
@limiter.limit('30 per minute')
def prep_companies():
    from sqlalchemy import text as sqltext

    data = request.get_json(silent=True) or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({'error': 'Search query is required.'}), 400

    pat = f'%{query}%'
    rows = db.session.execute(sqltext("""
        SELECT c.slug, c.name,
               (c.meta ? 'rounds') AS has_rounds,
               (SELECT count(*) FROM questions q WHERE q.company_id = c.id) AS n
        FROM companies c
        WHERE (c.name ILIKE :pat OR c.slug ILIKE :pat
           OR c.aliases::text ILIKE :pat)
          AND c.slug <> 'role-only'   -- sentinel for role-only packs, never a pick
        ORDER BY has_rounds DESC, n DESC, c.name
        LIMIT 12
    """), {'pat': pat}).fetchall()

    return jsonify({'companies': [
        {'slug': r[0], 'name': r[1], 'has_rounds': bool(r[2]), 'question_count': r[3]}
        for r in rows
    ]})


@main.route('/api/prep/generate', methods=['POST'])
@login_required
@limiter.limit('6 per minute')
def prep_generate():
    from sqlalchemy import text as sqltext
    from app.utils.prep_bot import embed_query, fetch_salary_band, synthesize_pack

    data = request.get_json(silent=True) or {}
    slug = (data.get('company_slug') or '').strip()
    role = (data.get('role') or '').strip()[:80]

    if not role:
        return jsonify({'error': 'Role is required.'}), 400
    role_only = not slug

    if role_only:
        # Company not in the corpus → pack against a sentinel "Any company"
        # row so the (company_id, role) cache key keeps working unchanged.
        db.session.execute(sqltext("""
            INSERT INTO companies (slug, name, meta)
            VALUES ('role-only', 'Any company', '{}'::jsonb)
            ON CONFLICT (slug) DO NOTHING
        """))
        db.session.commit()
        company = db.session.execute(sqltext(
            "SELECT id, name, meta FROM companies WHERE slug = 'role-only'"
        )).fetchone()
    else:
        company = db.session.execute(sqltext(
            'SELECT id, name, meta FROM companies WHERE slug = :s'
        ), {'s': slug}).fetchone()
        if not company:
            return jsonify({'error': 'Unknown company. Pick one from the list.'}), 404
    cid, cname, meta = company[0], company[1], company[2] or {}

    # 1. Cache check — the free-tier sustainability key (Groq ~30 RPM).
    cached = db.session.execute(sqltext(
        'SELECT pack, salary FROM prep_packs '
        'WHERE company_id = :cid AND role = :role'
    ), {'cid': cid, 'role': role}).fetchone()
    if cached:
        return jsonify({'company': None if role_only else cname, 'role': role,
                        'mode': 'role' if role_only else 'company',
                        'pack': cached[0], 'salary': cached[1], 'cached': True})

    # 2. Hybrid retrieval: pgvector cosine (top 25) + FTS OR-query (top 15).
    #    Role-only mode searches the WHOLE corpus (role words in the query)
    #    instead of one company's slice.
    query_text = f'{role} interview questions' if role_only \
        else f'{cname} {role} interview questions'
    try:
        qvec = json.dumps(embed_query(query_text))
    except Exception:
        current_app.logger.exception('prep query embedding failed')
        return jsonify({'error': 'Search is temporarily unavailable. Please try again.'}), 502

    vec_rows = db.session.execute(sqltext(f"""
        SELECT question, COALESCE(category, ''), COALESCE(source_url, ''), source
        FROM questions
        WHERE embedding IS NOT NULL {'AND company_id = :cid' if not role_only else ''}
        ORDER BY embedding <=> CAST(:v AS vector)
        LIMIT 25
    """), ({'cid': cid} if not role_only else {}) | {'v': qvec}).fetchall()

    fts_source = role if role_only else f'{cname} {role}'
    words = [w for w in re.sub(r'[^a-z0-9 ]', '', fts_source.lower()).split() if w]
    fts_rows = []
    if words:
        or_q = ' | '.join(words)
        fts_rows = db.session.execute(sqltext(f"""
            SELECT question, COALESCE(category, ''), COALESCE(source_url, ''), source
            FROM questions
            WHERE {'1=1' if role_only else 'company_id = :cid'}
              AND to_tsvector('english', question) @@ to_tsquery('english', :q)
            ORDER BY ts_rank_cd(to_tsvector('english', question),
                                to_tsquery('english', :q)) DESC
            LIMIT 15
        """), ({'cid': cid} if not role_only else {}) | {'q': or_q}).fetchall()

    retrieved, seen = [], set()
    for r in list(vec_rows) + list(fts_rows):
        if r[0] in seen:
            continue
        seen.add(r[0])
        retrieved.append({'question': r[0], 'category': r[1],
                          'source_url': r[2], 'source': r[3]})

    # 3. Groq synthesis (rounds prose comes from companies.meta — no live scrape).
    rounds_prose = [] if role_only else (meta.get('rounds') or [])
    pack = synthesize_pack(None if role_only else cname, role, rounds_prose,
                           retrieved, role_only=role_only)
    if not pack:
        return jsonify({'error': 'Pack generation failed. You have not been charged.'}), 502

    # 4. Salary band (best effort — never blocks the pack).
    salary = fetch_salary_band(role)

    # 5. Cache for every future request of this (company, role).
    db.session.execute(sqltext("""
        INSERT INTO prep_packs (company_id, role, pack, salary)
        VALUES (:cid, :role, CAST(:pack AS jsonb), CAST(:salary AS jsonb))
        ON CONFLICT (company_id, role) DO UPDATE
            SET pack = EXCLUDED.pack, salary = EXCLUDED.salary,
                created_at = now()
    """), {'cid': cid, 'role': role, 'pack': json.dumps(pack),
           'salary': json.dumps(salary) if salary else None})
    db.session.commit()

    return jsonify({'company': None if role_only else cname, 'role': role,
                    'mode': 'role' if role_only else 'company',
                    'pack': pack, 'salary': salary, 'cached': False})
