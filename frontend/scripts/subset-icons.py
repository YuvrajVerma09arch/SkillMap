"""Subset bootstrap-icons to only the glyphs the React app actually uses.

Keeps: @font-face, every rule without a `content:` declaration (base/utility
rules), and every icon class that appears in frontend/src.
Drops: glyph rules for icons the app never renders (all ~2000 -> ~50).
Verifies: every used class resolves to a codepoint present in the subset.

Run:  python3 frontend/scripts/subset-icons.py   (needs `fonttools brotli`)
"""
import glob
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSS_IN = f"{ROOT}/frontend/public/vendor/bootstrap-icons/bootstrap-icons.min.css"
FONT_WOFF2 = f"{ROOT}/frontend/public/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2"
FONT_WOFF = f"{ROOT}/frontend/public/vendor/bootstrap-icons/fonts/bootstrap-icons.woff"

# 1. Icons referenced anywhere in app source (literal strings, incl. data tables)
used = set()
for path in glob.glob(f"{ROOT}/frontend/src/**/*.js*", recursive=True):
    with open(path) as fh:
        used.update(re.findall(r"\bbi-[a-z0-9-]+", fh.read()))

# 2. Parse flat `selector{declarations}` pairs (this file has no nested @media).
# Strip leading `/* ... */` licence banners: upstream attaches them to the
# @font-face selector, which otherwise defeats the @font-face check below and
# leaves a stale duplicate rule in the output.
css = open(CSS_IN).read()
rules = []
for chunk in css.split("}"):
    chunk = chunk.strip()
    if not chunk or "{" not in chunk:
        continue
    sel, decl = chunk.split("{", 1)
    sel = re.sub(r"^\s*/\*.*?\*/\s*", "", sel, flags=re.S).strip()
    rules.append((sel, decl))

content_re = re.compile(r'content:\s*"\\([0-9a-fA-F]{2,6})"')
class_re = re.compile(r"\.([A-Za-z0-9_-]+)")

kept, codepoints, dropped, unresolved = [], set(), [], set()
for sel, decl in rules:
    if sel.startswith("@font-face"):
        kept.append((sel, decl))
        continue
    m = content_re.search(decl)
    if not m:
        kept.append((sel, decl))            # base/utility rules cost nothing
        continue
    classes = {c for c in class_re.findall(sel) if c.startswith("bi-")}
    if classes and classes <= used:
        codepoints.add(int(m.group(1), 16))
        kept.append((sel, decl))
    else:
        dropped.append(sel)

kept_selectors = " ".join(s for s, _ in kept)
unresolved = {c for c in used if f".{c}" not in kept_selectors}

print(f"used classes: {len(used)} | kept rules: {len(kept)} | "
      f"dropped rules: {len(dropped)} | codepoints: {len(codepoints)}")
if unresolved:
    print(f"!! used but no rule in subset: {sorted(unresolved)}")
    sys.exit(1)

# 3. Subset both font files down to those codepoints (+ ASCII space)
unicodes = ",".join(f"U+{cp:04X}" for cp in sorted(codepoints | {0x20}))
for path in (FONT_WOFF2, FONT_WOFF):
    subprocess.run(
        ["pyftsubset", path, f"--unicodes={unicodes}",
         f"--flavor={path.rsplit('.', 1)[1]}", "--layout-features=kern,liga,clig,calt",
         "--hinting", f"--output-file={path}.tmp"],
        check=True)
    subprocess.run(["mv", f"{path}.tmp", path], check=True)

# 4. Rebuild CSS: fresh cache-busting hash, upstream attribution kept
body = "".join(f"{s}{{{d}}}" for s, d in kept if not s.startswith("@font-face"))
hash16 = hashlib.sha256(unicodes.encode()).hexdigest()[:16]
face = (f'@font-face{{font-display:block;font-family:bootstrap-icons;'
        f'src:url("fonts/bootstrap-icons.woff2?{hash16}") format("woff2"),'
        f'url("fonts/bootstrap-icons.woff?{hash16}") format("woff")}}')
banner = ("/*! Bootstrap Icons v1.11.3 — subset to the glyphs SkillMap renders "
          "via frontend/scripts/subset-icons.py. MIT, "
          "Copyright The Bootstrap Authors, https://icons.getbootstrap.com/ */")
open(CSS_IN, "w").write(banner + face + body + "\n")
print(f"css: {len(css)} -> {len(banner + face + body)} bytes | hash={hash16}")
