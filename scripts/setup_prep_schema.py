"""Create the Company Prep Pack data layer in Neon.

Idempotent: safe to re-run. Sets up:
  - pgvector extension
  - companies       (canonical company records)
  - questions       (interview-question corpus w/ 768-dim embeddings)
  - prep_packs      (per company+role cached pack — the free-tier sustainability key)

Usage:
    python3 scripts/setup_prep_schema.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app import create_app, db

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS companies (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    slug        TEXT NOT NULL UNIQUE,
    aliases     JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- meta holds scraped per-company round structure / recruitment prose
-- (InterviewBit) so pack synthesis never needs a live scrape at runtime.
ALTER TABLE companies ADD COLUMN IF NOT EXISTS meta JSONB NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS questions (
    id           SERIAL PRIMARY KEY,
    company_id   INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    role         TEXT NOT NULL DEFAULT '',
    question     TEXT NOT NULL,
    category     TEXT,
    source       TEXT NOT NULL,
    source_url   TEXT,
    dedupe_hash  TEXT NOT NULL UNIQUE,
    embedding    VECTOR(768),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Hybrid retrieval: exact pgvector cosine scan + Postgres FTS.
-- No HNSW/ivfflat index on purpose: corpus stays well under 50k rows,
-- where a sequential exact scan is faster than building/refreshing an index.
CREATE INDEX IF NOT EXISTS questions_fts_idx
    ON questions USING GIN (to_tsvector('english', question));
CREATE INDEX IF NOT EXISTS questions_company_idx
    ON questions (company_id);
CREATE INDEX IF NOT EXISTS questions_role_idx
    ON questions (role);

CREATE TABLE IF NOT EXISTS prep_packs (
    id           SERIAL PRIMARY KEY,
    company_id   INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    role         TEXT NOT NULL,
    pack         JSONB NOT NULL,
    salary       JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (company_id, role)
);
"""


def main():
    app = create_app()
    with app.app_context():
        try:
            for statement in [s.strip() for s in SCHEMA_SQL.split(';') if s.strip()]:
                db.session.execute(text(statement))
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            print(f'Schema setup failed: {exc}')
            sys.exit(1)

        # Sanity check: does pgvector actually resolve VECTOR(768)?
        ok = db.session.execute(
            text("SELECT to_regclass('questions') IS NOT NULL "
                 "AND EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        ).scalar()
        if not ok:
            print('Tables created but pgvector extension is missing on this database.')
            sys.exit(1)

        counts = {
            t: db.session.execute(text(f'SELECT count(*) FROM {t}')).scalar()
            for t in ('companies', 'questions', 'prep_packs')
        }
        print('Prep schema ready:',
              ', '.join(f'{k}={v}' for k, v in counts.items()))


if __name__ == '__main__':
    main()
