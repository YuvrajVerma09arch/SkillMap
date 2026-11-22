# Security audit & hardening — 2026-11-22

Read-only threat-model + STRIDE review of the full stack (Flask blueprints,
utils, Jinja templates, React SPA, config, git history, dependencies), followed
by fixes for confirmed issues only. See the attempt ledger at the bottom.

## Trust boundaries mapped

HTTP request (routes, JSON/form bodies, path params), file upload, OAuth
callback, payment verify, third-party job-feed data, and **Groq/LLM output**
(cached prep packs). Assets: credentials, seeker PII (phone, resume), recruiter
work_email, credits/money movement.

## Confirmed & fixed

1. **HIGH — IDOR: wrong FK used to gate PII and resume downloads.**
   `Application.seeker_id` is a FK to `seeker_profiles.id`, but the two
   relationship helpers compared it to `users.id`. Because those are
   independent sequences, a recruiter with *any* legitimate application whose
   `seeker_profiles.id` collided with a victim's `users.id` could unlock that
   victim's phone number and download their resume; symmetrically a seeker
   could unlock an unrelated recruiter's `work_email`.
   - Fix: `app/main/routes.py` — compare `Application.seeker_id` against
     `seeker_user.seeker_profile.id` in both helpers, with a None guard.
   - Verified with an abuse-case test that forces the collision: victim blocked
     on both `/api/profiles/<id>` and `/api/files/resume/<file>` (403 / no PII),
     while genuine applicant relationships still work (200 / phone visible).

2. **MEDIUM — Missing role authorization on profile-save endpoints.**
   `POST /api/profile/seeker` and `POST /api/profile/recruiter` had only
   `@login_required`, so any user could create the other role's profile and
   pollute the authorization data. The SPA always routes by role, so guards
   don't break legitimate flows.
   - Fix: 403 when `current_user.role` doesn't match the endpoint.
   - Verified: cross-role saves 403, matching-role saves 200.

3. **MEDIUM — No baseline security headers.** Added an `after_request` handler
   (`app/__init__.py`) setting `X-Content-Type-Options: nosniff`,
   `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`,
   and `Permissions-Policy` on every response. Verified present.

4. **LOW — Unvalidated URL schemes in `href`.** React 18 only warns about
   `javascript:` URLs; user/feed/LLM-controlled values flowed into anchors.
   - Fix: `frontend/src/lib/safeHref.js` allowlists `http(s):`, rejects
     `javascript:`/`data:`/`vbscript:`/other schemes (incl. case/whitespace
     obfuscation), and upgrades schemeless domains to `https://` so legitimate
     legacy values keep working. Applied at all 4 untrusted sinks (CompanyProfile,
     LiveJobs, JobFeed, PrepResult); also upgraded `rel` to `noopener noreferrer`.
   - Verified with a 17-case unit run (all pass).

## Reviewed — no real issue found

SQL injection (all raw SQL uses bound params), command injection / `eval` /
`pickle`, SSRF (all server fetches use hardcoded base URLs + fixed feed map),
LLM output handling (JSON-parsed, never evaluated), XSS/templates (no
`dangerouslySetInnerHTML`, `|safe`, or `innerHTML`; Jinja templates are dead
code), secrets (none in source or git history), CORS (exact origin list, never
`*`), uploads (allowlist + magic bytes + size caps + UUID names + private dir),
auth coverage, password hashing (Werkzeug), generic error bodies, SPA path
containment, and payment signature verification (server-side HMAC — forging
success is not possible).

## Deferred — with reason & review condition

These are **not** exploitable as configured, or require approval/infra changes
(the skill's "Ask First" bucket). Do not re-run without a changed premise.

| Item | Why deferred | Revisit when |
|---|---|---|
| `npm audit`: Vite/esbuild + react-router (moderate/high) | Vite/esbuild are build-time only; react-router issue needs SSR or a user-controlled `<Link>` target (none — all static paths, and the one dynamic `navigate` uses a hardcoded server path). Fixes are **major-version** breaking upgrades. | App adopts SSR or user-controlled navigation; or a compatible patched minor exists |
| Python deps (Authlib/urllib3/requests/etc. advisories) | Mostly features unused here (Authlib is used as an OAuth **client**, not a server/JWS issuer); many are DoS or require crafted certs. Bulk upgrades risk breakage on a frozen stack. | A reachable advisory on an actually-used code path |
| Strict CSP | Would break the app: React inline `style=` is pervasive and `frontend/index.html` uses inline `onload=` handlers for async CSS; Razorpay `checkout.js` loads from an external origin. A correct CSP needs refactoring those first. | Inline handlers/styles are removed (nonce/hash-based) |
| Synchronizer CSRF token | Existing Origin check blocks browser cross-site writes; tokens change the auth flow (Ask First). | App gains non-browser clients or proxy Host trust changes |
| Shared (Redis) rate-limit store + explicit SECRET_KEY | Single-worker deploy documented; in-memory limits and the random per-process key are masked. Multi-worker is an infra change (Ask First). | Deploy scales past one worker |
| Cookie `Secure` default | Set via `COOKIE_SECURE=1` in production per README; true for cross-origin by default. Flipping the same-origin default is operational. | — |
| Payment idempotency atomicity / webhook | Replay check + last-write-wins prevents double crediting; HMAC verifies authenticity. Hardening, not exploitable. | Moving to a webhook-driven model |

## Guard

Three portable, self-contained regression tests live in `tests/`:

```
python3 tests/test_idor.py        # collision stays blocked, legit PII flows intact
python3 tests/test_hardening.py   # role guards + security headers
node tests/test_safe_href.mjs     # href scheme allowlist
```

Each spins up its own temp SQLite DB (no running server needed). Re-run them
after any change to `main/routes.py`, `app/__init__.py`, `app/models.py`, or
`frontend/src/lib/safeHref.js`.
