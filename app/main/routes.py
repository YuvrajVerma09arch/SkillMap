import os
import uuid
from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for, session
from flask_login import login_required, current_user
from flask import abort
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
        # Recruiter Logic
        profile = current_user.recruiter_profile
        return render_template('recruiter/setup.html', profile=profile)
    else:
        # SEEKER LOGIC (EDIT MODE)
        profile = current_user.seeker_profile
        
        # PARSE EDUCATION DATA (Fixing the missing College/Year bug)
        parsed_edu = {'college': '', 'year': ''}
        if profile and profile.education_level:
            # Format is: "Degree - College Name (Year)"
            # Regex to extract: Anything after " - " until " (", then the Year inside "()"
            try:
                # Split "Degree - College..."
                parts = profile.education_level.split(' - ', 1)
                if len(parts) > 1:
                    rest = parts[1] # "LJIET (2026)"
                    college_part = rest.rsplit(' (', 1) # ["LJIET", "2026)"]
                    if len(college_part) > 1:
                        parsed_edu['college'] = college_part[0]
                        parsed_edu['year'] = college_part[1].replace(')', '')
                    else:
                        parsed_edu['college'] = rest
            except:
                pass # Fallback to empty if format is weird

        return render_template('seeker/questionnaire.html', profile=profile, parsed_edu=parsed_edu)
# --- 2. SAVE SEEKER ---
@main.route('/save-seeker-profile', methods=['POST'])
@login_required
def save_seeker_profile():
    try:
        # 1. Get Basic Data
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        location = request.form.get('location')
        experience_years = request.form.get('experience_years')
        education_level = request.form.get('qualification')
        college = request.form.get('college')
        grad_year = request.form.get('grad_year')
        skills = request.form.getlist('skills')
        linkedin = request.form.get('linkedin')
        
        # 2. Get Project Data
        project_title = request.form.get('project_title')
        project_link = request.form.get('project_link')
        
        projects_data = []
        if project_title and project_link:
            projects_data = [{'title': project_title, 'link': project_link}]

        # 3. Update User Name
        current_user.name = full_name
        db.session.add(current_user)

        # 4. Get/Create Profile
        profile = SeekerProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = SeekerProfile(user_id=current_user.id)
        
        # 5. Update Profile Fields
        profile.phone = phone
        profile.location = location
        profile.experience_years = experience_years
        # Combine Education into one string for storage
        profile.education_level = f"{education_level} - {college} ({grad_year})"
        profile.skills = skills 
        profile.linkedin_url = linkedin
        
        # Only overwrite projects if user provided new ones, or if it's a new profile
        if projects_data:
            profile.projects = projects_data

        if 'profile_pic' in request.files:
            pic = request.files['profile_pic']
            if pic and pic.filename != '':
                pic_filename = secure_filename(pic.filename)
                # Unique name: pic_user_ID_hash.jpg
                pic_unique_name = f"pic_{current_user.id}_{uuid.uuid4().hex[:8]}_{pic_filename}"
                
                upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder,exist_ok=True)
                
                pic.save(os.path.join(upload_folder, pic_unique_name))
                profile.profile_pic = pic_unique_name
        
        # 6. Handle Resume
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                unique_name = f"{current_user.id}_{uuid.uuid4().hex[:8]}_{filename}"
                
                upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder, exist_ok=True)
                
                file.save(os.path.join(upload_folder, unique_name))
                profile.resume_file = unique_name

        db.session.add(profile)
        db.session.commit()
        
        flash("Profile Updated Successfully!", "success")
        # FIXED: Now redirects to the profile page we just created logic for
        return redirect(url_for('main.view_profile', user_id=current_user.id))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}") # Print to terminal for debugging
        flash(f"Error saving profile: {str(e)}", "danger")
        return redirect(url_for('main.setup_profile'))

# --- 3. SAVE RECRUITER ---
@main.route('/save-recruiter-profile', methods=['POST'])
@login_required
def save_recruiter_profile():
    try:
        # Extract Data
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        company_size = request.form.get('size')
        location = request.form.get('location')
        website = request.form.get('website')
        
        # New Fields
        recruiter_name = request.form.get('recruiter_name')
        role_title = request.form.get('role_title')
        work_email = request.form.get('work_email')
        
        profile = RecruiterProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = RecruiterProfile(user_id=current_user.id)
            
        # Update Fields
        profile.company_name = company_name
        profile.industry = industry
        profile.company_size = company_size
        profile.location = location
        profile.website = website
        
        profile.recruiter_name = recruiter_name
        profile.role_title = role_title
        profile.work_email = work_email
        
        db.session.add(profile)
        db.session.commit()
        
        flash("Company Profile Updated!", "success")
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

    # 1. Get Recruiter Profile
    profile = current_user.recruiter_profile
    if not profile:
        return redirect(url_for('main.setup_profile'))

    # 2. Get All Active Jobs
    jobs = JobPost.query.filter_by(recruiter_id=profile.id).order_by(JobPost.posted_at.desc()).all()

    # 3. Initialize Stats & Heap
    total_applicants = 0
    shortlisted_count = 0
    applicant_heap = MaxHeap() 

    # 4. Loop through jobs and applications
    for job in jobs:
        # Get applications for this job
        job_apps = Application.query.filter_by(job_id=job.id).all()
        total_applicants += len(job_apps)

        for application in job_apps:
            if application.status == 'Shortlisted':
                shortlisted_count += 1
            
            # Smart Match Logic
            seeker_profile = application.seeker
            if seeker_profile:
                seeker_user = seeker_profile.user
                
                # Calculate Score (Seeker Skills vs Job Skills)
                # Note: job.required_skills is now a clean list from our new form
                score = calculate_match_score(seeker_profile.skills, job.required_skills)
                
                # Create Candidate Object for Display
                candidate_data = {
                    "name": seeker_user.name,
                    "role": job.title, # Showing which job they applied for
                    "match_score": score
                }
                
                # Push to Heap (Score is the priority key)
                applicant_heap.push((score, candidate_data))

    # 5. Get Top 5 Matches
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

