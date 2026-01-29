from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # CRITICAL: This separates Recruiters from Seekers
    # Values: 'seeker' or 'recruiter'
    role = db.Column(db.String(20), nullable=False, default='seeker')
    
    # Relationships
    # If Recruiter: They can have many "Jobs"
    jobs_posted = db.relationship('Job', backref='recruiter', lazy=True)
    
    # If Seeker: They can have many "Applications"
    applications = db.relationship('Application', backref='applicant', lazy=True)

    # --- SECURITY METHODS ---
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # For our AI Matcher: "Python, SQL, AWS"
    required_skills = db.Column(db.String(200)) 
    
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Link to the Recruiter who posted it
    recruiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Link to applications received
    applications = db.relationship('Application', backref='job', lazy=True)

class Application(db.Model):
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    applied_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Applied') # Applied, Interview, Rejected
    
    # The Resume Match Score (0-100) - Saved for the recruiter to see!
    match_score = db.Column(db.Integer)
    
    # Links
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)