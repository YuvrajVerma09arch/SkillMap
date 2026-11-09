import { useState } from 'react'
import { NavLink, Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function LogoMark({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="14" cy="14" r="13" stroke="#e63946" strokeWidth="1" />
      <circle cx="14" cy="14" r="3" fill="#e63946" />
      <ellipse cx="14" cy="14" rx="13" ry="5" stroke="rgba(255,255,255,0.2)" strokeWidth="0.75" />
      <line x1="14" y1="1" x2="14" y2="27" stroke="rgba(255,255,255,0.1)" strokeWidth="0.75" />
    </svg>
  )
}

const SEEKER_LINKS = [
  { to: '/resume-checker', label: 'Resume' },
  { to: '/roadmap', label: 'Roadmap' },
  { to: '/prep', label: 'Prep' },
  { to: '/jobs', label: 'Jobs' },
]

const RECRUITER_LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/talent', label: 'Talent' },
  { to: '/resume-checker', label: 'Analysis' },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const links = user
    ? user.role === 'seeker'
      ? SEEKER_LINKS
      : RECRUITER_LINKS
    : []

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <>
      <nav className="nav-root">
        <div className="max-w-screen-xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3 group">
            <LogoMark />
            <span style={{ fontFamily: "'Space Grotesk',sans-serif", fontWeight: 700, fontSize: 16, letterSpacing: '-0.02em', color: '#f0f0f0' }}>
              SKILL<span style={{ color: '#e63946' }}>MAP</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <NavLink to="/" end className="nav-link">Home</NavLink>
            {links.map((l) => (
              <NavLink key={l.to} to={l.to} className="nav-link">{l.label}</NavLink>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-4">
            {user ? (
              <>
                <Link
                  to="/pricing"
                  className="flex items-center gap-1.5 label-signal border border-signal/30 px-3 py-1.5 hover:bg-signal/10 transition-colors"
                >
                  <i className="bi bi-lightning-charge-fill" style={{ fontSize: 10 }}></i>
                  CREDITS: {user.credits}
                </Link>
                <div className="relative group">
                  <button className="flex items-center gap-2 btn-ghost" style={{ padding: '7px 14px' }}>
                    <div className="w-6 h-6 flex items-center justify-center" style={{ background: 'var(--signal)', fontSize: 11, fontWeight: 700, fontFamily: "'JetBrains Mono',monospace" }}>
                      {user.name?.[0]?.toUpperCase()}
                    </div>
                    <span className="label" style={{ color: 'var(--chalk-2)', textTransform: 'none', letterSpacing: 0, fontSize: 13 }}>
                      {user.name}
                    </span>
                    <i className="bi bi-chevron-down" style={{ fontSize: 9, color: 'var(--chalk-3)' }}></i>
                  </button>
                  <div className="absolute right-0 mt-1 w-44 py-1 hidden group-hover:block" style={{ background: 'var(--ink-2)', border: '1px solid var(--wire-2)', zIndex: 200 }}>
                    <Link
                      to={user.role === 'recruiter' ? '/company' : '/profile'}
                      className="block px-4 py-2.5 label hover:bg-white/5"
                      style={{ textTransform: 'none', letterSpacing: 0, fontSize: 12, color: 'var(--chalk-2)' }}
                    >
                      {user.role === 'recruiter' ? 'Company Profile' : 'My Profile'}
                    </Link>
                    <div className="divider my-1"></div>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2.5 label"
                      style={{ textTransform: 'none', letterSpacing: 0, fontSize: 12, color: 'var(--signal)', background: 'none', border: 'none', cursor: 'pointer' }}
                    >
                      Sign out
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <>
                <NavLink to="/login" className="nav-link" style={{ padding: '6px 0' }}>Login</NavLink>
                <Link to="/role-select" className="btn-signal" style={{ padding: '8px 20px', fontSize: 12 }}>Get Started →</Link>
              </>
            )}
          </div>

          <button
            className="md:hidden"
            style={{ color: 'var(--chalk-2)', background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}
            onClick={() => setMobileOpen((o) => !o)}
          >
            <i className="bi bi-list" style={{ fontSize: 22 }}></i>
          </button>
        </div>

        {mobileOpen && (
          <div className="md:hidden" style={{ background: 'var(--ink-2)', borderTop: '1px solid var(--wire)', padding: '16px 24px' }}>
            <div className="flex flex-col gap-4">
              <NavLink to="/" end className="nav-link" onClick={() => setMobileOpen(false)}>Home</NavLink>
              {user ? (
                <>
                  {links.map((l) => (
                    <NavLink key={l.to} to={l.to} className="nav-link" onClick={() => setMobileOpen(false)}>{l.label}</NavLink>
                  ))}
                  <NavLink to={user.role === 'recruiter' ? '/company' : '/profile'} className="nav-link" onClick={() => setMobileOpen(false)}>
                    {user.role === 'recruiter' ? 'Company Profile' : 'My Profile'}
                  </NavLink>
                  <button className="nav-link" style={{ color: 'var(--signal)', background: 'none', border: 'none', textAlign: 'left', padding: 0 }} onClick={handleLogout}>
                    Sign out
                  </button>
                </>
              ) : (
                <>
                  <NavLink to="/login" className="nav-link" onClick={() => setMobileOpen(false)}>Login</NavLink>
                  <NavLink to="/role-select" className="nav-link" style={{ color: 'var(--signal)' }} onClick={() => setMobileOpen(false)}>Get Started</NavLink>
                </>
              )}
            </div>
          </div>
        )}
      </nav>

      <main style={{ paddingTop: 56, minHeight: '100vh', position: 'relative', zIndex: 1 }}>
        <Outlet />
      </main>

      <footer style={{ background: 'var(--ink-2)', borderTop: '1px solid var(--wire)', position: 'relative', zIndex: 1 }}>
        <div className="max-w-screen-xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-10">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <LogoMark size={22} />
                <span style={{ fontFamily: "'Space Grotesk',sans-serif", fontWeight: 700, fontSize: 14, letterSpacing: '-0.01em' }}>
                  SKILL<span style={{ color: '#e63946' }}>MAP</span>
                </span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.7, maxWidth: 280 }}>
                AI-powered career intelligence system. Analyze, map, and accelerate your professional trajectory.
              </p>
              <div className="flex gap-3 mt-5">
                <a href="#" className="btn-ghost" style={{ padding: '7px 10px', fontSize: 13 }}><i className="bi bi-twitter-x"></i></a>
                <a href="#" className="btn-ghost" style={{ padding: '7px 10px', fontSize: 13 }}><i className="bi bi-linkedin"></i></a>
                <a href="#" className="btn-ghost" style={{ padding: '7px 10px', fontSize: 13 }}><i className="bi bi-github"></i></a>
              </div>
            </div>
            <div>
              <p className="label mb-4">System</p>
              <div className="flex flex-col gap-2.5">
                <Link to="/" style={{ fontSize: 13, color: 'var(--chalk-3)' }} className="hover:text-chalk transition-colors">Home</Link>
                <Link to="/pricing" style={{ fontSize: 13, color: 'var(--chalk-3)' }} className="hover:text-chalk transition-colors">Pricing</Link>
                <Link to="/legal" style={{ fontSize: 13, color: 'var(--chalk-3)' }} className="hover:text-chalk transition-colors">Legal</Link>
              </div>
            </div>
            <div>
              <p className="label mb-4">Status</p>
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center gap-2">
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }}></span>
                  <span style={{ fontSize: 12, color: 'var(--chalk-3)', fontFamily: "'JetBrains Mono',monospace" }}>All systems operational</span>
                </div>
                <span style={{ fontSize: 11, color: 'var(--chalk-3)', fontFamily: "'JetBrains Mono',monospace" }}>Powered by Groq · Llama 3</span>
                <span style={{ fontSize: 11, color: 'var(--chalk-3)', fontFamily: "'JetBrains Mono',monospace" }}>Payments via Razorpay</span>
              </div>
            </div>
          </div>
          <div className="divider"></div>
          <div className="flex flex-col md:flex-row items-center justify-between gap-3 mt-6">
            <span className="label">© 2025 SkillMap AI. All rights reserved.</span>
            <span className="label">BUILD · 2025.1 · ORBITAL-INTERFACE</span>
          </div>
        </div>
      </footer>
    </>
  )
}
