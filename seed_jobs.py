import re

from bs4 import BeautifulSoup

from app import create_app, db
from app.models import JobPost
from app.jobs.routes import (
    fetch_remotive, fetch_indian_jobs, fetch_carrerlift, fetch_aicte,
    fetch_greenhouse, fetch_lever, fetch_ashby, fetch_remoteok, fetch_jobicy,
    fetch_rss, fetch_usajobs, fetch_arbeitnow,
)

SKILL_KEYWORDS = [
    'python', 'java', 'javascript', 'typescript', 'react', 'node', 'sql',
    'aws', 'docker', 'kubernetes', 'machine learning', 'data analysis',
    'excel', 'css', 'html', 'git', 'flask', 'django', 'spring', 'golang',
    'c++', 'php', 'angular', 'vue', 'redis', 'mongodb', 'pandas',
    'tensorflow', 'power bi', 'tableau', 'azure', 'gcp', 'linux',
    'graphql', 'firebase', 'redux', 'next.js', 'flutter', 'cybersecurity',
    'ethical hacking', 'networking', 'java script', 'rest api',
]

GH_BOARDS = [
    'airbnb', 'cloudflare', 'databricks', 'datadog', 'discord', 'elastic',
    'figma', 'gitlab', 'mongodb', 'pinterest', 'reddit', 'robinhood',
    'roblox', 'samsara', 'twilio', 'coinbase', 'affirm', 'asana',
    'instacart', 'lyft', 'mixpanel', 'gusto', 'checkr', 'circleci',
    'dropbox', 'airtable', 'pagerduty', 'inmobi',
]

ASHBY_BOARDS = [
    'openai', 'notion', 'ramp', 'cursor', 'cohere', 'linear',
    'supabase', 'modal', 'anyscale', 'runway',
]


def clean_text(raw):
    if not raw:
        return ''
    text = BeautifulSoup(raw, 'html.parser').get_text(separator=' ')
    return re.sub(r'\s+', ' ', text).strip()[:1200]


def extract_skills(text):
    low = text.lower()
    return [k for k in SKILL_KEYWORDS if k in low][:8]


def main():
    app = create_app()
    with app.app_context():
        existing = {
            url for (url,) in JobPost.query.with_entities(JobPost.external_link)
            .filter(JobPost.external_link.isnot(None)).all()
        }
        sources = [
            (fetch_remotive(), 'Remote', 20),
            (fetch_indian_jobs(), 'Full-time', 20),
            (fetch_carrerlift(), 'Internship', 20),
            (fetch_aicte('government'), 'Internship', 20),
            (fetch_aicte('private'), 'Internship', 20),
            (fetch_remoteok(), 'Remote', 15),
            (fetch_jobicy(), 'Remote', 15),
            (fetch_rss('weworkremotely'), 'Remote', 20),
            (fetch_rss('hn'), 'Full-time', 20),
            (fetch_rss('python'), 'Full-time', 15),
            (fetch_usajobs(), 'Full-time', 20),
            (fetch_arbeitnow(), 'Full-time', 15),
            (fetch_lever('palantir'), 'Full-time', 10),
        ]
        for board in GH_BOARDS:
            sources.append((fetch_greenhouse(board), 'Full-time', 8))
        for board in ASHBY_BOARDS:
            sources.append((fetch_ashby(board), 'Full-time', 8))

        added = 0
        for jobs, default_type, cap in sources:
            for j in jobs[:cap]:
                url = j.get('url')
                title = (j.get('title') or '').strip()[:100]
                if not url or url in existing or not title:
                    continue
                description = clean_text(j.get('description'))
                if not description:
                    description = f'{title} - visit the posting for full details.'
                stipend = (j.get('stipend') or '').strip()[:50] or None
                db.session.add(JobPost(
                    recruiter_id=None,
                    company_name=(j.get('company') or 'Company')[:100],
                    title=title,
                    description=description,
                    location=(j.get('location') or 'Remote')[:100],
                    salary_range=stipend,
                    job_type=default_type,
                    experience_required='Entry level',
                    responsibilities=[],
                    required_skills=extract_skills(f'{title} {description}'),
                    nice_to_have=[],
                    benefits=[],
                    is_active=True,
                    is_seeded=True,
                    external_link=url[:255],
                ))
                existing.add(url)
                added += 1
        db.session.commit()
        print(f'Added {added} seeded jobs (total now {JobPost.query.count()})')


if __name__ == '__main__':
    main()
