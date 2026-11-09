"""Company Prep Pack synthesis.

Given (company, role) + retrieved corpus questions + scraped round-structure
prose, Groq synthesizes a structured pack: rounds breakdown, top 10-15 likely
questions with attribution, a tailored study plan, and tips.

Salary bands come from Adzuna (already used by app/jobs/routes.py on the free
tier). Everything here is called at most once per (company, role) — the result
is cached in prep_packs, which keeps us inside Groq's free ~30 RPM limit.
"""

import os
import json
import requests
from groq import Groq

GROQ_MODEL = 'openai/gpt-oss-120b'

_query_embedder = None   # fastembed singleton (loaded on first request)


def get_client():
    api_key = os.environ.get('GROQ_API_KEY')
    return Groq(api_key=api_key) if api_key else None


def fetch_salary_band(role, company=''):
    """Salary band via Adzuna (IN + US). Returns dict or None; never raises."""
    app_id = os.environ.get('APP_ID')
    app_key = os.environ.get('APP_KEY')
    if not app_id or not app_key:
        return None

    bands = {}
    for country, label in (('in', 'INR'), ('us', 'USD')):
        try:
            url = (
                f'https://api.adzuna.com/v1/api/jobs/{country}/search/1'
                f'?app_id={app_id}&app_key={app_key}&results_per_page=20'
                f'&what={requests.utils.quote(role)}'
                f'&content-type=application/json'
            )
            resp = requests.get(url, timeout=8)
            if resp.status_code != 200:
                continue
            results = resp.json().get('results') or []
            mins = [r['salary_min'] for r in results if r.get('salary_min')]
            maxs = [r['salary_max'] for r in results if r.get('salary_max')]
            if mins and maxs:
                bands[country.lower()] = {
                    'currency': results[0].get('salary_currency') or label,
                    'min': round(min(mins)),
                    'max': round(max(maxs)),
                    'sample': len(results),
                }
        except Exception:
            continue
    return bands or None


def embed_query(text_):
    """Local bge-base-en-v1.5 768-dim query embedding (same vector space as
    the corpus — both sides must use identical models)."""
    global _query_embedder
    if _query_embedder is None:
        from fastembed import TextEmbedding
        _query_embedder = TextEmbedding(model_name='BAAI/bge-base-en-v1.5')
    vec = next(iter(_query_embedder.query_embed([text_])))
    return vec.tolist()


def synthesize_pack(company_name, role, rounds_prose, retrieved):
    """Groq pack synthesis. `retrieved` = list of dicts from hybrid retrieval.

    Returns the pack dict, or {} on failure (caller must not charge/caches).
    """
    client = get_client()
    if not client:
        return {}

    # Attribution input: corpus rows keep their real source; the model is told
    # to cite them as-is and to mark anything it adds as synthesized.
    corpus_lines = []
    for i, r in enumerate(retrieved, 1):
        corpus_lines.append(
            f'{i}. "{r["question"]}" [{r.get("category") or "unclassified"}]'
            f'{" — " + r["source_url"] if r.get("source_url") else ""}'
        )
    corpus_block = '\n'.join(corpus_lines) or '(no corpus rows for this company)'

    rounds_block = '\n'.join(f'- {p[:600]}' for p in (rounds_prose or [])) or \
        '(no published process description — infer a standard loop for this company)'

    prompt = f"""You are a career coach building a Company Prep Pack.
Company: {company_name}
Target role: {role}

PUBLISHED INTERVIEW PROCESS (verbatim excerpts, from the company's interview-prep page):
{rounds_block}

CORPUS OF QUESTIONS ACTUALLY ASKED AT THIS COMPANY (from LeetCode company-wise
frequency data and InterviewBit; the URL after each question is its source):
{corpus_block}

Produce a JSON object with EXACTLY these keys:
{{
  "rounds": [{{"name": "...", "focus": "...", "tips": "..."}}],
  "questions": [{{"question": "...", "why": "...", "category": "...",
                 "source": "corpus" | "synthesized", "source_url": "..."}}],
  "study_plan": [{{"week": "Week 1", "focus": "...", "actions": ["...", "..."]}}],
  "tips": ["..."]
}}

Rules:
- rounds: 3-5 entries derived from the published process; name each round
  (e.g. "OA", "DS/Algo Round 1", "HR/Bar Raiser") and what it focuses on.
- questions: EXACTLY 12 entries. At least 8 must come from the corpus above
  (copy the text verbatim; set "source":"corpus" and carry its source_url).
  Up to 4 may be behavioral/system-design questions typical for this company
  (set "source":"synthesized", "source_url":""), grounded in the published
  process when one exists.
- "why" = one sentence on why this question is likely for this company/role.
- study_plan: 4 weeks, actions must be concrete and time-boxed.
- tips: 4-6 short, company-specific interview tips.
- Return ONLY the JSON object, no markdown fences, no commentary.""" 

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.4,
            response_format={'type': 'json_object'},
        )
        raw = completion.choices[0].message.content
        pack = json.loads(raw)
        # Minimal shape validation so a malformed reply never gets cached.
        if not isinstance(pack.get('questions'), list) or not pack['questions']:
            return {}
        return pack
    except Exception as exc:
        print(f'prep_bot synthesis failed: {exc}')
        return {}
