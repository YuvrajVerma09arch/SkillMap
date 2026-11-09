# app/jobs/routes.py
import os
import re
import time
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from app import db
from app.models import JobPost, Application, User, SeekerProfile
from app.utils.matcher import calculate_match_score
from app.utils.email_service import send_interview_invite, send_job_offer, send_rejection

jobs = Blueprint('jobs', __name__)

# Bug fix: arbitrary URL strings used to be written into the status column.
VALID_STATUSES = {'Applied', 'Shortlisted', 'Accepted', 'Rejected'}


def job_payload(job, include_description=True):
    payload = {
        'id': job.id,
        'title': job.title,
        'location': job.location,
        'job_type': job.job_type,
        'salary_range': job.salary_range,
        'experience_required': job.experience_required,
        'required_skills': job.required_skills or [],
        'nice_to_have': job.nice_to_have or [],
        'benefits': job.benefits or [],
        'responsibilities': job.responsibilities or [],
        'is_active': job.is_active,
        'is_seeded': job.is_seeded,
        'external_link': job.external_link,
        'posted_at': job.posted_at.isoformat() if job.posted_at else None,
    }
    if include_description:
        payload['description'] = job.description
    if job.company_name:
        payload['company_name'] = job.company_name
    elif job.recruiter and job.recruiter.company_name:
        payload['company_name'] = job.recruiter.company_name
    else:
        payload['company_name'] = 'Company'
    return payload