# --- 6. SEEKER PROFILE VIEWER ---
@main.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Security: Ensure profile exists
    if user.role == 'seeker' and not user.seeker_profile:
        if current_user.id == user.id:
            return redirect(url_for('main.setup_profile'))
        else:
            flash("This user has not set up their profile yet.", "warning")
            return redirect(url_for('main.home'))

    # Determine permissions
    is_own_profile = (current_user.id == user.id)
    is_recruiter = (current_user.role == 'recruiter')
    if current_user.id != user_id and current_user.role != 'recruiter':
        abort(403)

    return render_template(
        'seeker/profile.html', 
        user=user, 
        profile=user.seeker_profile,
        is_own_profile=is_own_profile,
        is_recruiter=is_recruiter
    )

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
        if not current_user.deduct_credits(1):
            flash("You need 1 Credit to analyze a resume. Please Upgrade!", "warning")
            return redirect(url_for('payments.pricing'))
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
    profile_resume = None
    
    # 1. Detect Existing Profile Resume
    if current_user.role == 'seeker' and current_user.seeker_profile:
        profile_resume = current_user.seeker_profile.resume_file

    if request.method == 'POST':
        if not current_user.deduct_credits(1):
            flash("You need 1 Credit to analyze a resume. Please Upgrade!", "warning")
            return redirect(url_for('payments.pricing'))
            
        job_description = request.form.get('job_description')
        use_existing = request.form.get('use_existing') == 'yes'
        
        save_path = None
        is_temp_file = False
        
        # --- THE FIX: ENSURE FOLDER EXISTS ---
        upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'static', 'uploads'))
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True) # Creates the folder safely

        try:
            # CASE A: Use Profile Resume
            if use_existing and profile_resume:
                save_path = os.path.join(upload_folder, profile_resume)
                if not os.path.exists(save_path):
                    # Graceful fallback if Render wiped the file
                    flash("Profile resume file was cleared from the server cache. Please upload it again below.", "warning")
                    save_path = None

            # CASE B: Upload New Resume
            elif 'resume' in request.files:
                file = request.files['resume']
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(upload_folder, f"temp_{uuid.uuid4().hex[:6]}_{filename}")
                    file.save(save_path) # Now this will work because the folder exists!
                    is_temp_file = True
            
            # 2. Run Analysis
            if save_path:
                results = analyze_resume(save_path, job_description)
                if 'match_score' not in results:
                    results['match_score'] = 0
            else:
                # If they tried to use existing but it was missing, we don't run the AI
                if not use_existing:
                    flash("Please upload a resume.", "warning")

        except Exception as e:
            print(f"Server Error during analysis: {e}")
            flash("An error occurred while processing the file. Please try again.", "danger")
        finally:
            # 3. Cleanup Temp File
            if is_temp_file and save_path and os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except Exception as cleanup_error:
                    print(f"Failed to clean up temp file: {cleanup_error}")

    return render_template('seeker/resume_checker.html', results=results, profile_resume=profile_resume)

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
        if not current_user.deduct_credits(1):
            flash("You need 1 Credit to generate a roadmap. Please Upgrade!", "warning")
            return redirect(url_for('payments.pricing'))
        if 'start_new' in request.form:
            role = request.form.get('role', role)
            question = generate_interview_question(role, "General", resume_text="")
            session['current_question'] = question
            session['current_role'] = role
        elif 'submit_answer' in request.form:
            user_answer = request.form.get('user_answer')
            feedback = evaluate_answer(question, user_answer)
            
    return render_template('seeker/interview.html', question=question, feedback=feedback, role=role)

@main.route('/trigger-email', methods=['POST'])
@login_required
def trigger_email():
    roadmap_data = session.get('latest_roadmap')
    target_role = session.get('target_role')
    
    if not roadmap_data:
        flash("No roadmap found to email. Please generate one first.", "warning")
        return redirect(url_for('main.roadmap'))
        
    # Using the same email service we set up for recruiters
    success, msg = send_roadmap_email(current_user.email, current_user.name, target_role, roadmap_data)
    
    if success:
        flash(f"Roadmap sent to {current_user.email}!", "success")
    else:
        flash(f"Failed to send email: {msg}", "danger")
        
    return redirect(url_for('main.roadmap'))