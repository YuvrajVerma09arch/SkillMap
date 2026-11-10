import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const FEATURES = [
  { num: '01', icon: 'bi-file-earmark-text', title: 'Resume Analyst', text: 'GPT-OSS 120B scores your resume against job descriptions with semantic precision. Identify gaps, strengthen positioning.', link: '/resume-checker', cta: 'Run Analysis →' },
  { num: '02', icon: 'bi-diagram-3', title: 'Roadmap Generator', text: 'Personalized step-by-step learning paths built from your current skill set and target role requirements.', link: '/roadmap', cta: 'Generate Path →' },
  { num: '03', icon: 'bi-journal-check', title: 'Company Prep Pack', text: 'Company-specific prep: interview round structure, top asked questions with sources, a 4-week study plan and salary bands. Free.', link: '/prep', cta: 'Build Pack →' },
  { num: '04', icon: 'bi-briefcase', title: 'Job Matching', text: 'Semantic matching connects your profile to live opportunities. Apply with one click, track everything.', link: '/live-jobs', cta: 'Browse Jobs →' },
  { num: '05', icon: 'bi-people', title: 'Recruiter Connect', text: 'Direct recruiter-to-candidate matching. No keyword games — pure semantic alignment between profiles and roles.', link: '/role-select', cta: 'Connect →' },
  { num: '06', icon: 'bi-lightning-charge', title: 'Credit System', text: 'Transparent credit-based pricing via Razorpay. Pay only for what you use, upgrade when you need more.', link: '/pricing', cta: 'View Plans →' },
]

const STEPS = [
  { num: '01', title: 'Upload Resume', text: 'Drop your resume. AI parses skills, experience, and education in seconds.', icon: 'bi-upload' },
  { num: '02', title: 'AI Analysis', text: 'Deep semantic analysis against thousands of role requirements using GPT-OSS 120B.', icon: 'bi-cpu' },
  { num: '03', title: 'Get Roadmap', text: 'Receive a personalized path with skill gaps, resources, and milestones.', icon: 'bi-map' },
  { num: '04', title: 'Apply & Win', text: 'Connect with matched recruiters, prep with company packs, apply with confidence.', icon: 'bi-rocket-takeoff' },
]

