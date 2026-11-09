import { Link } from 'react-router-dom'
import { useSearchParams } from 'react-router-dom'

const SEEKER_MODULES = ['Resume Analyst', 'Roadmap Generator', 'Company Prep Pack', 'Job Matching']
const RECRUITER_MODULES = ['Post Jobs', 'Talent Feed', 'Applicant Tracker', 'Resume Analysis']

function RoleCard({ num, role, icon, title, text, modules }) {
  return (
    <Link to={`/register?role=${role}`} className="role-card">
      <div className="label" style={{ marginBottom: 32, color: 'var(--signal)' }}>ROLE · {num}</div>
      <div style={{ width: 56, height: 56, background: 'var(--ink)', border: '1px solid var(--wire-2)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 28 }}>
        <i className={`bi ${icon}`} style={{ fontSize: 24, color: 'var(--chalk-2)' }}></i>
      </div>
      <h2 className="display" style={{ fontSize: 28, color: 'var(--chalk)', marginBottom: 12 }}>{title}</h2>
      <p style={{ fontSize: 14, color: 'var(--chalk-3)', lineHeight: 1.7, marginBottom: 32, flex: 1 }}>{text}</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 36 }}>
        {modules.map((m) => (
          <div key={m} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ width: 4, height: 4, background: 'var(--signal)', borderRadius: '50%', display: 'inline-block', flexShrink: 0 }}></span>
            <span style={{ fontSize: 13, color: 'var(--chalk-2)', fontFamily: "'JetBrains Mono',monospace" }}>{m}</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: 'var(--signal)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
        Select {title} <span style={{ fontSize: 14 }}>→</span>
      </div>
    </Link>
  )
}

export default function RoleSelect() {
  const [params] = useSearchParams()
  const isOauth = params.get('oauth') === '1'

  return (
    <div style={{ minHeight: 'calc(100vh - 56px)', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '60px 24px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', right: -150, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', opacity: 0.05 }}>
        <svg className="orbit-spin" width="500" height="500" viewBox="0 0 500 500" fill="none">
          <circle cx="250" cy="250" r="245" stroke="white" strokeWidth="0.75" />
          <ellipse cx="250" cy="250" rx="245" ry="88" stroke="white" strokeWidth="0.5" />
          <circle cx="250" cy="5" r="4" fill="white" />
          <circle cx="495" cy="250" r="3" fill="white" />
        </svg>
      </div>

      <div className="max-w-screen-lg mx-auto w-full" style={{ position: 'relative', zIndex: 1 }}>
        <div className="animate-fade-up" style={{ textAlign: 'center', marginBottom: 64 }}>
          <div className="label-signal" style={{ marginBottom: 12, display: 'block', textAlign: 'center' }}>System Initialization</div>
          <h1 className="display" style={{ fontSize: 'clamp(32px,5vw,56px)', color: 'var(--chalk)', marginBottom: 16 }}>
            Select Your Role
          </h1>
          <p style={{ fontSize: 15, color: 'var(--chalk-3)', maxWidth: 400, margin: '0 auto', lineHeight: 1.7 }}>
            Your role determines which modules and tools are activated in your dashboard.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-up" style={{ animationDelay: '0.15s' }}>
          <RoleCard
            num="01"
            role="seeker"
            icon="bi-person-lines-fill"
            title="Job Seeker"
            text="Access AI resume analysis, personalized career roadmaps, company-specific prep packs, and live job matching."
            modules={SEEKER_MODULES}
          />
          <RoleCard
            num="02"
            role="recruiter"
            icon="bi-buildings"
            title="Recruiter"
            text="Post jobs, browse a talent feed of AI-matched candidates, review applications, and manage your hiring pipeline."
            modules={RECRUITER_MODULES}
          />
        </div>

        <p className="animate-fade-up" style={{ textAlign: 'center', marginTop: 40, fontSize: 14, color: 'var(--chalk-3)', animationDelay: '0.25s' }}>
          Already have an account?
          <Link to="/login" style={{ color: 'var(--signal)', textDecoration: 'none', marginLeft: 4 }}>Sign in →</Link>
        </p>
      </div>
    </div>
  )
}
