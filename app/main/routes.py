import os
import uuid
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from app.utils.email_service import send_roadmap_email # Real Service

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/resume-checker', methods=['GET', 'POST'])
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
                flash(f"Error generating roadmap: {str(e)}", "danger")
    
    return render_template('seeker/roadmap.html', roadmap=roadmap_data)

# --- THE REAL EMAIL ROUTE (Fixed) ---
@main.route('/trigger-email', methods=['POST'])
@login_required
def trigger_email():
    # Get data from session
    roadmap_data = session.get('latest_roadmap')
    target_role = session.get('target_role')
    
    if not roadmap_data:
        flash("No roadmap found! Generate one first.", "warning")
        return redirect(url_for('main.roadmap'))

    # CALL THE REAL PYTHON EMAIL SERVICE
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

@main.route('/interview', methods=['GET', 'POST'])
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


# Add this route to app/main/routes.py


# ... (Previous imports) ...

# 1. ADD THE SETUP ROUTE
@main.route('/setup-profile', methods=['GET'])
@login_required
def setup_profile():
    # If Recruiter, send to their setup (Placeholder for now)
    if current_user.role == 'recruiter':
        return render_template('recruiter/setup.html') 
    else:
    # If Seeker, show the new form
     return render_template('seeker/questionnaire.html')

# 2. ADD THE SAVE ROUTE (Handle Form Submission)
@main.route('/save-seeker-profile', methods=['POST'])
@login_required
def save_seeker_profile():
    # Collect data (In a real app, save this to DB)
    full_name = request.form.get('full_name')
    skills = request.form.getlist('skills') # Gets all selected skills
    
    # FOR NOW: Simulate saving by marking session
    # (Since we just nuked the DB, we will add the User Model update later)
    session['profile_completed'] = True
    
    flash(f"Profile Setup Complete! You selected {len(skills)} skills.", "success")
    return redirect(url_for('main.home'))

@main.route('/save-recruiter-profile', methods=['POST'])
@login_required
def save_recruiter_profile():
    # Collect Data
    company = request.form.get('company_name')
    industry = request.form.get('industry')
    # In real app: Save to 'Company' table
    
    session['profile_completed'] = True
    flash(f"Welcome {company}! Your dashboard is ready.", "success")
    
    # Redirect to Recruiter Dashboard (We haven't built this yet, so send to home)
    return redirect(url_for('main.recruiter_dashboard'))


# app/main/routes.py

@main.route('/recruiter/dashboard')
@login_required
def recruiter_dashboard():
    # 1. Check if user is actually a recruiter
    if current_user.role != 'recruiter':
        flash("Access Denied: Recruiters only.", "danger")
        return redirect(url_for('main.home'))

    # 2. DUMMY DATA (Simulating DB Queries)
    
    # Stats for the "Hero" Cards
    stats = {
        "total_applicants": 87,
        "active_jobs": 4,
        "interviews": 6
    }

    # Job List (Simulating your "Job" table)
    jobs = [
        {
            "title": "Senior Python Developer",
            "location": "Remote / Bengaluru",
            "posted_days": 2,
            "applicants": 42, # High traffic!
            "status": "Active"
        },
        {
            "title": "AI/ML Engineer",
            "location": "Pune",
            "posted_days": 5,
            "applicants": 18,
            "status": "Active"
        },
        {
            "title": "Frontend React Dev",
            "location": "Delhi (Hybrid)",
            "posted_days": 12,
            "applicants": 27,
            "status": "Active"
        }
    ]

    # AI Candidates (Simulating Smart Match)
    candidates = [
        {"name": "Arjun Mehta", "role": "Full Stack Dev", "match_score": 96},
        {"name": "Priya Sharma", "role": "Data Scientist", "match_score": 92},
        {"name": "Rohan Das", "role": "Python Expert", "match_score": 88},
        {"name": "Sanya V.", "role": "Backend Lead", "match_score": 85},
    ]

    return render_template('recruiter/dashboard.html', 
                           stats=stats, 
                           jobs=jobs, 
                           candidates=candidates)