export default function Home() {
  const { user } = useAuth()

  return (
    <div style={{ position: 'relative', overflow: 'hidden' }}>
      <section style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', position: 'relative', overflow: 'hidden', padding: '80px 24px 60px' }}>
        <div style={{ position: 'absolute', top: '50%', left: '60%', transform: 'translate(-50%,-50%)', pointerEvents: 'none', zIndex: 0 }}>
          <svg className="orbit-1" width="700" height="700" viewBox="0 0 700 700" fill="none" style={{ opacity: 0.07 }}>
            <circle cx="350" cy="350" r="340" stroke="white" strokeWidth="0.75" />
            <circle cx="350" cy="350" r="240" stroke="white" strokeWidth="0.5" />
            <ellipse cx="350" cy="350" rx="340" ry="120" stroke="white" strokeWidth="0.5" />
            <circle cx="350" cy="10" r="4" fill="white" opacity="0.6" />
            <circle cx="690" cy="350" r="3" fill="white" opacity="0.4" />
          </svg>
        </div>
        <div style={{ position: 'absolute', top: '50%', left: '60%', transform: 'translate(-50%,-50%)', pointerEvents: 'none', zIndex: 0 }}>
          <svg className="orbit-2" width="500" height="500" viewBox="0 0 500 500" fill="none" style={{ opacity: 0.05 }}>
            <ellipse cx="250" cy="250" rx="240" ry="80" stroke="#e63946" strokeWidth="0.75" />
            <circle cx="250" cy="10" r="3" fill="#e63946" opacity="0.8" />
          </svg>
        </div>

        <div className="scan-line"></div>

        <div className="max-w-screen-xl mx-auto w-full" style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ maxWidth: 680 }}>
            <div className="flex items-center gap-3 mb-8 animate-fade-up">
              <span className="animate-blink" style={{ color: 'var(--signal)', fontSize: 8 }}>●</span>
              <span className="label-signal">SYSTEM ONLINE · AI CAREER INTELLIGENCE</span>
            </div>

            <h1 className="display animate-fade-up" style={{ fontSize: 'clamp(42px,7vw,88px)', color: 'var(--chalk)', marginBottom: 24, animationDelay: '0.1s' }}>
              Map Your<br />
              <span style={{ color: 'var(--signal)' }}>Career</span><br />
              Trajectory
            </h1>

            <p className="animate-fade-up" style={{ fontSize: 16, color: 'var(--chalk-3)', maxWidth: 480, lineHeight: 1.7, marginBottom: 40, animationDelay: '0.2s' }}>
              SkillMap uses Groq's GPT-OSS 120B to analyze your resume, generate personalized roadmaps, and connect you with the right opportunities — with precision.
            </p>

            <div className="flex flex-wrap gap-3 animate-fade-up" style={{ animationDelay: '0.3s' }}>
              {!user ? (
                <>
                  <Link to="/role-select" className="btn-signal">Initialize System <span style={{ fontSize: 16, lineHeight: 1 }}>→</span></Link>
                  <Link to="/login" className="btn-ghost">Login</Link>
                </>
              ) : user.role === 'seeker' ? (
                <>
                  <Link to="/roadmap" className="btn-signal">View Roadmap <span style={{ fontSize: 16, lineHeight: 1 }}>→</span></Link>
                  <Link to="/resume-checker" className="btn-ghost">Resume Analyst</Link>
                </>
              ) : (
                <>
                  <Link to="/dashboard" className="btn-signal">Dashboard <span style={{ fontSize: 16, lineHeight: 1 }}>→</span></Link>
                  <Link to="/talent" className="btn-ghost">Talent Feed</Link>
                </>
              )}
            </div>

            <div className="flex flex-wrap gap-6 mt-12 animate-fade-up" style={{ animationDelay: '0.4s' }}>
              <div>
                <p className="label mb-1">Engine</p>
                <p style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12, color: 'var(--chalk-2)' }}>GPT-OSS 120B · Groq</p>
              </div>
              <div>
                <p className="label mb-1">Payments</p>
                <p style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12, color: 'var(--chalk-2)' }}>Razorpay</p>
              </div>
              <div>
                <p className="label mb-1">Interface</p>
                <p style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12, color: 'var(--chalk-2)' }}>Orbital v1.0</p>
              </div>
            </div>
          </div>
        </div>

        <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 1, background: 'var(--wire)' }}></div>
      </section>

      <section id="features" style={{ padding: '96px 24px', position: 'relative', zIndex: 1 }}>
        <div className="max-w-screen-xl mx-auto">
          <div className="section-label"><span className="label-signal">Core Modules</span></div>
          <h2 className="display" style={{ fontSize: 'clamp(28px,4vw,48px)', color: 'var(--chalk)', marginBottom: 56, maxWidth: 480 }}>
            Six tools. One system.
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px" style={{ background: 'var(--wire)' }}>
            {FEATURES.map((f) => (
              <div key={f.num} className="feat-card">
                <div className="label mb-4">MODULE · {f.num}</div>
                <div style={{ fontSize: 28, color: 'var(--chalk-2)', marginBottom: 16 }}><i className={`bi ${f.icon}`}></i></div>
                <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--chalk)', marginBottom: 10 }}>{f.title}</h3>
                <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.7, marginBottom: 20 }}>{f.text}</p>
                <Link to={f.link} style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: 'var(--signal)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>{f.cta}</Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ padding: '96px 24px', borderTop: '1px solid var(--wire)', borderBottom: '1px solid var(--wire)', position: 'relative', zIndex: 1 }}>
        <div className="max-w-screen-xl mx-auto">
          <div className="section-label"><span className="label-signal">Sequence</span></div>
          <h2 className="display" style={{ fontSize: 'clamp(28px,4vw,48px)', color: 'var(--chalk)', marginBottom: 64 }}>
            From resume to offer.
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8" style={{ position: 'relative' }}>
            {STEPS.map((s, i) => (
              <div key={s.num} style={{ position: 'relative' }}>
                {i < STEPS.length - 1 && <div className="step-connector"></div>}
                <div style={{ width: 40, height: 40, background: 'var(--ink)', border: '1px solid var(--wire-2)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
                  <i className={`bi ${s.icon}`} style={{ color: 'var(--signal)', fontSize: 16 }}></i>
                </div>
                <div className="label mb-2" style={{ color: 'var(--signal)' }}>STEP · {s.num}</div>
                <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--chalk)', marginBottom: 8 }}>{s.title}</h3>
                <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.7 }}>{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ padding: '96px 24px', position: 'relative', zIndex: 1, overflow: 'hidden' }}>
        <div style={{ position: 'absolute', right: -200, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', opacity: 0.06 }}>
          <svg width="600" height="600" viewBox="0 0 600 600" fill="none">
            <circle cx="300" cy="300" r="290" stroke="white" strokeWidth="0.75" />
            <ellipse cx="300" cy="300" rx="290" ry="100" stroke="#e63946" strokeWidth="0.75" />
            <circle cx="300" cy="10" r="5" fill="white" />
          </svg>
        </div>

        <div className="max-w-screen-xl mx-auto" style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ maxWidth: 600 }}>
            <div className="section-label"><span className="label-signal">Ready</span></div>
            <h2 className="display" style={{ fontSize: 'clamp(32px,5vw,64px)', color: 'var(--chalk)', marginBottom: 20 }}>
              Your career<br />starts here.
            </h2>
            <p style={{ fontSize: 15, color: 'var(--chalk-3)', lineHeight: 1.7, marginBottom: 36, maxWidth: 400 }}>
              No credit card required to get started. Explore the platform, then upgrade when you're ready.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link to="/role-select" className="btn-signal">Get Started Free →</Link>
              <Link to="/pricing" className="btn-ghost">View Pricing</Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
