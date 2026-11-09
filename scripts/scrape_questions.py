"""Build the interview-question corpus for Company Prep Packs.

Sources (pluggable adapters, run independently so one blocked source
doesn't sink the pipeline):

  1. github    liquidslr/leetcode-company-wise-problems — per-company CSVs
               (title, difficulty, frequency, topics). Volume source.
  2. interviewbit  <company>-interview-questions/ pages — structured DSA
               problems (window.__INTERVIEWBIT__.sectionalProblems) plus the
               recruitment/rounds prose stored on companies.meta.

Both are permitted by their robots.txt (only /profile is disallowed on
interviewbit.com; GitHub raw/API is meant for programmatic access).

Policy: 1 request / 2s per host, browser User-Agent, robots.txt honoured,
raw responses cached on disk (scripts/.scrape_cache) so re-runs are free.

Embeddings: local fastembed BAAI/bge-base-en-v1.5, 768-dim (no API quota;
Gemini's free tier allowed only 1000 embed texts/day), written only to rows
whose embedding IS NULL.

Usage:
    python3 scripts/scrape_questions.py --dry-run --limit 5
    python3 scripts/scrape_questions.py --limit 40
    python3 scripts/scrape_questions.py --no-embed
"""

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

import requests
from sqlalchemy import text as sqltext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CACHE_DIR = Path(__file__).resolve().parent / '.scrape_cache'
MIN_INTERVAL = 2.0  # seconds between requests to the same host
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
)
ACCEPT_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

GH_REPO = 'liquidslr/leetcode-company-wise-problems'
GH_TREE_URL = f'https://api.github.com/repos/{GH_REPO}/git/trees/HEAD?recursive=0'
IB_SITEMAP_URL = 'https://www.interviewbit.com/sitemaps/cms.xml.gz'


# --------------------------------------------------------------------------
# Polite fetching: rate limit + robots.txt + disk cache
# --------------------------------------------------------------------------

class PoliteFetcher:
    def __init__(self, refresh=False):
        self.refresh = refresh
        self._last_hit = {}
        self._robots = {}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT, **ACCEPT_HEADERS})

    @staticmethod
    def _key(url):
        return hashlib.sha1(url.encode()).hexdigest()

    def _body_path(self, url):
        return CACHE_DIR / (self._key(url) + '.body')

    def _meta_path(self, url):
        return CACHE_DIR / (self._key(url) + '.json')

    def _wait(self, url):
        host = urllib.parse.urlparse(url).netloc
        last = self._last_hit.get(host, 0)
        gap = time.time() - last
        if gap < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - gap)
        self._last_hit[host] = time.time()

    def robots_allowed(self, url):
        """Honour robots.txt. Missing/unparsable file => allowed (standard)."""
        parts = urllib.parse.urlparse(url)
        origin = f'{parts.scheme}://{parts.netloc}'
        if origin in self._robots:
            return self._robots[origin]

        allowed = True
        rp = urllib.robotparser.RobotFileParser()
        try:
            self._wait(origin + '/robots.txt')
            resp = self.session.get(origin + '/robots.txt', timeout=15)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                allowed = rp.can_fetch(USER_AGENT, url)
        except Exception as exc:
            print(f'    robots.txt check failed for {origin} ({exc}) -> allowing')
        self._robots[origin] = allowed
        return allowed

    def get(self, url, accept_gzip=False):
        """Return (status, text) from cache when possible, else the network."""
        if not self.refresh:
            body_p, meta_p = self._body_path(url), self._meta_path(url)
            if body_p.exists() and meta_p.exists():
                try:
                    meta = json.loads(meta_p.read_text())
                    return meta['status'], body_p.read_bytes()
                except Exception:
                    pass  # corrupt cache -> refetch

        if not self.robots_allowed(url):
            print(f'    BLOCKED by robots.txt: {url}')
            return 403, b''

        self._wait(url)
        headers = dict(ACCEPT_HEADERS)
        if accept_gzip:
            headers['Accept-Encoding'] = 'gzip'
        resp = self.session.get(url, timeout=30, headers=headers)
        data = resp.content

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._body_path(url).write_bytes(data)
        self._meta_path(url).write_text(json.dumps({'url': url, 'status': resp.status_code}))
        return resp.status_code, data


