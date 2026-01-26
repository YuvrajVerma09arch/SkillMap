import os
import uuid
from flask import Blueprint, render_template, request, current_app, flash
from werkzeug.utils import secure_filename
from app.utils.resume_parser import analyze_resume 
# from app.utils.resume_parser_ml import analyze_resume
from app.utils.roadmap_gen import generate_roadmap

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/resume-checker', methods=['GET', 'POST'])
def resume_checker():
    results = None
    # Default: Grey ring for empty state
    score_gradient = "conic-gradient(#dfe6e9 0%, #dfe6e9 0)" 
    
    if request.method == 'POST':
        # 1. Get Job Description
        job_description = request.form.get('job_description')
        
        # 2. Get File
        if 'resume' not in request.files:
            flash('No file part')
            return render_template('seeker/resume_checker.html', results=None, score_gradient=score_gradient)
            
        resume_file = request.files['resume']
        
        if resume_file.filename == '':
            flash('No selected file')
            return render_template('seeker/resume_checker.html', results=None, score_gradient=score_gradient)

        if resume_file:
            # 3. Save File Securely
            filename = secure_filename(resume_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            resume_file.save(save_path)

            try:
                # 4. Analyze
                results = analyze_resume(save_path, job_description)
                
                # 5. Calculate Gradient String (Python handles the logic now)
                score = results.get('match_score', 0)
                score_gradient = f"conic-gradient(#00cec9 {score}%, #dfe6e9 0)"
                
            except Exception as e:
                flash(f"Error analyzing resume: {str(e)}")
            finally:
                # 6. Cleanup: Remove the file after analysis to save space
                if os.path.exists(save_path):
                    os.remove(save_path)

    # Pass the pre-calculated string to the template
    return render_template('seeker/resume_checker.html', results=results, score_gradient=score_gradient)

@main.route('/roadmap', methods=['GET', 'POST'])
def roadmap():
    roadmap_data = []
    
    if request.method == 'POST':
        current_skills = request.form.get('current_skills')
        target_role = request.form.get('target_role')
        
        if current_skills and target_role:
            try:
                roadmap_data = generate_roadmap(current_skills, target_role)
            except Exception as e:
                flash(f"Error generating roadmap: {str(e)}", "danger")
    
    return render_template('seeker/roadmap.html', roadmap=roadmap_data)