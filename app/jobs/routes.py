# app/jobs/routes.py
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app import db
from app.models import JobPost, Application, User, SeekerProfile
from datetime import datetime
from bs4 import BeautifulSoup
import requests
# --- CRITICAL IMPORT ---
from app.utils.matcher import calculate_match_score 
from app.utils.email_service import send_interview_invite, send_job_offer, send_rejection

jobs = Blueprint('jobs', __name__)

# --- 1. JOB FEED (Seeker) ---
@jobs.route('/jobs')
@login_required
def job_feed():
    if current_user.role != 'seeker':
        return redirect(url_for('main.recruiter_dashboard'))
    
    # Get Query Parameters
    filter_role = request.args.get('role', '').strip()
    filter_location = request.args.get('location', '').strip()
    filter_type = request.args.get('type', '').strip()

    # Start with Base Query (Active Jobs Only)
    query = JobPost.query.filter_by(is_active=True)

    # Apply Filters
    if filter_role:
        query = query.filter(JobPost.title.ilike(f"%{filter_role}%"))
    if filter_location:
        query = query.filter(JobPost.location.ilike(f"%{filter_location}%"))
    if filter_type:
        query = query.filter(JobPost.job_type == filter_type)

    # Sort by Newest First
    all_jobs = query.order_by(JobPost.posted_at.desc()).all()
    
    # Get IDs of jobs user has already applied to
    applied_job_ids = []
    if current_user.seeker_profile:
        my_apps = Application.query.filter_by(seeker_id=current_user.seeker_profile.id).with_entities(Application.job_id).all()
        applied_job_ids = [app.job_id for app in my_apps]

    return render_template('seeker/job_feed.html', jobs=all_jobs, applied_ids=applied_job_ids)

# --- 2. APPLY TO JOB (With Smart Score) ---
@jobs.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_to_job(job_id):
    if current_user.role != 'seeker':
        flash("Recruiters cannot apply to jobs.", "warning")
        return redirect(url_for('jobs.job_feed'))

    seeker_profile = current_user.seeker_profile
    if not seeker_profile:
        flash("Please complete your profile before applying.", "warning")
        return redirect(url_for('main.setup_profile'))

    # Check for duplicate
    existing_app = Application.query.filter_by(job_id=job_id, seeker_id=seeker_profile.id).first()
    if existing_app:
        flash("You have already applied to this job.", "info")
        return redirect(url_for('jobs.job_feed'))

    # --- SMART MATCH CALCULATION ---
    job = JobPost.query.get(job_id)
    # This line triggered the error before. Now it will work because of the import.
    score = calculate_match_score(seeker_profile.skills, job.required_skills)
    
    # Create Application with Score
    new_app = Application(
        job_id=job_id, 
        seeker_id=seeker_profile.id,
        status='Applied',
        match_score=score 
    )
    
    db.session.add(new_app)
    db.session.commit()
    
    flash("Application submitted successfully!", "success")
    return redirect(url_for('jobs.job_feed'))

# --- 3. ANALYZE FIT ---
@jobs.route('/analyze-fit/<int:job_id>', methods=['POST'])
@login_required
def analyze_fit(job_id):
    job = JobPost.query.get_or_404(job_id)
    
    # Combine description and skills for the AI
    full_context = job.description
    if job.required_skills:
        skills_text = ", ".join(job.required_skills)
        full_context += f"\n\n### Required Skills:\n{skills_text}"
        
    session['prefill_job_description'] = full_context
    session['analyzing_job_id'] = job.id
    
    return redirect(url_for('main.resume_checker'))

# --- 4. MY APPLICATIONS ---
@jobs.route('/my-applications')
@login_required
def my_applications():
    if current_user.role != 'seeker':
        return redirect(url_for('main.recruiter_dashboard'))
    
    if not current_user.seeker_profile:
        return redirect(url_for('main.setup_profile'))
        
    my_apps = Application.query.filter_by(seeker_id=current_user.seeker_profile.id)\
                               .order_by(Application.applied_at.desc()).all()
                               
    return render_template('seeker/my_applications.html', applications=my_apps)

