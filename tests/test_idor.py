"""Regression test for the Application.seeker_id / users.id IDOR (SECURITY.md #1).

Forces the ID collision: attacker.seeker_profile.id == victim.users.id.
The buggy code compared Application.seeker_id (a seeker_profiles.id) to
seeker_user.id (a users.id), letting an unrelated recruiter unlock PII.

Run from repo root:  python3 tests/test_idor.py
Exit 0 = all assertions pass, 1 = a regression is present.
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DB = os.path.join(tempfile.gettempdir(), 'skillmap_idor_test.db')
if os.path.exists(DB):
    os.remove(DB)
os.environ['DATABASE_URL'] = f'sqlite:///{DB}'
os.environ.setdefault('SECRET_KEY', 'test-only-secret')

from app import create_app, db
from app.models import User, SeekerProfile, RecruiterProfile, JobPost, Application


def build_fixtures():
    recruiter = User(id=100, name='Recruiter', email='r@x.com', role='recruiter')
    recruiter.set_password('x')
    db.session.add(recruiter)
    db.session.commit()
    db.session.add(RecruiterProfile(id=1, user_id=100, company_name='Acme'))
    db.session.commit()
    db.session.add(JobPost(id=1, recruiter_id=1, company_name='Acme',
                           title='Dev', description='d'))
    db.session.commit()

    # victim: users.id=1, seeker_profile.id=5
    victim = User(id=1, name='Victim', email='v@x.com', role='seeker')
    victim.set_password('x')
    db.session.add(victim)
    db.session.commit()
    db.session.add(SeekerProfile(id=5, user_id=1, phone='VICTIM-PHONE',
                                 resume_file='1_deadbeef_resume.pdf'))
    db.session.commit()

    # attacker: users.id=2, seeker_profile.id=1 (== victim.users.id)
    attacker = User(id=2, name='Attacker', email='a@x.com', role='seeker')
    attacker.set_password('x')
    db.session.add(attacker)
    db.session.commit()
    db.session.add(SeekerProfile(id=1, user_id=2, phone='ATTACKER-PHONE',
                                 resume_file='2_aaaa_resume.pdf'))
    db.session.commit()
    db.session.add(Application(id=1, job_id=1, seeker_id=1))  # attacker applied
    db.session.commit()

    # legitimate applicant: users.id=3, seeker_profile.id=9
    legit = User(id=3, name='Legit', email='l@x.com', role='seeker')
    legit.set_password('x')
    db.session.add(legit)
    db.session.commit()
    db.session.add(SeekerProfile(id=9, user_id=3, phone='LEGIT-PHONE',
                                 resume_file='3_bbbb_resume.pdf'))
    db.session.add(Application(id=2, job_id=1, seeker_id=9))
    db.session.commit()

    # collider: users.id=9 (== legit's profile id) but never applied
    collider = User(id=9, name='Collider', email='c@x.com', role='seeker')
    collider.set_password('x')
    db.session.add(collider)
    db.session.commit()
    db.session.add(SeekerProfile(id=99, user_id=9, phone='COLLIDER-PHONE',
                                 resume_file='9_cccc_resume.pdf'))
    db.session.commit()


def main():
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    build_fixtures()

    from app.main.routes import (recruiter_can_view_seeker,
                                 seeker_can_view_recruiter, uploads_dir)

    r, v, a, l, c = (db.session.get(User, i) for i in (100, 1, 2, 3, 9))
    fails = []

    def check(label, got, want):
        ok = got == want
        print(f'  {"ok  " if ok else "FAIL"} {label}: {got!r} (want {want!r})')
        if not ok:
            fails.append(f'{label}: {got!r} != {want!r}')

    print('[helpers]')
    check('recruiter sees victim (collision)', recruiter_can_view_seeker(r, v), False)
    check('recruiter sees legit applicant', recruiter_can_view_seeker(r, l), True)
    check('collider seeker sees recruiter (collision)', seeker_can_view_recruiter(c, r), False)
    check('legit seeker sees recruiter', seeker_can_view_recruiter(l, r), True)
    check('applicant seeker sees recruiter', seeker_can_view_recruiter(a, r), True)

    print('[http]')
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = '100'
        sess['_fresh'] = True

    data = client.get('/api/profiles/1').get_json() or {}
    check('victim phone gated', data.get('profile', {}).get('phone'), None)
    data = client.get('/api/profiles/3').get_json() or {}
    check('legit phone visible', data.get('profile', {}).get('phone'), 'LEGIT-PHONE')

    os.makedirs(uploads_dir(), exist_ok=True)
    files = ['1_deadbeef_resume.pdf', '3_bbbb_resume.pdf']
    for f in files:
        with open(os.path.join(uploads_dir(), f), 'wb') as fh:
            fh.write(b'%PDF-1.4 dummy')

    check('victim resume blocked', client.get('/api/files/resume/' + files[0]).status_code, 403)
    check('legit resume allowed', client.get('/api/files/resume/' + files[1]).status_code, 200)
    for f in files:
        os.remove(os.path.join(uploads_dir(), f))

    ctx.pop()
    if fails:
        print('\nFAIL:')
        for f in fails:
            print('  -', f)
        return 1
    print('\nPASS: collision blocked, legitimate relationships preserved')
    return 0


if __name__ == '__main__':
    sys.exit(main())