# ─── 1. JOB FEED (Seeker) ───────────────────────────────────────────────────
@jobs.route('/api/jobs', methods=['GET'])
@login_required
def job_feed():
    if current_user.role != 'seeker':
        return jsonify({'error': 'Seekers only.'}), 403

    filter_role = request.args.get('role', '').strip()
    filter_location = request.args.get('location', '').strip()
    filter_type = request.args.get('type', '').strip()

    query = JobPost.query.filter_by(is_active=True)

    if filter_role:
        query = query.filter(JobPost.title.ilike(f"%{filter_role}%"))
    if filter_location:
        query = query.filter(JobPost.location.ilike(f"%{filter_location}%"))
    if filter_type:
        query = query.filter(JobPost.job_type == filter_type)

    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(50, max(1, request.args.get('per_page', 10, type=int) or 10))
    total = query.count()
    pages = max(1, -(-total // per_page))
    page = min(page, pages)
    all_jobs = (
        query.order_by(JobPost.posted_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    applied_job_ids = []
    if current_user.seeker_profile:
        my_apps = Application.query.filter_by(
            seeker_id=current_user.seeker_profile.id
        ).with_entities(Application.job_id).all()
        applied_job_ids = [app.job_id for app in my_apps]

    return jsonify({
        'jobs': [job_payload(j) for j in all_jobs],
        'applied_ids': applied_job_ids,
        'total': total,
        'page': page,
        'pages': pages,
        'per_page': per_page,
    })


# ─── 2. APPLY TO JOB (with smart score) ─────────────────────────────────────
@jobs.route('/api/jobs/<int:job_id>/apply', methods=['POST'])
@login_required
def apply_to_job(job_id):
    if current_user.role != 'seeker':
        return jsonify({'error': 'Recruiters cannot apply to jobs.'}), 403

    seeker_profile = current_user.seeker_profile
    if not seeker_profile:
        return jsonify({'error': 'Please complete your profile before applying.', 'redirect': '/setup-profile'}), 403

    # Bug fix: get_or_404 instead of .get() -> AttributeError on bad ids.
    job = JobPost.query.get_or_404(job_id)
    # Bug fix: closed/inactive jobs could still accept applications.
    if not job.is_active:
        return jsonify({'error': 'This job is no longer accepting applications.'}), 400
    if job.external_link:
        return jsonify({'error': 'This job is hosted externally.', 'external_link': job.external_link}), 400

    existing_app = Application.query.filter_by(job_id=job_id, seeker_id=seeker_profile.id).first()
    if existing_app:
        return jsonify({'error': 'You have already applied to this job.', 'application_id': existing_app.id}), 409

    score = calculate_match_score(seeker_profile.skills, job.required_skills)

    new_app = Application(
        job_id=job_id,
        seeker_id=seeker_profile.id,
        status='Applied',
        match_score=score,
    )
    db.session.add(new_app)
    db.session.commit()

    return jsonify({
        'application': {
            'id': new_app.id,
            'job_id': job_id,
            'status': new_app.status,
            'match_score': new_app.match_score,
        }
    }), 201


# ─── 3. MY APPLICATIONS ─────────────────────────────────────────────────────
@jobs.route('/api/applications/me', methods=['GET'])
@login_required
def my_applications():
    if current_user.role != 'seeker':
        return jsonify({'error': 'Seekers only.'}), 403
    if not current_user.seeker_profile:
        return jsonify({'needs_setup': True, 'applications': []}), 200

    my_apps = Application.query.filter_by(
        seeker_id=current_user.seeker_profile.id
    ).order_by(Application.applied_at.desc()).all()

    return jsonify({
        'applications': [
            {
                'id': app.id,
                'status': app.status,
                'match_score': app.match_score,
                'applied_at': app.applied_at.isoformat() if app.applied_at else None,
                'job': job_payload(app.job, include_description=False) if app.job else None,
            }
            for app in my_apps
        ]
    })


# ─── 4. RECRUITER: POST JOB ─────────────────────────────────────────────────
@jobs.route('/api/recruiter/jobs', methods=['POST'])
@login_required
def post_job():
    if current_user.role != 'recruiter':
        return jsonify({'error': 'Recruiters only.'}), 403
    if not current_user.recruiter_profile:
        return jsonify({'error': 'Complete your company profile first.', 'redirect': '/setup-profile'}), 403

    try:
        data = request.get_json(silent=True) or {}

        title = (data.get('title') or '').strip()
        description = (data.get('description') or '').strip()
        if not title or not description:
            return jsonify({'error': 'Title and description are required.'}), 400

        def as_list(value, separator='\n'):
            if isinstance(value, list):
                return [str(v).strip() for v in value if str(v).strip()]
            if not value:
                return []
            return [x.strip() for x in str(value).split(separator) if x.strip()]

        new_job = JobPost(
            recruiter_id=current_user.recruiter_profile.id,
            title=title,
            location=data.get('location'),
            job_type=data.get('job_type'),
            salary_range=data.get('salary_range'),
            experience_required=data.get('experience_required'),
            description=description,
            responsibilities=as_list(data.get('responsibilities'), '\n'),
            required_skills=as_list(data.get('required_skills')),
            nice_to_have=as_list(data.get('nice_to_have'), ','),
            benefits=as_list(data.get('benefits'), ','),
        )

        db.session.add(new_job)
        db.session.commit()
        return jsonify({'job': job_payload(new_job)}), 201

    except Exception:
        db.session.rollback()
        current_app.logger.exception('job posting failed')
        return jsonify({'error': 'Error posting job. Please try again.'}), 500


# ─── 5. RECRUITER: VIEW APPLICANTS ──────────────────────────────────────────
@jobs.route('/api/recruiter/jobs/<int:job_id>/applicants', methods=['GET'])
@login_required
def view_applicants(job_id):
    job = JobPost.query.get_or_404(job_id)
    if not current_user.recruiter_profile or job.recruiter_id != current_user.recruiter_profile.id:
        return jsonify({'error': 'Unauthorized access.'}), 403

    applications = Application.query.filter_by(job_id=job_id).all()

    applicants_data = []
    for app in applications:
        seeker = app.seeker
        user = seeker.user
        applicants_data.append({
            'id': app.id,
            'name': user.name,
            'email': user.email,
            'phone': seeker.phone,
            'experience': seeker.experience_years,
            'user_id': user.id,
            'skills': seeker.skills or [],
            'status': app.status,
            'match_score': app.match_score,
            'applied_at': app.applied_at.strftime('%Y-%m-%d') if app.applied_at else None,
            'resume': seeker.resume_file,
        })

    # Pending first, closed (Accepted/Rejected) last
    applicants_data.sort(key=lambda x: 1 if x['status'] in ['Accepted', 'Rejected'] else 0)

    return jsonify({'job': job_payload(job, include_description=False), 'applicants': applicants_data})


# ─── 6. RECRUITER: UPDATE STATUS ────────────────────────────────────────────
@jobs.route('/api/applications/<int:app_id>/status', methods=['POST'])
@login_required
def update_status(app_id):
    data = request.get_json(silent=True) or {}
    status = (data.get('status') or '').strip()

    # Bug fix: only known statuses may be written.
    if status not in VALID_STATUSES:
        return jsonify({'error': f'Invalid status. Allowed: {sorted(VALID_STATUSES)}'}), 400

    app_record = Application.query.get_or_404(app_id)
    job = app_record.job

    if not current_user.recruiter_profile or job.recruiter_id != current_user.recruiter_profile.id:
        return jsonify({'error': 'Unauthorized.'}), 403

    app_record.status = status
    db.session.commit()

    candidate = app_record.seeker.user
    job_title = job.title
    recruiter_email = current_user.email

    email_ok, email_msg = True, ''
    if status == 'Shortlisted':
        email_ok, email_msg = send_interview_invite(candidate.email, candidate.name, job_title, recruiter_email)
    elif status == 'Accepted':
        email_ok, email_msg = send_job_offer(candidate.email, candidate.name, job_title)
    elif status == 'Rejected':
        email_ok, email_msg = send_rejection(candidate.email, candidate.name, job_title)

    return jsonify({
        'application': {'id': app_record.id, 'status': app_record.status},
        'email_sent': email_ok,
        'email_error': None if email_ok else email_msg,
    })


# ─── 7. LIVE (EXTERNAL) JOBS ────────────────────────────────────────────────
_FEED_CACHE = {}
_FEED_TTL_SECONDS = 600


def _cached(key, fetcher):
    hit = _FEED_CACHE.get(key)
    if hit and time.time() - hit[0] < _FEED_TTL_SECONDS:
        return hit[1]
    data = fetcher()
    _FEED_CACHE[key] = (time.time(), data)
    return data


@jobs.route('/api/live-jobs', methods=['GET'])
@login_required
def live_jobs():
    if current_user.role != 'seeker':
        return jsonify({'error': 'Seekers only.'}), 403

    source = request.args.get('feed', 'india')
    if source == 'remote':
        raw_jobs = fetch_remotive()
    elif source == 'carrerlift':
        raw_jobs = fetch_carrerlift()
    elif source == 'aicte-govt':
        raw_jobs = fetch_aicte('government')
    elif source == 'aicte-private':
        raw_jobs = fetch_aicte('private')
    elif source == 'tech':
        raw_jobs = fetch_remoteok() + fetch_jobicy()
    elif source == 'rss':
        raw_jobs = fetch_rss('weworkremotely') + fetch_rss('hn') + fetch_rss('python')
    elif source == 'usa':
        raw_jobs = fetch_usajobs()
    elif source == 'europe':
        raw_jobs = fetch_arbeitnow()
    else:
        raw_jobs = fetch_indian_jobs()
        source = 'india'

    for job in raw_jobs:
        if job.get('description'):
            soup = BeautifulSoup(job['description'], 'html.parser')
            job['clean_description'] = soup.get_text(separator=' ')
        else:
            job['clean_description'] = 'No description available.'

    return jsonify({'jobs': raw_jobs, 'feed': source})


def fetch_remotive():
    try:
        url = 'https://remotive.com/api/remote-jobs?category=software-dev&limit=20'
        resp = requests.get(url, timeout=5).json()
        result = []
        for j in resp.get('jobs', []):
            result.append({
                'title': j.get('title'),
                'company': j.get('company_name'),
                'location': j.get('candidate_required_location'),
                'url': j.get('url'),
                'description': j.get('description'),
                'logo': j.get('company_logo'),
                'source': 'Remotive',
            })
        return result
    except Exception as e:
        print(f'Remotive Error: {e}')
        return []


def fetch_indian_jobs():
    try:
        app_id = os.environ.get('APP_ID')
        app_key = os.environ.get('APP_KEY')
        if not app_id or not app_key:
            return []
        url = (
            f'https://api.adzuna.com/v1/api/jobs/in/search/1'
            f'?app_id={app_id}&app_key={app_key}&results_per_page=15'
            f'&what=software&category=it-jobs&content-type=application/json'
        )
        resp = requests.get(url, timeout=5).json()
        result = []
        for j in resp.get('results', []):
            result.append({
                'title': j.get('title'),
                'company': (j.get('company') or {}).get('display_name'),
                'location': (j.get('location') or {}).get('display_name'),
                'url': j.get('redirect_url'),
                'description': j.get('description'),
                'logo': None,
                'source': 'Adzuna (India)',
            })
        return result
    except Exception as e:
        print(f'Adzuna Error: {e}')
        return []


def fetch_carrerlift():
    def _scrape():
        jobs = []
        seen = set()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
        }
        for page in (1, 2):
            try:
                params = {'page': page} if page > 1 else {}
                resp = requests.get(
                    'https://www.carrerlift.in/jobs',
                    params=params,
                    headers=headers,
                    timeout=8,
                )
                resp.raise_for_status()
            except Exception as e:
                print(f'Carrerlift Error: {e}')
                continue
            soup = BeautifulSoup(resp.text, 'html.parser')
            for h2 in soup.find_all('h2'):
                anchor = h2.find('a', href=re.compile(r'^/jobs/'))
                if not anchor or anchor['href'] in seen:
                    continue
                card = h2.find_parent('div', class_='rounded-xl')
                if not card:
                    continue
                seen.add(anchor['href'])
                meta = {}
                for dt in card.find_all('dt'):
                    dd = dt.find_next_sibling('dd')
                    if dd:
                        meta[dt.get_text(strip=True)] = dd.get_text(' ', strip=True)
                company_el = card.find('p', class_='truncate')
                desc_el = card.find('p', class_='line-clamp-2')
                external = card.find('a', target='_blank', href=re.compile(r'^https?://'))
                jobs.append({
                    'title': anchor.get_text(' ', strip=True),
                    'company': company_el.get_text(strip=True) if company_el else None,
                    'location': meta.get('Location'),
                    'stipend': meta.get('Stipend'),
                    'url': external['href'] if external else 'https://www.carrerlift.in' + anchor['href'],
                    'description': desc_el.get_text(' ', strip=True) if desc_el else '',
                    'logo': None,
                    'source': 'Carrerlift',
                })
        return jobs
    return _cached('carrerlift', _scrape)


def fetch_aicte(section):
    def _fetch():
        categories = {'government': 'Government,Army,TULIP', 'private': 'Corporate,MSME,NGO'}[section]
        label = {'government': 'AICTE (Govt)', 'private': 'AICTE (Private)'}[section]
        try:
            resp = requests.get(
                'https://internship.aicte-india.org/api/v1/catalogue/internships',
                params={'categories': categories, 'pageSize': 60},
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json().get('items', [])
        except Exception as e:
            print(f'AICTE Error: {e}')
            return []
        base = 'https://internship.aicte-india.org'
        jobs = []
        for item in items:
            uid = item.get('uid')
            if not uid:
                continue
            logo = item.get('logo')
            jobs.append({
                'title': item.get('title'),
                'company': item.get('organization'),
                'location': item.get('location'),
                'stipend': item.get('stipendDisplay') if item.get('stipend') else None,
                'url': f'{base}/internships/{uid}',
                'description': item.get('description') or '',
                'logo': f'{base}{logo}' if logo and logo.startswith('/') else logo,
                'source': label,
            })
        return jobs
    return _cached(f'aicte:{section}', _fetch)


def fetch_greenhouse(board):
    def _fetch():
        try:
            resp = requests.get(
                f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs',
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json().get('jobs', [])
        except Exception as e:
            print(f'Greenhouse {board} Error: {e}')
            return []
        jobs = []
        for item in items:
            url = item.get('absolute_url')
            if not url:
                continue
            jobs.append({
                'title': item.get('title'),
                'company': item.get('company_name') or board.replace('-', ' ').title(),
                'location': (item.get('location') or {}).get('name'),
                'stipend': None,
                'url': url,
                'description': '',
                'logo': None,
                'source': f'Greenhouse ({board})',
            })
        return jobs
    return _cached(f'gh:{board}', _fetch)


def fetch_lever(company):
    def _fetch():
        try:
            resp = requests.get(
                f'https://api.lever.co/v0/postings/{company}?mode=json',
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json()
        except Exception as e:
            print(f'Lever {company} Error: {e}')
            return []
        jobs = []
        for item in items:
            url = item.get('hostedUrl')
            if not url:
                continue
            cats = item.get('categories') or {}
            jobs.append({
                'title': item.get('text'),
                'company': company.title(),
                'location': cats.get('location'),
                'stipend': None,
                'url': url,
                'description': item.get('descriptionPlain') or '',
                'logo': None,
                'source': f'Lever ({company})',
            })
        return jobs
    return _cached(f'lever:{company}', _fetch)


ASHBY_DISPLAY = {
    'openai': 'OpenAI', 'notion': 'Notion', 'ramp': 'Ramp', 'cursor': 'Cursor',
    'cohere': 'Cohere', 'linear': 'Linear', 'supabase': 'Supabase',
    'modal': 'Modal', 'anyscale': 'Anyscale', 'runway': 'Runway',
}


def fetch_ashby(board):
    def _fetch():
        try:
            resp = requests.get(
                f'https://api.ashbyhq.com/posting-api/job-board/{board}',
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json().get('jobs', [])
        except Exception as e:
            print(f'Ashby {board} Error: {e}')
            return []
        jobs = []
        for item in items:
            url = item.get('jobUrl')
            if not url:
                continue
            jobs.append({
                'title': (item.get('title') or '').strip() or None,
                'company': ASHBY_DISPLAY.get(board, board.title()),
                'location': item.get('location'),
                'stipend': None,
                'url': url,
                'description': item.get('descriptionHtml') or '',
                'logo': None,
                'source': f'Ashby ({board})',
            })
        return jobs
    return _cached(f'ashby:{board}', _fetch)


def fetch_remoteok():
    def _fetch():
        try:
            resp = requests.get(
                'https://remoteok.com/api',
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json()
        except Exception as e:
            print(f'RemoteOK Error: {e}')
            return []
        jobs = []
        for item in items:
            if not isinstance(item, dict) or not item.get('position'):
                continue
            salary_min = item.get('salary_min')
            salary_max = item.get('salary_max')
            stipend = f'${salary_min:,} - ${salary_max:,}' if salary_min and salary_max else None
            jobs.append({
                'title': item.get('position'),
                'company': item.get('company'),
                'location': item.get('location') or 'Remote',
                'stipend': stipend,
                'url': item.get('url'),
                'description': item.get('description') or '',
                'logo': item.get('company_logo') or None,
                'source': 'RemoteOK',
            })
        return jobs
    return _cached('remoteok', _fetch)


def fetch_jobicy():
    def _fetch():
        try:
            resp = requests.get(
                'https://jobicy.com/api/v2/remote-jobs?count=25',
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json().get('jobs', [])
        except Exception as e:
            print(f'Jobicy Error: {e}')
            return []
        jobs = []
        for item in items:
            url = item.get('url')
            if not url:
                continue
            jobs.append({
                'title': item.get('jobTitle'),
                'company': item.get('companyName'),
                'location': item.get('jobGeo') or 'Remote',
                'stipend': None,
                'url': url,
                'description': item.get('jobExcerpt') or '',
                'logo': item.get('companyLogo') or None,
                'source': 'Jobicy',
            })
        return jobs
    return _cached('jobicy', _fetch)


RSS_FEEDS = {
    'weworkremotely': {
        'url': 'https://weworkremotely.com/categories/remote-programming-jobs.rss',
        'label': 'We Work Remotely',
    },
    'hn': {
        'url': 'https://hnrss.org/jobs',
        'label': 'Hacker News Jobs',
    },
    'python': {
        'url': 'https://www.python.org/jobs/feed/rss/',
        'label': 'Python.org Jobs',
    },
}


def fetch_rss(source):
    feed = RSS_FEEDS.get(source)
    if not feed:
        return []

    def _fetch():
        try:
            resp = requests.get(
                feed['url'],
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=8,
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
        except Exception as e:
            print(f'RSS {source} Error: {e}')
            return []
        jobs = []
        for item in root.iter('item'):
            title = (item.findtext('title') or '').strip()
            url = (item.findtext('link') or '').strip()
            if not title or not url:
                continue
            company = feed['label']
            if ' - ' in title:
                name, role = title.rsplit(' - ', 1)
            elif ': ' in title:
                name, role = title.split(': ', 1)
            else:
                name, role = '', title
            if name.strip() and len(name) < 60:
                company, title = name.strip(), role.strip()
            jobs.append({
                'title': title[:100],
                'company': company[:100],
                'location': 'Remote',
                'stipend': None,
                'url': url,
                'description': item.findtext('description') or '',
                'logo': None,
                'source': feed['label'],
            })
        return jobs
    return _cached(f'rss:{source}', _fetch)


def fetch_usajobs(keyword='python'):
    key = os.environ.get('USAJOBS_KEY')
    if not key:
        return []

    def _fetch():
        try:
            resp = requests.get(
                'https://data.usajobs.gov/api/search',
                params={
                    'Keyword': keyword,
                    'LocationName': 'United States',
                    'ResultsPerPage': 25,
                },
                headers={
                    'Authorization-Key': key,
                    'User-Agent': os.environ.get('USAJOBS_USER_AGENT') or 'skillmap',
                },
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json().get('SearchResult', {}).get('SearchResultItems', [])
        except Exception as e:
            print(f'USAJOBS Error: {e}')
            return []
        jobs = []
        for item in items:
            d = item.get('MatchedObjectDescriptor') or {}
            url = d.get('PositionURI')
            if not url:
                continue
            location = (d.get('PositionLocationDisplay') or 'United States').split(';')[0]
            jobs.append({
                'title': d.get('PositionTitle'),
                'company': d.get('OrganizationName') or 'US Federal Government',
                'location': location[:100],
                'stipend': None,
                'url': url,
                'description': d.get('QualificationSummary') or '',
                'logo': None,
                'source': 'USAJOBS',
            })
        return jobs
    return _cached(f'usajobs:{keyword}', _fetch)


def fetch_arbeitnow():
    def _fetch():
        try:
            resp = requests.get(
                'https://www.arbeitnow.com/api/job-board-api',
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=8,
            )
            resp.raise_for_status()
            items = resp.json().get('data', [])
        except Exception as e:
            print(f'Arbeitnow Error: {e}')
            return []
        jobs = []
        for item in items:
            url = item.get('url')
            if not url:
                continue
            jobs.append({
                'title': item.get('title'),
                'company': item.get('company_name'),
                'location': 'Remote' if item.get('remote') else item.get('location') or 'Germany',
                'stipend': None,
                'url': url,
                'description': item.get('description') or '',
                'logo': None,
                'source': 'Arbeitnow (Germany)',
            })
        return jobs
    return _cached('arbeitnow', _fetch)
