# Performance pass — 2026-11-21

Measure-first pass on the homepage. Baseline → final **Lighthouse mobile performance
score 72 → 90**; FCP 4.51 → 2.16 s, LCP 4.74 → 3.36 s, CLS 0.002 → 0.001,
TBT ~0 → 34 ms. Core Web Vitals are in the "Good" band (LCP ≤ 2.5 s is the next
target; FCP/LCP here are under Lighthouse's simulated 4G, not field data).

## Method

Local production build served by Flask (`DATABASE_URL=sqlite:///... PORT=5001
python3 run.py`), rebuilt after each single change. Each run:

```
CHROME_PATH=…/chromium-1148/.../Chromium \
npx lighthouse http://127.0.0.1:5001/ \
  --only-categories=performance --form-factor=mobile \
  --screenEmulation.mobile --throttling-method=simulate \
  --output=json --output-path=/tmp/lh_<run>.json
```

Same URL, flags, and throttle profile every time. Functional regression check
after each change: Playwright smoke over 6 routes with 0 console/page errors,
plus `frontend/scripts/subset-icons.py` verification (cmap coverage + canvas
glyph paint for all 52 used icons).

## Attempt ledger

| # | Change | Score | FCP | LCP | Verdict |
|---|--------|-------|-----|-----|---------|
| 0 | baseline | 72 | 4.51 s | 4.74 s | — |
| 1 | self-host bootstrap-icons 1.11.3 (was jsdelivr CDN) | 70 | 4.70 s | 4.85 s | kept — score-neutral, removes a third-party render-blocking hop |
| 2 | load Google Fonts + icons CSS non-blocking (`media="print" onload`) | 74 | 3.65 s | 4.86 s | kept — FCP −1.05 s, blocking CSS now only the local bundle |
| 3 | route-level code splitting (18 pages `React.lazy`, `Home` eager) | 78 | 3.16 s | 4.44 s | kept — main bundle 288.68 → 192.00 kB (gzip 81.31 → 61.10), unused JS 153 → 60 KB |
| 4 | pitch poster JPG → WebP (`cwebp -q 82`) | 79 | 3.16 s | 4.36 s | kept — 154 → 96.8 kB, total weight 653 → 594 KiB |
| 5 | subset bootstrap-icons to the 52 glyphs actually used | **90** | 2.16 s | 3.36 s | kept — CSS 85.9 → 2.7 kB, woff2 130 → 5.5 kB; LCP render delay 3908 → 459 ms |
| — | gzip/brotli in Flask | — | — | — | skipped — Lighthouse "text compression" was a local-server artifact; production already serves `content-encoding: br` at Render's edge |
| — | async Vite layout CSS | — | — | — | skipped — would cause FOUC on the LCP text; not worth the visual regression |
| — | trim "unused CSS" 27 KB | — | — | — | skipped — SPA coverage false positive (classes belong to lazy routes); only 847 bytes are truly dead |
| — | trim "unused JS" 60 KB | — | — | — | skipped — react-dom core is 129 kB of the 192 kB bundle; not droppable |

Run-to-run variance on TBT was 11–34 ms — both are effectively zero and do not
change the score. The 72 → 90 gain is far outside that noise.

## Regenerating the icon subset

After adding/removing a `bi-*` class in `frontend/src`, run:

```
python3 frontend/scripts/subset-icons.py
cd frontend && npm run build
python3 /tmp/verify_icons.py   # optional: cmap + canvas glyph verification
```

The script is idempotent and fails loudly if a used class has no upstream rule.
It strips leading licence comments before classifying rules — upstream attaches
its banner to the `@font-face` selector, which otherwise leaves a stale
duplicate `@font-face` in the output.

The master video and poster source live in the gitignored local `pitch/` dir;
the WebP in `app/static/media/` is regenerable from the master with `cwebp`.
