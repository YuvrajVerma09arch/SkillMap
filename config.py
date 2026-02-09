import os

class Config:
    # Security Key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    
    # Database Connection
    uri = os.environ.get('DATABASE_URL')
    
    # --- DEBUGGING BLOCK ---
    if uri:
        # Hide password for security log
        clean_uri = uri.split('@')[1] if '@' in uri else 'UNKNOWN'
    else:
        print("\n FLASK CONFIG: No DATABASE_URL found!\n")
    # -----------------------
    
    # FIX: Render/Neon provides 'postgres://', but SQLAlchemy needs 'postgresql://'
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True, 
        "pool_recycle": 300,   # Refresh connections every 5 minutes
    }
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024