# --------------------------------------------------------------------------
# Company discovery
# --------------------------------------------------------------------------

def normalize(name):
    return re.sub(r'[^a-z0-9]', '', (name or '').lower())


def discover_companies(fetcher):
    """Merge company lists from both sources into {norm: {name, gh, ib}}."""
    companies = {}

    # --- GitHub folder tree ---
    status, raw = fetcher.get(GH_TREE_URL)
    if status == 200:
        try:
            tree = json.loads(raw).get('tree', [])
            for node in tree:
                if node.get('type') != 'tree':
                    continue
                name = node['path']
                if name.startswith('.') or name.lower() == 'readme':
                    continue
                companies.setdefault(normalize(name), {})['name'] = name
                companies[normalize(name)]['gh'] = name
            print(f'GitHub: {sum(1 for c in companies.values() if c.get("gh"))} company folders')
        except Exception as exc:
            print(f'GitHub tree parse failed: {exc}')
    else:
        print(f'GitHub tree fetch failed (HTTP {status})')

    # --- InterviewBit sitemap ---
    status, raw = fetcher.get(IB_SITEMAP_URL, accept_gzip=True)
    if status == 200:
        try:
            import gzip
            xml = gzip.decompress(raw).decode('utf-8', 'ignore')
            slugs = []
            for loc in re.findall(r'<loc>([^<]+)</loc>', xml):
                m = re.match(r'https://www\.interviewbit\.com/([a-z0-9-]+)-interview-questions/?$', loc)
                if m:
                    slugs.append(m.group(1))
            for slug in slugs:
                key = normalize(slug)
                companies.setdefault(key, {})
                companies[key]['ib'] = slug
                companies[key].setdefault('name', slug.replace('-', ' ').title())
            print(f'InterviewBit: {len(slugs)} company pages')
            both = sum(1 for c in companies.values() if c.get('gh') and c.get('ib'))
            print(f'Overlap: {both} companies in both sources')
        except Exception as exc:
            print(f'InterviewBit sitemap parse failed: {exc}')
    else:
        print(f'InterviewBit sitemap fetch failed (HTTP {status})')

    return companies


# --------------------------------------------------------------------------
# Adapters
# --------------------------------------------------------------------------

class GithubCsvSource:
    """Per-company CSVs from liquidslr/leetcode-company-wise-problems."""

    name = 'leetcode-company-wise'

    def __init__(self, fetcher):
        self.fetcher = fetcher

    def fetch(self, folder):
        url = f'https://raw.githubusercontent.com/{GH_REPO}/HEAD/{urllib.parse.quote(folder)}/5.%20All.csv'
        status, raw = self.fetcher.get(url)
        if status != 200:
            return [], None

        try:
            text = raw.decode('utf-8-sig', 'ignore')
            reader = csv.DictReader(io.StringIO(text))
            rows = []
            for r in reader:
                # tolerate column renames
                low = { (k or '').strip().lower(): (v or '').strip() for k, v in r.items() }
                title = low.get('title') or low.get('problem_statement') or ''
                if not title:
                    continue
                difficulty = (low.get('difficulty') or '').capitalize()
                topics = low.get('topics') or low.get('topic') or ''
                link = low.get('link') or low.get('url') or ''
                freq = low.get('frequency') or '0'
                rows.append({
                    'question': title,
                    'category': ': '.join(p for p in (difficulty, topics) if p),
                    'source_url': link,
                    'sort': _float(freq),
                })
            rows.sort(key=lambda x: x['sort'], reverse=True)
            return rows, None
        except Exception as exc:
            print(f'    CSV parse failed for {folder}: {exc}')
            return [], None


