from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from sqlalchemy.dialects.postgresql import JSON  # <--- Crucial for Neon DB

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 1. USERS TABLE
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False) # 'seeker' or 'recruiter'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    seeker_profile = db.relationship('SeekerProfile', backref='user', uselist=False, lazy=True)
    recruiter_profile = db.relationship('RecruiterProfile', backref='user', uselist=False, lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 2. SEEKER PROFILES
class SeekerProfile(db.Model):
    __tablename__ = 'seeker_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    headline = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    experience_years = db.Column(db.String(20))
    education_level = db.Column(db.String(50))
    
    # Postgres JSON Columns (Stores lists like ["Python", "Java"])
    skills = db.Column(JSON) 
    
    resume_file = db.Column(db.String(255))
    resume_text = db.Column(db.Text) # For AI Analysis
    linkedin_url = db.Column(db.String(255))
    portfolio_url = db.Column(db.String(255))
    
    applications = db.relationship('Application', backref='seeker', lazy=True)

# 3. RECRUITER PROFILES
class RecruiterProfile(db.Model):
    __tablename__ = 'recruiter_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    company_name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(50))
    company_size = db.Column(db.String(50))
    location = db.Column(db.String(100))
    website = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    
    jobs = db.relationship('JobPost', backref='recruiter', lazy=True)

# 4. JOB POSTS
class JobPost(db.Model):
    __tablename__ = 'job_posts'
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiter_profiles.id'), nullable=False)
    
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100))
    salary_range = db.Column(db.String(50))
    job_type = db.Column(db.String(50))
    experience_required = db.Column(db.String(50))
    
    # Rich Data for Smart Matching (Stored as JSON)
    responsibilities = db.Column(JSON)
    required_skills = db.Column(JSON)
    nice_to_have = db.Column(JSON)
    benefits = db.Column(JSON)
    
    is_active = db.Column(db.Boolean, default=True)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    applications = db.relationship('Application', backref='job', lazy=True)

# 5. APPLICATIONS
class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posts.id'), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey('seeker_profiles.id'), nullable=False)
    
    status = db.Column(db.String(20), default='Applied')
    match_score = db.Column(db.Float)
    cover_note = db.Column(db.Text)
    
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)