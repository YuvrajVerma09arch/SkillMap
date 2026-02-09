import os
import uuid
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# --- DB & MODELS IMPORT ---
from app import db
from app.models import SeekerProfile, RecruiterProfile, JobPost, Application, User
from app.utils.email_service import send_roadmap_email 

# --- ALGORITHMS IMPORT ---
from app.utils.heap import MaxHeap
from app.utils.matcher import calculate_match_score

main = Blueprint('main', __name__)

# --- HOME ---
@main.route('/')
def home():
    return render_template('index.html')

# --- 1. PROFILE SETUP ROUTER ---
@main.route('/setup-profile', methods=['GET'])
@login_required
def setup_profile():
    if current_user.role == 'recruiter':
        if current_user.recruiter_profile:
            return redirect(url_for('main.recruiter_dashboard'))
        return render_template('recruiter/setup.html')
    else:
        if current_user.seeker_profile:
            return redirect(url_for('main.roadmap'))
        return render_template('seeker/questionnaire.html')

# --- 2. SAVE SEEKER ---
@main.route('/save-seeker-profile', methods=['POST'])
@login_required
def save_seeker_profile():
    try:
        phone = request.form.get('phone')
        location = request.form.get('location')
        experience_years = request.form.get('experience_years')
        education_level = request.form.get('qualification')
        college = request.form.get('college')
        grad_year = request.form.get('grad_year')
        skills = request.form.getlist('skills') 
        
        profile = SeekerProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = SeekerProfile(user_id=current_user.id)
        
        profile.phone = phone
        profile.location = location
        profile.experience_years = experience_years
        profile.education_level = f"{education_level} - {college} ({grad_year})"
        profile.skills = skills 
        
        db.session.add(profile)
        db.session.commit()
        
        flash("Profile Saved Successfully!", "success")
        return redirect(url_for('jobs.job_feed'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('main.setup_profile'))

# --- 3. SAVE RECRUITER ---
@main.route('/save-recruiter-profile', methods=['POST'])
@login_required
def save_recruiter_profile():
    try:
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        company_size = request.form.get('size')
        location = request.form.get('location')
        recruiter_name = request.form.get('recruiter_name')
        role_title = request.form.get('role_title')
        website = request.form.get('website')
        
        profile = RecruiterProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = RecruiterProfile(user_id=current_user.id)
            
        profile.company_name = company_name
        profile.industry = industry
        profile.company_size = company_size
        profile.location = location
        profile.website = website
        # Note: You might need to add recruiter_name/role_title to your RecruiterProfile model if not there
        
        db.session.add(profile)
        db.session.commit()
        
        flash("Company Setup Complete!", "success")
        return redirect(url_for('main.recruiter_dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('main.setup_profile'))

# --- 4. RECRUITER DASHBOARD (WITH HEAP LOGIC) ---
@main.route('/recruiter/dashboard')
@login_required
def recruiter_dashboard():
    if current_user.role != 'recruiter':
        return redirect(url_for('jobs.job_feed'))

    # 1. Get Profile
    profile = RecruiterProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return redirect(url_for('main.setup_profile'))

    # 2. Get Jobs
    jobs = JobPost.query.filter_by(recruiter_id=profile.id).order_by(JobPost.posted_at.desc()).all()

    # 3. Calculate Stats & Build Max Heap
    total_applicants = 0
    shortlisted_count = 0
    applicant_heap = MaxHeap() # <--- Your Custom Data Structure

    for job in jobs:
        job_apps = Application.query.filter_by(job_id=job.id).all()
        total_applicants += len(job_apps)

        for application in job_apps:
            if application.status == 'Shortlisted':
                shortlisted_count += 1
            
            # Access Relations: Application -> SeekerProfile -> User
            seeker_profile = application.seeker
            if seeker_profile:
                seeker_user = seeker_profile.user
                
                # Calculate Smart Match Score
                score = calculate_match_score(seeker_profile.skills, job.required_skills)
                
                # Prepare Data Packet
                candidate_data = {
                    "name": seeker_user.name,
                    "role": job.title,
                    "id": seeker_user.id,
                    "status": application.status
                }
                
                # Push to Heap (Sorts by score automatically)
                applicant_heap.push((score, candidate_data))

    # 4. Extract Top 5 Candidates from Heap
    top_candidates = applicant_heap.get_top_n(5)

    stats = {
        "total_applicants": total_applicants,
        "active_jobs": len(jobs),
        "interviews": shortlisted_count
    }

    return render_template('recruiter/dashboard.html', 
                           stats=stats, 
                           jobs=jobs, 
                           candidates=top_candidates)

# --- 5. JOB POSTING ---
@main.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'recruiter':
        return redirect(url_for('main.home'))
    
    if not current_user.recruiter_profile:
        return redirect(url_for('main.setup_profile'))

    if request.method == 'POST':
        try:
            # Extract basic data
            title = request.form.get('title')
            location = request.form.get('location')
            job_type = request.form.get('job_type')
            salary = request.form.get('salary_range')
            experience = request.form.get('experience_required')
            desc = request.form.get('description')
            
            # Extract smart lists
            resp = [l.strip() for l in request.form.get('responsibilities', '').split('\n') if l.strip()]
            skills = [s.strip() for s in request.form.get('required_skills', '').split(',') if s.strip()]
            nice = [n.strip() for n in request.form.get('nice_to_have', '').split(',') if n.strip()]
            benefits = [b.strip() for b in request.form.get('benefits', '').split(',') if b.strip()]

            new_job = JobPost(
                recruiter_id=current_user.recruiter_profile.id,
                title=title, location=location, job_type=job_type,
                salary_range=salary, experience_required=experience, description=desc,
                responsibilities=resp, required_skills=skills, nice_to_have=nice, benefits=benefits
            )
            
            db.session.add(new_job)
            db.session.commit()
            flash(f"Job '{title}' Posted!", "success")
            return redirect(url_for('main.recruiter_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "danger")

    return render_template('recruiter/post_job.html')

# --- 6. SEEKER PROFILE VIEWER ---
@main.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    is_own = (current_user.id == user.id)
    is_recruiter = (current_user.role == 'recruiter')
    
    if not is_own and not is_recruiter:
        flash("Access Denied", "warning")
        return redirect(url_for('jobs.job_feed'))

    profile = user.seeker_profile
    if not profile and is_own:
        return redirect(url_for('main.setup_profile'))

    return render_template('seeker/profile.html', user=user, profile=profile, is_own_profile=is_own, is_recruiter=is_recruiter)

@main.route('/my-profile')
@login_required
def my_profile():
    return redirect(url_for('main.view_profile', user_id=current_user.id))

# --- 7. RECRUITER COMPANY PROFILE VIEWER ---
@main.route('/company/<int:recruiter_id>')
@login_required
def view_company(recruiter_id):
    profile = RecruiterProfile.query.filter_by(user_id=recruiter_id).first_or_404()
    jobs = JobPost.query.filter_by(recruiter_id=profile.id, is_active=True).all()
    is_owner = (current_user.id == recruiter_id)
    
    # We pass 'profile' as the RecruiterProfile object
    # We pass 'recruiter_name' from the User table join if needed, or assume it's stored in profile
    # For now, let's assume the profile object has everything we need
    return render_template('recruiter/profile.html', profile=profile, jobs=jobs, is_owner=is_owner)

@main.route('/my-company')
@login_required
def my_company():
    if current_user.role != 'recruiter':
        return redirect(url_for('main.home'))
    return redirect(url_for('main.view_company', recruiter_id=current_user.id))

# --- 8. TALENT FEED ---
@main.route('/talent')
@login_required
def talent_feed():
    if current_user.role != 'recruiter':
        return redirect(url_for('jobs.job_feed'))
    
    seekers = db.session.query(User).join(SeekerProfile).filter(User.role == 'seeker').all()
    return render_template('recruiter/talent_feed.html', seekers=seekers)

# --- 9. OTHER TOOLS (Roadmap, Resume, Interview) ---
# ... (Keep existing code for roadmap, resume_checker, interview, trigger_email) ...
@main.route('/roadmap', methods=['GET', 'POST'])
@login_required 
def roadmap():
    from app.utils.roadmap_gen import generate_roadmap
    roadmap_data = []
    if request.method == 'POST':
        current_skills = request.form.get('current_skills')
        target_role = request.form.get('target_role')
        if current_skills and target_role:
            try:
                roadmap_data = generate_roadmap(current_skills, target_role)
                session['latest_roadmap'] = roadmap_data
                session['target_role'] = target_role
            except Exception as e:
                flash(f"Error: {str(e)}", "danger")
    return render_template('seeker/roadmap.html', roadmap=roadmap_data)

@main.route('/resume-checker', methods=['GET', 'POST'])
@login_required
def resume_checker():
    from app.utils.resume_parser import analyze_resume
    results = None
    score_gradient = "conic-gradient(#dfe6e9 0%, #dfe6e9 0)"
    if request.method == 'POST':
        job_description = request.form.get('job_description')
        if 'resume' in request.files:
            resume_file = request.files['resume']
            if resume_file.filename != '':
                filename = secure_filename(resume_file.filename)
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                resume_file.save(save_path)
                try:
                    results = analyze_resume(save_path, job_description)
                    score = results.get('match_score', 0)
                    score_gradient = f"conic-gradient(#00cec9 {score}%, #dfe6e9 0)"
                except Exception as e:
                    flash(f"Error: {str(e)}")
                finally:
                    if os.path.exists(save_path): os.remove(save_path)
    return render_template('seeker/resume_checker.html', results=results, score_gradient=score_gradient)

@main.route('/interview', methods=['GET', 'POST'])
@login_required
def interview():
    from app.utils.interview_bot import generate_interview_question, evaluate_answer
    if request.args.get('reset'):
        session.pop('current_question', None)
        return redirect(url_for('main.interview'))
    
    question = session.get('current_question')
    feedback = None
    role = session.get('current_role', 'Software Engineer')
    
    if request.method == 'POST':
        if 'start_new' in request.form:
            role = request.form.get('role', role)
            question = generate_interview_question(role, "General", resume_text="")
            session['current_question'] = question
            session['current_role'] = role
        elif 'submit_answer' in request.form:
            user_answer = request.form.get('user_answer')
            feedback = evaluate_answer(question, user_answer)
            
    return render_template('seeker/interview.html', question=question, feedback=feedback, role=role)