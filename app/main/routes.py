import os
import uuid
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

# --- DB & MODELS IMPORT ---
from app import db
from app.models import SeekerProfile, RecruiterProfile, JobPost,Application,User
from app.utils.email_service import send_roadmap_email 

main = Blueprint('main', __name__)

# --- HOME ---
@main.route('/')
def home():
    return render_template('index.html')

# --- 1. PROFILE SETUP ROUTER (Check DB) ---
@main.route('/setup-profile', methods=['GET'])
@login_required
def setup_profile():
    # 1. Recruiter Flow
    if current_user.role == 'recruiter':
        # If profile exists in DB, go to dashboard
        if current_user.recruiter_profile:
            return redirect(url_for('main.recruiter_dashboard'))
        return render_template('recruiter/setup.html')
    
    # 2. Seeker Flow
    else:
        # If profile exists in DB, go to roadmap
        if current_user.seeker_profile:
            return redirect(url_for('main.roadmap'))
        return render_template('seeker/questionnaire.html')

# --- 2. SAVE SEEKER (WRITE TO NEON DB) ---
@main.route('/save-seeker-profile', methods=['POST'])
@login_required
def save_seeker_profile():
    try:
        # Extract Form Data
        phone = request.form.get('phone')
        location = request.form.get('location')
        experience_years = request.form.get('experience_years')
        education_level = request.form.get('qualification')
        college = request.form.get('college')
        grad_year = request.form.get('grad_year')
        
        # Get List of Skills (Postgres handles this list automatically)
        skills = request.form.getlist('skills') 
        
        # Check if profile exists (Update vs Create)
        profile = SeekerProfile.query.filter_by(user_id=current_user.id).first()
        
        if not profile:
            profile = SeekerProfile(user_id=current_user.id)
        
        # Update Fields
        profile.phone = phone
        profile.location = location
        profile.experience_years = experience_years
        # Combine education info for simpler display
        profile.education_level = f"{education_level} - {college} ({grad_year})"
        profile.skills = skills # <--- Saves directly as JSON
        
        # Save to DB
        db.session.add(profile)
        db.session.commit()
        
        flash("Profile Saved Successfully!", "success")
        return redirect(url_for('jobs.job_feed'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving profile: {str(e)}", "danger")
        return redirect(url_for('main.setup_profile'))

# --- 3. SAVE RECRUITER (WRITE TO NEON DB) ---
@main.route('/save-recruiter-profile', methods=['POST'])
@login_required
def save_recruiter_profile():
    try:
        # Extract Data
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        company_size = request.form.get('size')
        location = request.form.get('location')
        
        # Check/Create
        profile = RecruiterProfile.query.filter_by(user_id=current_user.id).first()
        
        if not profile:
            profile = RecruiterProfile(user_id=current_user.id)
            
        profile.company_name = company_name
        profile.industry = industry
        profile.company_size = company_size
        profile.location = location
        
        # Save
        db.session.add(profile)
        db.session.commit()
        
        flash("Company Profile Setup Complete!", "success")
        return redirect(url_for('main.recruiter_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error saving profile: {str(e)}", "danger")
        return redirect(url_for('main.setup_profile'))

# --- 4. RECRUITER DASHBOARD (REAL DATA) ---
@main.route('/recruiter/dashboard')
@login_required
def recruiter_dashboard():
    if current_user.role != 'recruiter':
        flash("Access Denied.", "danger")
        return redirect(url_for('main.home'))

    # 1. Get the Profile
    profile = current_user.recruiter_profile
    if not profile:
        return redirect(url_for('main.setup_profile'))

    # 2. Query Real Jobs from DB
    jobs = JobPost.query.filter_by(recruiter_id=profile.id).order_by(JobPost.posted_at.desc()).all()
    
    # 3. Calculate Real Stats 
    job_ids = [job.id for job in jobs]
    
    # Count all applications that belong to this recruiter's jobs
    total_applicants = 0
    if job_ids:
        total_applicants = Application.query.filter(Application.job_id.in_(job_ids)).count()
    
    stats = {
        "total_applicants": total_applicants,
        "active_jobs": len(jobs),
        "interviews": 0 # Placeholder for now (we haven't built interview scheduling yet)
    }

    # 4. Find "Recent Candidates" for the bottom list
    # Join Application + SeekerProfile + User to get names
    recent_applications = []
    if job_ids:
        recent_applications = db.session.query(Application, SeekerProfile, User)\
            .join(SeekerProfile, Application.seeker_id == SeekerProfile.id)\
            .join(User, SeekerProfile.user_id == User.id)\
            .filter(Application.job_id.in_(job_ids))\
            .order_by(Application.applied_at.desc())\
            .limit(5)\
            .all()
            
    # Format for template
    candidates_data = []
    for app, seeker, user in recent_applications:
        # Find which job they applied for
        applied_job = next((j for j in jobs if j.id == app.job_id), None)
        candidates_data.append({
            "name": user.name,
            "role": applied_job.title if applied_job else "Unknown Job",
            "match_score": app.match_score if app.match_score else 0,
            "status": app.status,
            "date": app.applied_at.strftime('%d %b')
        })

    return render_template('recruiter/dashboard.html', 
                           stats=stats, 
                           jobs=jobs, 
                           candidates=candidates_data)

    # 2. Query Real Jobs from DB
    jobs = JobPost.query.filter_by(recruiter_id=profile.id).all()
    
    # 3. Calculate Stats
    stats = {
        "total_applicants": 0, # Placeholder until 'Application' logic is built
        "active_jobs": len(jobs),
        "interviews": 0
    }

    return render_template('recruiter/dashboard.html', 
                           stats=stats, 
                           jobs=jobs, 
                           candidates=[]) # Empty list until Matching Engine is built

# --- 5. SEEKER ROADMAP (EXISTING) ---
@main.route('/roadmap', methods=['GET', 'POST'])
@login_required 
def roadmap():
    from app.utils.roadmap_gen import generate_roadmap
    
    roadmap_data = []
    
    # Optional: If user has skills in DB, pre-fill them?
    # For now, we keep the manual generation flow as requested.
    
    if request.method == 'POST':
        current_skills = request.form.get('current_skills')
        target_role = request.form.get('target_role')
        
        if current_skills and target_role:
            try:
                roadmap_data = generate_roadmap(current_skills, target_role)
                session['latest_roadmap'] = roadmap_data
                session['target_role'] = target_role
            except Exception as e:
                flash(f"Error generating roadmap: {str(e)}", "danger")
    
    return render_template('seeker/roadmap.html', roadmap=roadmap_data)

# --- 6. RESUME CHECKER (EXISTING) ---
@main.route('/resume-checker', methods=['GET', 'POST'])
@login_required
def resume_checker():
    from app.utils.resume_parser import analyze_resume
    
    results = None
    score_gradient = "conic-gradient(#dfe6e9 0%, #dfe6e9 0)" 
    
    if request.method == 'POST':
        job_description = request.form.get('job_description')
        if 'resume' not in request.files:
            flash('No file part')
            return render_template('seeker/resume_checker.html', results=None, score_gradient=score_gradient)
            
        resume_file = request.files['resume']
        if resume_file.filename == '':
            flash('No selected file')
            return render_template('seeker/resume_checker.html', results=None, score_gradient=score_gradient)

        if resume_file:
            filename = secure_filename(resume_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            resume_file.save(save_path)

            try:
                results = analyze_resume(save_path, job_description)
                score = results.get('match_score', 0)
                score_gradient = f"conic-gradient(#00cec9 {score}%, #dfe6e9 0)"
            except Exception as e:
                flash(f"Error analyzing resume: {str(e)}")
            finally:
                if os.path.exists(save_path):
                    os.remove(save_path)

    return render_template('seeker/resume_checker.html', results=results, score_gradient=score_gradient)

# --- 7. EMAIL TRIGGER (EXISTING) ---
@main.route('/trigger-email', methods=['POST'])
@login_required
def trigger_email():
    roadmap_data = session.get('latest_roadmap')
    target_role = session.get('target_role')
    
    if not roadmap_data:
        flash("No roadmap found! Generate one first.", "warning")
        return redirect(url_for('main.roadmap'))

    success, message = send_roadmap_email(
        user_email=current_user.email,
        user_name=current_user.name,
        target_role=target_role,
        roadmap_data=roadmap_data
    )

    if success:
        flash(f"Roadmap sent to {current_user.email}!", "success")
    else:
        flash(f"Email Failed: {message}", "danger")

    return redirect(url_for('main.roadmap'))

# --- 8. INTERVIEW BOT (EXISTING) ---
@main.route('/interview', methods=['GET', 'POST'])
@login_required
def interview():
    from app.utils.interview_bot import generate_interview_question, evaluate_answer

    if request.args.get('reset'):
        session.pop('current_question', None)
        session.pop('current_role', None)
        session.pop('resume_context', None)
        return redirect(url_for('main.interview'))

    question = session.get('current_question')
    feedback = None
    role = session.get('current_role', 'Software Engineer')
    
    if request.method == 'POST':
        if 'start_new' in request.form:
            role = request.form.get('role', role)
            form_context = request.form.get('resume_context')
            if form_context:
                resume_context = form_context
            else:
                resume_context = session.get('resume_context', '')
            topic = request.form.get('topic', 'Core Skills')
            question = generate_interview_question(role, topic, resume_text=resume_context)
            session['current_question'] = question
            session['current_role'] = role
            session['resume_context'] = resume_context
        
        elif 'submit_answer' in request.form:
            user_answer = request.form.get('user_answer')
            question = session.get('current_question')
            feedback = evaluate_answer(question, user_answer)
    
    return render_template('seeker/interview.html', question=question, feedback=feedback, role=role)

# --- ADD THIS TO app/main/routes.py ---

@main.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    # Security: Only Recruiters
    if current_user.role != 'recruiter':
        flash("Only recruiters can post jobs.", "danger")
        return redirect(url_for('main.home'))
    
    # Check if they have a profile first
    if not current_user.recruiter_profile:
        flash("Please complete your company profile first.", "warning")
        return redirect(url_for('main.setup_profile'))

    if request.method == 'POST':
        try:
            # 1. Get Basic Data
            title = request.form.get('title')
            location = request.form.get('location')
            job_type = request.form.get('job_type')
            salary = request.form.get('salary_range')
            experience = request.form.get('experience_required')
            desc = request.form.get('description')
            
            # 2. Process Smart Data (Text -> List for JSON)
            # Responsibilities (Split by new line)
            resp_text = request.form.get('responsibilities', '')
            responsibilities = [line.strip() for line in resp_text.split('\n') if line.strip()]
            
            # Skills (Split by comma)
            skills_text = request.form.get('required_skills', '')
            required_skills = [skill.strip() for skill in skills_text.split(',') if skill.strip()]
            
            # Optional Fields
            nice_text = request.form.get('nice_to_have', '')
            nice_to_have = [item.strip() for item in nice_text.split(',') if item.strip()]
            
            benefits_text = request.form.get('benefits', '')
            benefits = [item.strip() for item in benefits_text.split(',') if item.strip()]

            # 3. Create Job Object
            new_job = JobPost(
                recruiter_id=current_user.recruiter_profile.id,
                title=title,
                location=location,
                job_type=job_type,
                salary_range=salary,
                experience_required=experience,
                description=desc,
                
                # JSON Magic 🪄
                responsibilities=responsibilities,
                required_skills=required_skills,
                nice_to_have=nice_to_have,
                benefits=benefits
            )
            
            db.session.add(new_job)
            db.session.commit()
            
            flash(f"Job '{title}' Posted Successfully!", "success")
            return redirect(url_for('main.recruiter_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error posting job: {str(e)}", "danger")

    return render_template('recruiter/post_job.html')

@main.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    # 1. Fetch the User
    user = User.query.get_or_404(user_id)
    
    # 2. Determine Permissions
    is_own_profile = (current_user.id == user.id)
    is_recruiter = (current_user.role == 'recruiter')
    
    # Security: Seekers generally shouldn't see other Seekers (yet), 
    # but Recruiters MUST see Seekers.
    if not is_own_profile and not is_recruiter:
        flash("You cannot view other profiles yet.", "warning")
        return redirect(url_for('jobs.job_feed'))

    # 3. Get the Profile Data
    profile = user.seeker_profile
    
    # If no profile exists yet, handle gracefully
    if not profile and is_own_profile:
        return redirect(url_for('main.setup_profile'))
    elif not profile:
        flash("This user has not set up their profile.", "warning")
        return redirect(url_for('main.recruiter_dashboard'))

    return render_template('seeker/profile.html', 
                           user=user, 
                           profile=profile, 
                           is_own_profile=is_own_profile,
                           is_recruiter=is_recruiter)

@main.route('/my-profile')
@login_required
def my_profile():
    return redirect(url_for('main.view_profile', user_id=current_user.id))

@main.route('/talent')
@login_required
def talent_feed():
    # Security: Only Recruiters can see this
    if current_user.role != 'recruiter':
        flash("Access Denied. Recruiters only.", "danger")
        return redirect(url_for('jobs.job_feed'))

    # Fetch all Seekers who have a profile
    # We join User and SeekerProfile to ensure we only get people with setup profiles
    seekers = db.session.query(User).join(SeekerProfile).filter(User.role == 'seeker').all()
    
    return render_template('recruiter/talent_feed.html', seekers=seekers)