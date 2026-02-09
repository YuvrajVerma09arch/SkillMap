from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
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
    
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'seeker')

        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('auth.login', mode='signup'))
        
        # Create new User
        new_user = User(email=email, name=name, role=role)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # --- THE FIX IS HERE ---
        # Log in the NEW user we just created
        login_user(new_user) 
        
        flash('Account created! Please complete your profile.', 'success')
        
        # Redirect Logic:
        if role == 'recruiter':
            return redirect(url_for('main.setup_profile')) # Will eventually go to Recruiter Setup
        else:
            return redirect(url_for('main.setup_profile')) # Seeker Questionnaire

    # If GET, show the login page but slide to signup
    return redirect(url_for('auth.login', mode='signup'))

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