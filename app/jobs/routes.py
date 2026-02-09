import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app import db
from app.models import JobPost, Application,SeekerProfile,User

# Define the Blueprint
jobs = Blueprint('jobs', __name__)

# --- 1. JOB FEED (Seeker View) ---
@jobs.route('/jobs')
@login_required
def job_feed():
    # Logic: Recruiters shouldn't see the seeker feed
    if current_user.role == 'recruiter':
        return redirect(url_for('main.recruiter_dashboard'))
        
    # Fetch Active Jobs (Newest First)
    db_jobs = JobPost.query.filter_by(is_active=True).order_by(JobPost.posted_at.desc()).all()
    
    # Serialize for JS (The Bridge)
    jobs_data = []
    for job in db_jobs:
        # Check if applied
        has_applied = False
        if current_user.seeker_profile:
             has_applied = Application.query.filter_by(
                job_id=job.id, 
                seeker_id=current_user.seeker_profile.id
            ).first() is not None

        jobs_data.append({
            "id": job.id,
            "company": job.recruiter.company_name,
            "logo": job.recruiter.company_name[0].upper(),
            "title": job.title,
            "location": job.location,
            "locationType": "onsite" if "onsite" in job.job_type.lower() else "remote",
            "type": "fulltime", 
            "salary": job.salary_range,
            "description": job.description,
            "tags": job.required_skills if job.required_skills else [],
            "applied": has_applied
        })
    
    return render_template('seeker/job_feed.html', jobs_json=json.dumps(jobs_data))

# --- 2. POST A JOB (Recruiter View) ---
@jobs.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'recruiter':
        flash("Only recruiters can post jobs.", "danger")
        return redirect(url_for('main.home'))
    
    if not current_user.recruiter_profile:
        flash("Please complete your profile first.", "warning")
        return redirect(url_for('main.setup_profile'))

    if request.method == 'POST':
        try:
            # Basic Data
            title = request.form.get('title')
            location = request.form.get('location')
            job_type = request.form.get('job_type')
            salary = request.form.get('salary_range')
            experience = request.form.get('experience_required')
            desc = request.form.get('description')
            
            # List Processing (Split text areas into lists)
            resp_text = request.form.get('responsibilities', '')
            responsibilities = [line.strip() for line in resp_text.split('\n') if line.strip()]
            
            skills_text = request.form.get('required_skills', '')
            required_skills = [skill.strip() for skill in skills_text.split(',') if skill.strip()]
            
            nice_text = request.form.get('nice_to_have', '')
            nice_to_have = [item.strip() for item in nice_text.split(',') if item.strip()]
            
            benefits_text = request.form.get('benefits', '')
            benefits = [item.strip() for item in benefits_text.split(',') if item.strip()]

            new_job = JobPost(
                recruiter_id=current_user.recruiter_profile.id,
                title=title,
                location=location,
                job_type=job_type,
                salary_range=salary,
                experience_required=experience,
                description=desc,
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

# --- 3. ANALYZE FIT (Action) ---
@jobs.route('/analyze-fit/<int:job_id>', methods=['POST'])
@login_required
def analyze_fit(job_id):
    job = JobPost.query.get_or_404(job_id)
    session['prefill_job_description'] = job.description
    session['analyzing_job_id'] = job.id
    return redirect(url_for('main.resume_checker'))

# --- 4. APPLY (Action) ---
@jobs.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if not current_user.seeker_profile:
        flash("Complete your profile before applying!", "warning")
        return redirect(url_for('main.setup_profile'))

    existing = Application.query.filter_by(
        job_id=job_id, 
        seeker_id=current_user.seeker_profile.id
    ).first()
    
    if existing:
        flash("You have already applied to this job!", "warning")
        return redirect(url_for('jobs.job_feed'))
        
    new_app = Application(
        job_id=job_id,
        seeker_id=current_user.seeker_profile.id,
        status='Applied'
    )
    
    db.session.add(new_app)
    db.session.commit()
    
    flash("Application Sent Successfully!", "success")
    return redirect(url_for('jobs.job_feed'))

@jobs.route('/job/<int:job_id>/applicants')
@login_required
def view_applicants(job_id):
    # Security: Ensure this job belongs to the current recruiter
    job = JobPost.query.get_or_404(job_id)
    if job.recruiter_id != current_user.recruiter_profile.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.recruiter_dashboard'))

    # Fetch Applications
    # We join Application -> SeekerProfile -> User to get all details
    raw_applicants = db.session.query(Application, SeekerProfile, User)\
        .join(SeekerProfile, Application.seeker_id == SeekerProfile.id)\
        .join(User, SeekerProfile.user_id == User.id)\
        .filter(Application.job_id == job_id)\
        .all()

    # Format Data
    applicants_list = []
    for app, seeker, user in raw_applicants:
        applicants_list.append({
            "id": app.id,
            "name": user.name,
            "email": user.email,
            "experience": seeker.experience_years,
            "skills": seeker.skills if seeker.skills else [],
            "status": app.status,
            "applied_at": app.applied_at.strftime('%Y-%m-%d')
        })

    return render_template('recruiter/applicants.html', job=job, applicants=applicants_list)

# --- 6. UPDATE APPLICATION STATUS ---
@jobs.route('/application/<int:app_id>/update/<status>', methods=['POST'])
@login_required
def update_status(app_id, status):
    application = Application.query.get_or_404(app_id)
    
    # Security Check (Complex but necessary)
    # Check if the job linked to this application belongs to the current recruiter
    job = JobPost.query.get(application.job_id)
    if job.recruiter_id != current_user.recruiter_profile.id:
        flash("You cannot modify this application.", "danger")
        return redirect(url_for('main.recruiter_dashboard'))
        
    application.status = status
    db.session.commit()
    
    flash(f"Candidate marked as {status}", "success")
    return redirect(url_for('jobs.view_applicants', job_id=job.id))