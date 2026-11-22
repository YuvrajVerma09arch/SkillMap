"""Regression tests for role guards + security headers (SECURITY.md #2, #3).

Run from repo root:  python3 tests/test_hardening.py
Exit 0 = all pass.
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB = os.path.join(tempfile.gettempdir(), 'skillmap_hardening_test.db')
if os.path.exists(DB):
    os.remove(DB)
os.environ['DATABASE_URL'] = f'sqlite:///{DB}'
os.environ.setdefault('SECRET_KEY', 'test-only-secret')

from app import create_app, db
from app.models import User


def main():
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    db.create_all()

    seeker = User(id=1, name='Seeker', email='s@x.com', role='seeker')
    seeker.set_password('x')
    recruiter = User(id=2, name='Recruiter', email='r@x.com', role='recruiter')
    recruiter.set_password('x')
    db.session.add_all([seeker, recruiter])
    db.session.commit()

    from flask import g
    client = app.test_client()
    fails = []

    def login(uid):
        # Flask-Login caches current_user in `g` (app-context scoped). Clear it
        # so switching sessions mid-test actually takes effect.
        if hasattr(g, '_login_user'):
            del g._login_user
        with client.session_transaction() as sess:
            sess.clear()
            sess['_user_id'] = str(uid)
            sess['_fresh'] = True

    def check(label, got, want):
        ok = got == want
        print(f'  {"ok  " if ok else "FAIL"} {label}: {got!r} (want {want!r})')
        if not ok:
            fails.append(f'{label}: {got!r} != {want!r}')

    print('[role guards]')
    login(1)
    check('seeker -> recruiter save blocked',
          client.post('/api/profile/recruiter', json={'company_name': 'X'}).status_code, 403)
    login(2)
    check('recruiter -> seeker save blocked',
          client.post('/api/profile/seeker', json={'full_name': 'X'}).status_code, 403)
    login(1)
    check('legit seeker save works',
          client.post('/api/profile/seeker', json={'full_name': 'Real'}).status_code, 200)
    login(2)
    check('legit recruiter save works',
          client.post('/api/profile/recruiter', json={'company_name': 'Real'}).status_code, 200)

    print('[security headers]')
    r = client.get('/api/health')
    check('X-Content-Type-Options', r.headers.get('X-Content-Type-Options'), 'nosniff')
    check('X-Frame-Options', r.headers.get('X-Frame-Options'), 'SAMEORIGIN')
    check('Referrer-Policy', r.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')
    check('Permissions-Policy present', bool(r.headers.get('Permissions-Policy')), True)

    ctx.pop()
    if fails:
        print('\nFAIL:')
        for f in fails:
            print('  -', f)
        return 1
    print('\nPASS: role guards + headers correct, legit flows intact')
    return 0


if __name__ == '__main__':
    sys.exit(main())
