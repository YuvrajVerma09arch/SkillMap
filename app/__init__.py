import os
from urllib.parse import urlsplit

from flask import Flask, send_from_directory, abort, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from config import Config

# Initialize Extensions Globaly
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
oauth = OAuth()
limiter = Limiter(key_func=get_remote_address)


@login_manager.unauthorized_handler
def _unauthorized():
    return jsonify({'error': 'Authentication required.'}), 401


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Init Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    oauth.init_app(app)
    limiter.init_app(app)

    # CORS: only enabled for an explicitly configured frontend origin list.
    # supports_credentials=True requires an exact-origin list (never '*').
    cors_origins = app.config.get('CORS_ORIGINS') or []
    if cors_origins:
        CORS(
            app,
            resources={r'/api/*': {'origins': cors_origins, 'supports_credentials': True}},
        )

    # CSRF hardening for cookie sessions: when deployed cross-origin the
    # session cookie is SameSite=None, so browsers WILL attach it to
    # cross-site requests. CORS stops other origins from *reading* replies but
    # does not stop them from *sending* state-changing requests. Enforce that
    # any request carrying an Origin header comes from a trusted origin.
    # Requests without an Origin header (curl, server-to-server, same-origin
    # GETs) pass through — browsers always send Origin on cross-site writes.
    trusted_origins = set(cors_origins)

    @app.before_request
    def _enforce_origin():
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return None
        origin = request.headers.get('Origin')
        if origin is None:
            return None
        if origin in trusted_origins or urlsplit(origin).netloc == request.host:
            return None
        return jsonify({'error': 'Origin not allowed.'}), 403

    os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)

    # 2. Register Google Client (MUST BE BEFORE BLUEPRINTS)
    if not app.config.get('GOOGLE_CLIENT_ID') or not app.config.get('GOOGLE_CLIENT_SECRET'):
        print("WARNING: Google Auth Keys are missing in Config!")

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

    # 4. Serve the React SPA for every unmatched GET route.
    #    Concrete API/static/OAuth rules registered above always win matching.
    dist_dir = os.path.abspath(os.path.join(app.root_path, '..', 'frontend', 'dist'))

    def _serve_spa():
        index = os.path.join(dist_dir, 'index.html')
        if os.path.exists(index):
            return send_from_directory(dist_dir, 'index.html')
        return jsonify({'error': 'Frontend build not found. Run: cd frontend && npm run build'}), 404

    @app.route('/', defaults={'path': ''}, methods=['GET'])
    @app.route('/<path:path>', methods=['GET'])
    def spa_catch_all(path):
        if path.startswith(('api/', 'static/', 'google/callback', 'login/google')):
            abort(404)
        if path:
            asset_path = os.path.abspath(os.path.join(dist_dir, path))
            try:
                if os.path.commonpath([dist_dir, asset_path]) == dist_dir and os.path.isfile(asset_path):
                    return send_from_directory(dist_dir, path)
            except ValueError:
                pass
        return _serve_spa()

    return app