class InterviewBitSource:
    """Structured DSA problems + recruitment/rounds prose from one page."""

    name = 'interviewbit'

    def __init__(self, fetcher):
        self.fetcher = fetcher

    def fetch(self, slug):
        url = f'https://www.interviewbit.com/{slug}-interview-questions/'
        status, raw = self.fetcher.get(url)
        if status != 200:
            return [], None

        html = raw.decode('utf-8', 'ignore')
        rows, meta = [], None

        # 1. structured problems blob
        m = re.search(r'sectionalProblems:\s*(\{.*?\})\s*,?\s*\n', html, re.S)
        if m:
            try:
                blob = json.loads(m.group(1))
                for difficulty, items in blob.items():
                    for it in items:
                        title = (it.get('problem_statement') or '').strip()
                        if not title:
                            continue
                        topic = (it.get('topic_title') or '').strip()
                        rows.append({
                            'question': title,
                            'category': ': '.join(p for p in (difficulty.capitalize(), topic) if p),
                            'source_url': f'https://www.interviewbit.com/problems/{it.get("slug", "")}/',
                            'sort': _float(it.get('score')),
                        })
            except Exception as exc:
                print(f'    sectionalProblems parse failed for {slug}: {exc}')

        # 2. rounds prose -> companies.meta (never re-scraped at runtime)
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            rounds = []
            for strong in soup.find_all('strong'):
                label = strong.get_text(strip=True)
                if 'round' not in label.lower():
                    continue
                parent_text = strong.find_parent().get_text(' ', strip=True)
                if parent_text and len(parent_text) > 40:
                    rounds.append(parent_text[:1500])
            if rounds:
                meta = {'rounds': rounds, 'source_url': url,
                        'scraped_at': datetime.now(timezone.utc).isoformat()}
        except Exception as exc:
            print(f'    rounds prose extraction failed for {slug}: {exc}')

        return rows, meta


def _float(value):
    try:
        return float(re.sub(r'[^0-9.]', '', str(value)) or 0)
    except Exception:
        return 0.0


# --------------------------------------------------------------------------
# Embedding
# --------------------------------------------------------------------------

EMBED_MODEL = 'BAAI/bge-base-en-v1.5'   # 768-dim, matches vector(768) schema
_embedder_cache = None


def _embedder():
    """Lazy singleton — first call downloads the ONNX model (~400 MB, cached)."""
    global _embedder_cache
    if _embedder_cache is None:
        from fastembed import TextEmbedding
        _embedder_cache = TextEmbedding(model_name=EMBED_MODEL)
    return _embedder_cache


def embed_texts(texts, batch_size=100):
    """Local fastembed (BAAI/bge-base-en-v1.5), 768-dim. Returns list of lists.

    Replaced Gemini: its free tier caps embeddings at 1000 texts/day, far
    below this corpus. Local inference has no quota and no rate limits.
    """
    model = _embedder()
    out = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i:i + batch_size]
        out.extend(v.tolist() for v in model.embed(chunk))
        print(f'    embedded {min(i + batch_size, len(texts))}/{len(texts)}',
              flush=True)
    return out


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

INSERT_SQL = sqltext("""
    INSERT INTO questions
        (company_id, role, question, category, source, source_url, dedupe_hash, embedding)
    VALUES
        (:company_id, :role, :question, :category, :source, :source_url,
         :dedupe_hash, CAST(:embedding AS vector))
    ON CONFLICT (dedupe_hash) DO UPDATE
        SET embedding = EXCLUDED.embedding
    WHERE questions.embedding IS NULL
""")


