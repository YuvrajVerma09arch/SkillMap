from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from sqlalchemy.dialects.postgresql import JSON 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 1. USERS TABLE (Modified for SaaS)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False) # 'seeker' or 'recruiter'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- NEW: SAAS FIELDS ---
    tier = db.Column(db.String(20), default='Free')  # 'Free', 'Pro', 'Enterprise'
    credits = db.Column(db.Integer, default=3)       # Starts with 3 Free Credits
    subscription_active_until = db.Column(db.DateTime, nullable=True) # For time-based access
    razorpay_customer_id = db.Column(db.String(100), nullable=True)   # Future-proofing

    # Relationships
    seeker_profile = db.relationship('SeekerProfile', backref='user', uselist=False, lazy=True)
    recruiter_profile = db.relationship('RecruiterProfile', backref='user', uselist=False, lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True) # Payment History

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Helper to check if user has enough credits
    def has_credits(self, cost=1):
        if self.tier == 'Enterprise': # Enterprise gets unlimited
            return True
        return self.credits >= cost

    # Helper to deduct credits
    def deduct_credits(self, cost=1):
        if self.tier != 'Enterprise' and self.credits >= cost:
            self.credits -= cost
            db.session.commit()
            return True
        return False

# 2. SEEKER PROFILES (Unchanged)
class SeekerProfile(db.Model):
    __tablename__ = 'seeker_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    headline = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    experience_years = db.Column(db.String(20))
    education_level = db.Column(db.String(50))
    
    skills = db.Column(JSON) 
    projects = db.Column(JSON)
    profile_pic = db.Column(db.String(255))
    resume_file = db.Column(db.String(255))
    resume_text = db.Column(db.Text) 
    linkedin_url = db.Column(db.String(255))
    portfolio_url = db.Column(db.String(255))
    
    applications = db.relationship('Application', backref='seeker', lazy=True)

# 3. RECRUITER PROFILES (Unchanged)
class RecruiterProfile(db.Model):
    __tablename__ = 'recruiter_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    recruiter_name = db.Column(db.String(100))
    role_title = db.Column(db.String(100))
    work_email = db.Column(db.String(120))
    company_name = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(50))
    company_size = db.Column(db.String(50))
    location = db.Column(db.String(100))
    website = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    
    jobs = db.relationship('JobPost', backref='recruiter', lazy=True)

# 4. JOB POSTS (Modified for Seeding Strategy)
class JobPost(db.Model):
    __tablename__ = 'job_posts'
    id = db.Column(db.Integer, primary_key=True)
    recruiter_id = db.Column(db.Integer, db.ForeignKey('recruiter_profiles.id'), nullable=True) # Nullable for Seeded Jobs
    
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100))
    salary_range = db.Column(db.String(50))
    job_type = db.Column(db.String(50))
    experience_required = db.Column(db.String(50))
    
    responsibilities = db.Column(JSON)
    required_skills = db.Column(JSON)
    nice_to_have = db.Column(JSON)
    benefits = db.Column(JSON)
    
    is_active = db.Column(db.Boolean, default=True)
    posted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # --- NEW: JOB SEEDING FIELD ---
    is_seeded = db.Column(db.Boolean, default=False) # True if scraped/seeded
    external_link = db.Column(db.String(255))        # Link to original job if seeded
    
    applications = db.relationship('Application', backref='job', lazy=True)

# 5. APPLICATIONS (Unchanged)
class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_posts.id'), nullable=False)
    seeker_id = db.Column(db.Integer, db.ForeignKey('seeker_profiles.id'), nullable=False)
    
    status = db.Column(db.String(20), default='Applied')
    match_score = db.Column(db.Float)
    cover_note = db.Column(db.Text)
    
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

# 6. NEW: TRANSACTIONS (The Ledger)
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)     # e.g., 499.00
    currency = db.Column(db.String(10), default='INR')
    status = db.Column(db.String(20), default='pending') # pending, success, failed
    
    # Razorpay Specifics
    razorpay_order_id = db.Column(db.String(100), unique=True)
    razorpay_payment_id = db.Column(db.String(100))
    
    credits_purchased = db.Column(db.Integer, default=0) # How many credits this bought
    created_at = db.Column(db.DateTime, default=datetime.utcnow)