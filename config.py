import os

class Config:
    # Security Key (Keep this secret in production!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    
    # Database Connection
    # Format: postgresql://username:password@localhost:5432/databasename
    # For now, we set a default to SQLite so you can test TODAY without installing Postgres yet if needed.
    # When ready for Postgres, you just change this one line in your .env file.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Folder to save uploaded resumes
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Max upload size: 16MB