def dedupe_hash(company_slug, role, question):
    norm = re.sub(r'\s+', ' ', question).strip().lower()
    norm = re.sub(r'[^\w\s]', '', norm)
    return hashlib.sha1(f'{company_slug}|{role}|{norm}'.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description='Scrape interview questions into Neon')
    ap.add_argument('--limit', type=int, default=0, help='max companies (0 = all matched)')
    ap.add_argument('--per-company', type=int, default=150, help='max questions per company')
    ap.add_argument('--sources', default='github,interviewbit', help='comma list')
    ap.add_argument('--no-embed', action='store_true', help='skip Gemini embedding')
    ap.add_argument('--embed-only', action='store_true',
                    help='skip scraping; only embed rows with embedding IS NULL')
    ap.add_argument('--dry-run', action='store_true', help='no DB writes, no embedding')
    ap.add_argument('--refresh', action='store_true', help='ignore disk cache')
    args = ap.parse_args()

    if args.embed_only:
        # resume just the embedding pass — no discovery, no network scrape
        from app import create_app, db
        app = create_app()
        with app.app_context():
            embed_pending(db.session)
            total = db.session.execute(
                sqltext('SELECT count(*) FROM questions')).scalar()
            embedded = db.session.execute(sqltext(
                'SELECT count(*) FROM questions WHERE embedding IS NOT NULL')).scalar()
            print(f'\nDone. questions={total} embedded={embedded}')
        return

    wanted = {s.strip() for s in args.sources.split(',') if s.strip()}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    fetcher = PoliteFetcher(refresh=args.refresh)
    companies = discover_companies(fetcher)

    # only companies present in a source we actually want
    eligible = []
    for key, info in companies.items():
        if 'github' in wanted and info.get('gh'):
            eligible.append((key, info))
        elif 'interviewbit' in wanted and info.get('ib'):
            eligible.append((key, info))
    eligible.sort(key=lambda kv: kv[1].get('name', '').lower())
    if args.limit:
        eligible = eligible[:args.limit]

    print(f'\nProcessing {len(eligible)} companies '
          f'(sources: {", ".join(sorted(wanted))})\n')

    gh_src = GithubCsvSource(fetcher) if 'github' in wanted else None
    ib_src = InterviewBitSource(fetcher) if 'interviewbit' in wanted else None

    # Flask-SQLAlchemy's scoped session requires an application context for
    # every DB call, so the entire scrape/insert loop runs inside one.
    app = None
    if not args.dry_run:
        from app import create_app
        app = create_app()

    _ctx = app.app_context() if app else None
    if _ctx:
        _ctx.push()

    try:
        _run_loop(args, wanted, eligible, fetcher, gh_src, ib_src)
    finally:
        if _ctx:
            _ctx.pop()


