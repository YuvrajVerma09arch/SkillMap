from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config  # <--- IMPORT YOUR CONFIG FILE
from dotenv import load_dotenv
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    # 1. Load Env Vars First
    load_dotenv()
    
    app = Flask(__name__)
    
    # 2. LOAD CONFIG FROM OBJECT (The Fix)
    app.config.from_object(Config)
    
    # 3. Verify Database URL is loaded
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise RuntimeError("❌ ERROR: DATABASE_URL is missing! Check your .env file.")

    # 4. Ensure Upload Folder Exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please log in to access this feature."
    login_manager.login_message_category = 'info'

    # Register Blueprints
    from app.main.routes import main
    from app.auth.routes import auth
    from app.jobs.routes import jobs
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(jobs)

    # Database Tables (Verify connection to Neon)
    with app.app_context():
        # Since we created tables via SQL Editor, this just verifies models match
        db.create_all()

    return app