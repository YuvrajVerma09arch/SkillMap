from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from config import Config

# Initialize Extensions Globaly
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
oauth = OAuth()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Init Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    oauth.init_app(app)

    # 2. Register Google Client (MUST BE BEFORE BLUEPRINTS)
    # Check if keys exist to avoid silent failures
    if not app.config.get('GOOGLE_CLIENT_ID') or not app.config.get('GOOGLE_CLIENT_SECRET'):
        print("⚠️ WARNING: Google Auth Keys are missing in Config!")
    
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    # 3. Register Blueprints
    from app.main.routes import main
    from app.auth.routes import auth
    from app.jobs.routes import jobs
    from app.payments.routes import payments
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(jobs)
    app.register_blueprint(payments)

    return app