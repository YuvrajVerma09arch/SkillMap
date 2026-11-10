import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


class Config:
    # Security Key — random per-process fallback so a forgotten env var can
    # never fall back to a publicly known constant (session forgery risk).
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # Database Connection
    uri = os.environ.get('DATABASE_URL')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')

    # Split-host deploys: where the SPA is served (e.g. Vercel). Post-OAuth
    # redirects must land there — the API origin serves no frontend at all.
    FRONTEND_URL = (os.environ.get('FRONTEND_URL') or '').rstrip('/')

    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = uri

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Uploads — anchored to the project dir, NOT the process cwd, so files
    # always land inside the served app/static/uploads folder (gunicorn-safe).
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Cross-origin deploy: comma-separated frontend origins, e.g.
    # CORS_ORIGINS=https://skillmap.vercel.app,http://localhost:5173
    # Empty = same-origin only (Flask serves the built SPA).
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get('CORS_ORIGINS', '').split(',')
        if origin.strip()
    ]
    CROSS_ORIGIN = bool(CORS_ORIGINS)

    # Cookies: cross-origin XHR with credentials requires SameSite=None +
    # Secure; same-origin keeps the safer Lax default. COOKIE_SECURE overrides.
    SESSION_COOKIE_HTTPONLY = True
    # 'None' (string) is required for cross-site credentialed fetches; Python None
    # would omit the attribute and browsers default to Lax, breaking Vercel→Render.
    SESSION_COOKIE_SAMESITE = 'None' if CROSS_ORIGIN else 'Lax'
    SESSION_COOKIE_SECURE = _flag('COOKIE_SECURE', default=CROSS_ORIGIN)
    REMEMBER_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
