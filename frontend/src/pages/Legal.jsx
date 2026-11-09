import { Link } from 'react-router-dom'

const SECTIONS = [
  {
    h: '1. Acceptance of Terms',
    p: ['By accessing or using SkillMap ("the Service"), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.'],
  },
  {
    h: '2. Description of Service',
    p: ['SkillMap provides AI-powered career tools including resume analysis, roadmap generation, company prep packs, and job matching. Features are accessed via a credit-based system.'],
  },
  {
    h: '3. Credits & Payments',
    p: ['Credits are purchased via Razorpay and consumed per AI operation. All payments are final. Credits do not expire and are non-transferable.'],
    li: ['1 credit per resume analysis', '1 credit per roadmap generation', 'Company Prep Packs are free to use'],
  },
  {
    h: '4. User Responsibilities',
    p: ['You are responsible for maintaining the confidentiality of your account credentials. You agree not to misuse the Service or attempt to reverse-engineer any AI components.'],
  },
  {
    h: '5. Privacy Policy',
    p: [
      'We collect only the data necessary to provide the Service: your email, name, resume content (for analysis), and usage logs. We do not sell your data to third parties.',
      "Resume content is processed by Groq's Llama 3 API and is not stored beyond the session unless you explicitly save a result.",
    ],
  },
  {
    h: '6. Intellectual Property',
    p: ['All AI-generated content (roadmaps, prep packs, resume scores) is provided for personal use. SkillMap retains no ownership over your resume or personal data.'],
  },
  {
    h: '7. Limitation of Liability',
    p: ['SkillMap is provided "as is." We do not guarantee employment outcomes or the accuracy of AI-generated career advice. Use the Service as one of many tools in your career strategy.'],
  },
  {
    h: '8. Contact',
    p: ["For questions regarding these terms, contact us via the platform's support channel."],
  },
]

export default function Legal() {
  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '80px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ marginBottom: 56 }}>
        <div className="section-label"><span className="label-signal">Legal</span></div>
        <h1 className="display" style={{ fontSize: 'clamp(28px,4vw,48px)', color: 'var(--chalk)', marginBottom: 12 }}>
          Terms &amp; Privacy
        </h1>
        <p style={{ fontSize: 13, color: 'var(--chalk-3)', fontFamily: "'JetBrains Mono',monospace" }}>
          Last updated: 2025 · SkillMap AI
        </p>
      </div>

      <div className="animate-fade-up" style={{ animationDelay: '0.1s' }}>
        {SECTIONS.map((s) => (
          <div key={s.h} className="legal-section">
            <h2 className="legal-h2">{s.h}</h2>
            {s.p.map((para, i) => (
              <p key={i} className="legal-p">{para}</p>
            ))}
            {s.li && (
              <ul style={{ listStyle: 'none', padding: 0, marginTop: 12 }}>
                {s.li.map((item) => (
                  <li key={item} className="legal-li">{item}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>

      <div style={{ marginTop: 48 }}>
        <Link to="/" className="btn-ghost" style={{ display: 'inline-flex' }}>← Back to Home</Link>
      </div>
    </div>
  )
}