# --- 5. RECRUITER: POST JOB ---
@jobs.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'recruiter':
        return redirect(url_for('main.home'))
    
    if not current_user.recruiter_profile:
        return redirect(url_for('main.setup_profile'))

    if request.method == 'POST':
        try:
            title = request.form.get('title')
            location = request.form.get('location')
            job_type = request.form.get('job_type')
            salary = request.form.get('salary_range')
            experience = request.form.get('experience_required')
            desc = request.form.get('description')
            
            def parse_list(data, separator=','):
                return [x.strip() for x in data.split(separator) if x.strip()]

            resp = parse_list(request.form.get('responsibilities', ''), '\n')
            
            # Use getlist for Checkboxes
            skills = request.form.getlist('required_skills') 
            
            nice = parse_list(request.form.get('nice_to_have', ''), ',')
            benefits = parse_list(request.form.get('benefits', ''), ',')

            new_job = JobPost(
                recruiter_id=current_user.recruiter_profile.id,
                title=title, location=location, job_type=job_type,
                salary_range=salary, experience_required=experience, description=desc,
                responsibilities=resp, required_skills=skills, nice_to_have=nice, benefits=benefits
            )
            
            db.session.add(new_job)
            db.session.commit()
            flash(f"Job '{title}' Posted Successfully!", "success")
            return redirect(url_for('main.recruiter_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error posting job: {str(e)}", "danger")

    return render_template('recruiter/post_job.html')

# --- 6. RECRUITER: VIEW APPLICANTS ---
@jobs.route('/job/<int:job_id>/applicants')
@login_required
def view_applicants(job_id):
    job = JobPost.query.get_or_404(job_id)
    if not current_user.recruiter_profile or job.recruiter_id != current_user.recruiter_profile.id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main.recruiter_dashboard'))

    # --- CHANGED: Fetch ALL candidates so we see history ---
    applications = Application.query.filter_by(job_id=job_id).all()
    
    applicants_data = []
    for app in applications:
        seeker = app.seeker 
        user = seeker.user
        applicants_data.append({
            'id': app.id,
            'name': user.name,
            'email': user.email,
            'phone': seeker.phone,
            'experience': seeker.experience_years,
            'user_id': user.id,
            'skills': seeker.skills,
            'status': app.status,
            'match_score': app.match_score,
            'applied_at': app.applied_at.strftime('%Y-%m-%d'),
            'resume': seeker.resume_file
        })

    # Sort: Pending first, then Closed (so active ones are at the top)
    # We use a simple lambda: 0 if active, 1 if closed
    applicants_data.sort(key=lambda x: 1 if x['status'] in ['Accepted', 'Rejected'] else 0)

    return render_template('recruiter/applicants.html', job=job, applicants=applicants_data)


# --- 7. RECRUITER: UPDATE STATUS ---
@jobs.route('/application/<int:app_id>/update/<string:status>', methods=['POST'])
@login_required
def update_status(app_id, status):
    app_record = Application.query.get_or_404(app_id)
    job = app_record.job
    
    # Security Check
    if not current_user.recruiter_profile or job.recruiter_id != current_user.recruiter_profile.id:
        flash("Unauthorized.", "danger")
        return redirect(url_for('main.recruiter_dashboard'))
    
    # 1. Update Status
    app_record.status = status
    db.session.commit()
    
    # 2. Trigger Email Logic
    candidate = app_record.seeker.user
    job_title = job.title
    recruiter_email = current_user.email
    
    success = True
    msg = ""

    if status == 'Shortlisted':
        # Send Interview Invite
        success, msg = send_interview_invite(candidate.email, candidate.name, job_title, recruiter_email)
        if success:
            flash(f"Candidate shortlisted! Invite sent to {candidate.email}", "success")
        else:
            flash(f"Candidate shortlisted, but email failed: {msg}", "warning")
        
    elif status == 'Accepted':
        # Send Offer
        success, msg = send_job_offer(candidate.email, candidate.name, job_title)
        if success:
            flash(f"Candidate Hired! Offer sent to {candidate.email}.", "success")
        else:
            flash(f"Candidate Hired, but email failed: {msg}", "warning")
        
    elif status == 'Rejected':
        # Send Rejection
        success, msg = send_rejection(candidate.email, candidate.name, job_title)
        if success:
            flash(f"Candidate rejected. Notification sent.", "info")
        else:
            flash(f"Candidate rejected, but email failed: {msg}", "warning")
    
    return redirect(url_for('jobs.view_applicants', job_id=job.id))

@jobs.route('/live-jobs')
@login_required
def live_jobs():
    if current_user.role != 'seeker':
        return redirect(url_for('main.recruiter_dashboard'))
    
    # Get the requested feed source (default to 'remote')
    source = request.args.get('feed', 'india')
    
    # Fetch based on selection
    if source == 'remote':
        raw_jobs = fetch_remotive()
    else: 
        raw_jobs = fetch_indian_jobs()
        source = 'india'
    
    # Clean HTML Descriptions into pure text for the Groq AI
    for job in raw_jobs:
        if job.get('description'):
            soup = BeautifulSoup(job['description'], "html.parser")
            job['clean_description'] = soup.get_text(separator=' ')
        else:
            job['clean_description'] = "No description available."
            
    return render_template('seeker/live_jobs.html', jobs=raw_jobs, current_feed=source)
    
    
@jobs.route('/analyze-external-fit', methods=['POST'])
@login_required
def analyze_external_fit():
    # External jobs don't have an ID in our DB, so we get the text directly from the form
    job_desc = request.form.get('job_description')
    
    if job_desc:
        session['prefill_job_description'] = job_desc
        session['analyzing_job_id'] = 'external'
    
    return redirect(url_for('main.resume_checker'))


def fetch_remotive():
    try:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=20"
        resp = requests.get(url, timeout=5).json()
        jobs = []
        for j in resp.get('jobs', []):
            jobs.append({
                'title': j.get('title'),
                'company': j.get('company_name'),
                'location': j.get('candidate_required_location'),
                'url': j.get('url'),
                'description': j.get('description'), # Raw HTML for Analyze Fit
                'logo': j.get('company_logo'),
                'source': 'Remotive'
            })
        return jobs
    except Exception as e: 
        print(f"Remotive Error: {e}")
        return []


    
def fetch_indian_jobs():
    try:
        # Put your real Adzuna keys here!
        APP_ID = os.environ.get("APP_ID")
        APP_KEY = os.environ.get("APP_KEY")
        
        # We target 'in' (India), category 'it-jobs', keyword 'software'
        url = f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={APP_ID}&app_key={APP_KEY}&results_per_page=15&what=software&category=it-jobs&content-type=application/json"
        
        resp = requests.get(url, timeout=5).json()
        jobs = []
        for j in resp.get('results', []):
            jobs.append({
                'title': j.get('title'),
                'company': j.get('company', {}).get('display_name'),
                'location': j.get('location', {}).get('display_name'), # E.g., Bangalore, Pune, Ahmedabad!
                'url': j.get('redirect_url'),
                'description': j.get('description'),
                'logo': None, 
                'source': 'Adzuna (India)'
            })
        return jobs
    except Exception as e:
        print(f"Adzuna Error: {e}")
        return []