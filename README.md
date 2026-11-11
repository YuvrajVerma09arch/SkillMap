# SkillMap AI 🚀

SkillMap is an AI-powered career accelerator that connects job seekers with recruiters using semantic matching, not just keyword search — with resume analysis, interview prep, and career roadmaps powered by **GPT-OSS 120B**.

**Live:** https://skillmap-api-4eth.onrender.com

## 🌟 Key Features

### For Job Seekers
* **AI Resume Checker:** Upload a PDF resume and get an instant AI score + improvement feedback. Costs **5 credits** per analysis (charged atomically before the AI call, fully refunded if the analysis fails).
* **Career Roadmap Generator:** Get a personalized learning path from your current skills to a target role. Costs **1 credit**.
* **Interview Prep Packs (free):** Search any company and generate a prep pack with interview rounds and common questions — or use role-only packs when you don't have a company in mind. Cached per company + role.
* **Job Board & One-Click Apply:** Browse posted jobs, apply in one click, and track application status.
* **Live Job Aggregator:** Curated external feeds — India, remote, tech, USA, Europe, government, and RSS (Hacker News, We Work Remotely, Python jobs).
* **Talent Feed:** Semantic skill-based matching so the right recruiters find you.

### For Recruiters
* **Post jobs & review applicants:** Full applicant pipeline with status updates (applied → shortlisted → rejected).
* **Recruiter Dashboard:** Active jobs, applicant counts, and totals at a glance.
* **Discover talent:** Browse seeker profiles; contact details (phone, resume) are revealed **only after the seeker has applied** to your job — privacy by default.

### Platform
* **Credits & pricing:** Every new account starts with **5 free credits**; top up via Razorpay (starter plan included).
* **Authentication:** Email/password with Google OAuth sign-in; seeker/recruiter role selection at signup.
* **Role-only prep:** Interview prep works even before you pick a company.

## 🛡️ Security

The app passed a full red-team + white-box pentest and all findings were remediated:

* **Access-controlled uploads:** resumes and profile pics are served through authenticated, owner-checked API routes (`/api/files/...`) — never as public static files; path traversal blocked.
* **Atomic credit ledger:** `deduct_credits` / `refund_credits` are conditional DB UPDATEs — race-safe, balances can never go negative; charge-before-LLM with automatic refund on failure.
* **Anti-enumeration auth:** registration returns byte-identical responses for new and existing emails; login timing is equalized against hash-comparison leaks.
* **Output escaping:** all AI-derived content is HTML-escaped (and CR/LF-stripped from email subjects) before rendering — XSS and header-injection safe.
* **PII gating:** phone numbers, resumes, and recruiter work emails are only visible to the owner, or to a recruiter/seeker once there is an application linking them.
* **Rate limiting:** Flask-Limiter on auth (10/min/IP), resume analysis (6/min), prep generation (6/min), and company search (30/min).

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.13, Flask 3, SQLAlchemy, Flask-Migrate, Flask-Limiter, Gunicorn |
| **Frontend** | React 19 + Vite (SPA, served same-origin by Flask) |
| **Database** | PostgreSQL (Neon) |
| **AI Engine** | Groq API — **GPT-OSS 120B** |
| **Payments** | Razorpay |
| **Email** | Brevo API (SMTP fallback) |
| **Auth** | Email/password + Google OAuth (Authlib) |
| **Deployment** | Render (single origin) behind Cloudflare; UptimeRobot monitoring |

## 📦 Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/skillmap.git
   cd skillmap
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install & build the frontend:**
   ```bash
   cd frontend
   npm install
   npm run build      # production build served by Flask
   npm run dev        # or: dev server with hot reload (proxies to :5000)
   cd ..
   ```

4. **Configure `.env`:**
   ```
   SECRET_KEY=your_secret
   DATABASE_URL=postgresql://user:pass@host/db
   GROQ_API_KEY=your_groq_key
   RAZORPAY_KEY_ID=your_key
   RAZORPAY_KEY_SECRET=your_secret
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_secret
   GOOGLE_REDIRECT_URI=http://localhost:5000/google/callback
   FRONTEND_URL=http://localhost:5000
   COOKIE_SECURE=0            # set to 1 in production (HTTPS)
   BREVO_API_KEY=your_key     # or MAIL_USERNAME / MAIL_PASSWORD for SMTP
   ```

5. **Run the application:**
   ```bash
   python run.py              # http://localhost:5000  (set PORT to change)
   ```
   > macOS note: port 5000 is often taken by AirPlay — use `PORT=5001 python run.py` if the bind fails.

## ☁️ Deployment (Render)

* **Build command:**
  ```bash
  pip install -r requirements.txt && cd frontend && npm install && npm run build
  ```
* **Start command:**
  ```bash
  gunicorn run:app --bind 0.0.0.0:$PORT
  ```
* **Environment:** everything in step 4 above, plus `COOKIE_SECURE=1` and `PYTHON_VERSION=3.13.0`.
* **Monitoring:** UptimeRobot sends HEAD requests to `/api/health`.

## 📁 Project Structure

```
app/
├── __init__.py        # App factory, CORS, OAuth, rate limiter
├── models.py          # User, profiles, jobs, applications, transactions
├── auth/              # Register, login, Google OAuth
├── jobs/              # Job board, applications, live job feeds
├── main/              # Profiles, resume checker, roadmaps, prep packs, files
├── payments/          # Plans, Razorpay create/verify
└── utils/             # AI wrappers (resume, roadmap), email service
frontend/              # React 19 + Vite SPA
reports/               # Pentest findings & security reports
```

## 💰 Pricing

| Feature | Cost |
|---|---|
| New account credits | **5 free** |
| AI Resume Analysis | 5 credits |
| Career Roadmap | 1 credit |
| Interview Prep Packs | Free |
| Job posting / applying | Free |

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.

---

Built with ❤️ by Team SkillMap