def _run_loop(args, wanted, eligible, fetcher, gh_src, ib_src):
    from app import db

    session = db.session
    pending = []          # rows ready to insert
    company_ids = {}      # norm -> companies.id
    stats = {'github': 0, 'interviewbit': 0, 'skipped_no_source': 0,
             'dupes': 0, 'companies': 0}

    def flush(force=False):
        if not pending or args.dry_run:
            if force and pending:
                print(f'  (dry-run) {len(pending)} rows would be inserted')
            return
        while pending:
            batch = pending[:500]
            del pending[:500]
            session.execute(INSERT_SQL, batch)
            session.commit()

    for idx, (key, info) in enumerate(eligible, 1):
        name = info.get('name') or key
        parts = []
        collected = {}

        if gh_src and info.get('gh'):
            rows, _ = gh_src.fetch(info['gh'])
            for r in rows:
                collected.setdefault(dedupe_hash(key, '', r['question']), r)
                collected[dedupe_hash(key, '', r['question'])]['src'] = 'github'
            stats['github'] += len(rows)
            parts.append(f'github={len(rows)}')

        if ib_src and info.get('ib'):
            rows, meta = ib_src.fetch(info['ib'])
            for r in rows:
                h = dedupe_hash(key, '', r['question'])
                if h not in collected:
                    collected[h] = r
                    collected[h]['src'] = 'interviewbit'
            stats['interviewbit'] += len(rows)
            parts.append(f'interviewbit={len(rows)}')
        else:
            meta = None

        if not collected:
            stats['skipped_no_source'] += 1
            print(f'[{idx}/{len(eligible)}] {name}: no data ({", ".join(parts) or "no source"})')
            continue

        # cap per company, keep highest-sorted
        ordered = sorted(collected.values(), key=lambda r: r.get('sort', 0),
                         reverse=True)[:args.per_company]
        stats['companies'] += 1
        stats['dupes'] += len(collected) - len(ordered)

        if args.dry_run:
            print(f'[{idx}/{len(eligible)}] {name}: {len(ordered)} rows '
                  f'({", ".join(parts)}) [dry-run]')
            continue

        # upsert company
        session.execute(sqltext("""
            INSERT INTO companies (name, slug, aliases, meta)
            VALUES (:name, :slug, '[]'::jsonb, CAST(:meta AS jsonb))
            ON CONFLICT (slug) DO UPDATE
                SET meta = CASE WHEN EXCLUDED.meta = '{}'::jsonb
                                THEN companies.meta ELSE EXCLUDED.meta END
        """), {'name': name, 'slug': key,
               'meta': json.dumps(meta or {})})
        session.commit()
        cid = session.execute(sqltext('SELECT id FROM companies WHERE slug = :s'),
                              {'s': key}).scalar()
        company_ids[key] = cid

        for r in ordered:
            pending.append({
                'company_id': cid,
                'role': '',
                'question': r['question'],
                'category': r.get('category') or '',
                'source': r.get('src', 'github'),
                'source_url': r.get('source_url') or '',
                'dedupe_hash': dedupe_hash(key, '', r['question']),
                'embedding': None,
            })

        print(f'[{idx}/{len(eligible)}] {name}: {len(ordered)} rows ({", ".join(parts)})')
        if len(pending) >= 2000:
            flush()

    flush()

    # ---- embedding pass (already inside the app context pushed by main) ----
    if not args.dry_run and not args.no_embed:
        embed_pending(session)

    if not args.dry_run:
        total = session.execute(sqltext('SELECT count(*) FROM questions')).scalar()
        embedded = session.execute(
            sqltext('SELECT count(*) FROM questions WHERE embedding IS NOT NULL')).scalar()
        comps = session.execute(sqltext('SELECT count(*) FROM companies')).scalar()
        print(f'\nDone. companies={comps} questions={total} embedded={embedded}')
    else:
        print('\nDry run — nothing written.')


def embed_pending(session):
    """Embed every row whose embedding IS NULL (idempotent, resumable).

    Each batch is written and committed immediately so an interrupted run
    keeps its progress; DB writes retry once if the Neon pooler drops the
    idle SSL connection during a rate-limit sleep.
    """
    from sqlalchemy import text as sqltext
    from sqlalchemy.exc import OperationalError

    rows = session.execute(sqltext(
        "SELECT id, question, COALESCE(category, '') AS category "
        "FROM questions WHERE embedding IS NULL ORDER BY id"
    )).fetchall()
    if not rows:
        print('\nNo rows need embedding.')
        return
    print(f'\nEmbedding {len(rows)} rows with {EMBED_MODEL}...', flush=True)
    texts = [f'{q}. {c}'.strip().rstrip('.') for _, q, c in rows]

    BATCH = 100
    for i in range(0, len(rows), BATCH):
        chunk_rows = rows[i:i + BATCH]
        vecs = embed_texts([t for t in texts[i:i + BATCH]], batch_size=BATCH)
        params = [{'v': json.dumps(v), 'id': rid}
                  for (rid, _, _), v in zip(chunk_rows, vecs)]
        for attempt in range(3):
            try:
                session.execute(
                    sqltext('UPDATE questions SET embedding = CAST(:v AS vector) '
                            'WHERE id = :id'),
                    params)
                session.commit()
                break
            except OperationalError:
                session.rollback()
                if attempt == 2:
                    raise
                print('    DB connection dropped, reconnecting...', flush=True)
                time.sleep(3)
    print('Embedding complete.')


if __name__ == '__main__':
    main()
