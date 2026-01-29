from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# Initialize Extensions (Global Scope)
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    load_dotenv()
    
    app = Flask(__name__)
    
    # CONFIGURATION
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev_key_only'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skillmap.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # CRITICAL FIX: Upload Folder Config
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Ensure upload directory exists
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Initialize Plugins
    db.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Register Blueprints
    from app.main.routes import main
    from app.auth.routes import auth
    
    app.register_blueprint(main)
    app.register_blueprint(auth)

    # Create Database Tables
    with app.app_context():
        db.create_all()

    return app