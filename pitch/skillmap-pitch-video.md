# SkillMap Pitch / Showcase Video — Shot List & Prompts

**Target length:** ~31s (VO = 30.0s, generated) — 7 clips, crossfaded
**Aspect ratios:** 16:9 for the website/Show HN/Product Hunt hero; re-crop to 9:16 for X/Instagram using ffmpeg (`-vf "crop=ih*9/16:ih"`).
**Where to generate (free, no card):**
1. **Google Flow** — 50 credits/day ≈ 5× Veo 3.1 Lite clips (10 cr each, 4/6/8s, 720p). Best quality free route. No video 2–5 PM UTC. *(primary)*
2. **Krea** — 100 compute units/day, **no watermark** on free. *(for clean overlay shots)*
3. **Dreamina** — 120 credits/day (US accounts). *(bulk drafts)*

> ⚠️ Free tiers: watermark likely (Flow = invisible SynthID; visible mark toggleable except in IN/KR/VN), commercial-use terms vary — check before paid promotion. Delete/keep clips within free-tier retention windows.

---

## Hybrid audio plan (approved)

| Layer | Source | Notes |
|---|---|---|
| **Voiceover** | edge-tts `en-US-AndrewNeural` @ `-4%` rate | `voiceover/vo-final.mp3` (30.0s), word timings in `voiceover/vo-words.json` (72 words) |
| **Ambience/SFX** | Flow clip native audio | Prompts below request ambience only — **"no speech, no dialogue"** in every prompt |
| **Music bed** | Royalty-free (Pixabay / YouTube Audio Library, CC0) | Auto-ducked under VO via ffmpeg `sidechaincompress` |
| **Captions** | ffmpeg ASS, animated, word-synced from `vo-words.json` | Never let AI render text |

**Why not Flow as narrator:** different random voice per clip, script paraphrase risk, no timing control, crossfade audio chopping, 10 cr per re-take. Flow's native speech is kept only as ambience.

---

## Scene timeline (locked to actual VO timestamps)

VO anchors (from `vo-words.json`): "gone" @3.45s · "keywords" @8.54s · "SkillMap" @8.97s · "graph" @16.34s · "proven" @17.04s · "next" @20.01s · "demand" @22.34s · "Recruiters" @22.77s · "SkillMap" @27.28s · end @29.65s

| # | Video time | Clip | VO beat |
|---|------|------|---------|
| 1 | 0.0–4.0s | s1 (4s) | Hook — "six seconds… then it's gone" |
| 2 | 4.0–9.0s | s2 (6s, trimmed) | Problem — "scan for keywords" |
| 3 | 9.0–17.0s | s3a (8s) | Product — "reads your real work → skill graph" |
| 4 | 17.0–20.0s | s4 (6s, trimmed) | "What you've proven. Where you're strong." |
| 5 | 20.0–22.7s | s3b (6s, trimmed) | "what to learn next → job demand" |
| 6 | 22.7–27.1s | s3c (6s, trimmed) | Proof — "ranked shortlists backed by evidence" |
| 7 | 27.1–31.5s | s5 (6s, trimmed) | CTA — "SkillMap. Stop guessing who's qualified." |

Crossfades: 0.5s `xfade` between each pair (overlap reduces total duration — offsets computed at assembly).

---

## Shot-by-shot prompts (paste-ready, audio cues included)

### Shot 1 — Hook (4s)
> Cinematic macro shot of a paper resume lying on a dark desk, a glowing cyan scanning light bar sweeping across it line by line, holographic score rings lighting up above the page, dark studio background with subtle violet neon rim light, slow push-in, premium tech commercial style, shallow depth of field, ambient sound: soft paper rustle and a low electronic scan hum, no speech, no dialogue, no text, no words, no letters

### Shot 2 — Problem (6s)
> Overhead shot of a messy desk covered with crumpled job-application papers, a laptop showing an out-of-focus inbox, a dim clock ticking, moody low-key lighting with cold blue tones, subtle slow camera drift, cinematic realism, ambient sound: quiet room tone with faint clock ticking and paper shuffling, no speech, no dialogue, no text, no words

### Shot 3a — Resume analysis (8s)
> A translucent holographic document floating above a sleek laptop, invisible hands typing, a circular gauge filling up from red to green, small data particles rising, dark background with cyan and magenta neon accents, smooth orbital camera movement, premium SaaS product commercial, ambient sound: gentle keyboard taps and a rising soft synth chime as the gauge fills, no speech, no dialogue, no text, no words, no letters

### Shot 3b — Roadmap / path (6s)
> A glowing pathway of connected nodes appearing one by one across a dark futuristic map, each node lighting up like a milestone, camera glides forward along the path, cyan and amber glow, depth of field, abstract tech visualization, ambient sound: soft node activation pings and a low airy drone, no speech, no dialogue, no text, no words, no labels

### Shot 3c — Recruiter / jobs (6s)
> Split-screen style shot: on one side a confident professional smiling at a laptop, on the other side abstract floating profile cards connecting with glowing lines, bright modern office bokeh background, warm natural light mixed with subtle blue tech glow, slow dolly, ambient sound: light office murmur and subtle data connection whooshes, no speech, no dialogue, no text, no words

### Shot 4 — Proof (6s)
> Time-lapse style shot of a person's silhouette standing before a large transparent screen where progress bars and circular charts fill rapidly, particles of light, dark room with cyan glow, epic reveal camera pull-back, cinematic tech, ambient sound: deep cinematic swell with rapid soft counter ticks, no speech, no dialogue, no text, no numbers, no words

### Shot 5 — CTA (6s)
> Minimal dark scene, a single glowing cyan orb of light expanding into a soft radial gradient, gentle floating particles, elegant slow motion, plenty of empty space in the center for a title, premium end-card background, ambient sound: warm resolving synth chord fading in, no speech, no dialogue, no text, no words

---

## Text overlays (added in ffmpeg/assembly — do NOT ask AI to render text)

AI video models garble text. I add these myself during assembly:

1. **0.2–3.8s:** `Your resume is being rejected. Silently.`
2. **4.2–8.8s:** `Most resumes never reach a human.`
3. **9.2–16.8s:** `SkillMap — reads your real work`
4. **17.2–22.5s:** `Verified skill graph · What to learn next`
5. **22.9–26.9s:** `Ranked shortlists, backed by evidence`
6. **27.3–31.3s:** `skillmap — stop guessing who's qualified`

**Font style:** Inter/SF Semibold, white with subtle drop shadow, 600 weight, 0.8s ease-in/out on every caption.

Plus **word-synced caption stream** (bottom center, small) driven by `vo-words.json` — words highlight as Andrew speaks.

---

## Assembly (once clips are downloaded)

```bash
# 1. Normalize + xfade chain (0.5s crossfades), timings per scene table above
# 2. VO in: vo-final.mp3
# 3. Music bed: sidechaincompress keyed by VO (VO ducks music ~-12dB)
# 4. Clip native audio → amix at low level (-18dB) as ambience layer
# 5. ASS captions: scene overlays + word-synced stream from vo-words.json
# 6. loudnorm to -14 LUFS, export 16:9 + 9:16 crop
```

I'll run the crossfades, music ducking, captions, and 9:16 crop for you once the raw clips land in `pitch/clips/`.

---

## Also worth shooting (free)

- **Screen recording of the real product** (localhost:5001 or live URL) for the "product in action" beat — more convincing than AI B-roll. 3 short recordings: upload → score, roadmap generation, recruiter view.
- **Poster/thumbnail:** one still frame + title for PH/Show HN.
