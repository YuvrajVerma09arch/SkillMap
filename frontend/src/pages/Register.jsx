import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { get, apiUrl } from '../lib/api'

export default function Register() {
  const { register, user, setUser } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const role = params.get('role')

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) navigate('/', { replace: true })
  }, [user, navigate])

  useEffect(() => {
    get('/api/auth/oauth-prefill').then((d) => {
      if (d.email) {
        setEmail(d.email)
        setName(d.name || '')
      }
    }).catch(() => {})
  }, [])

  if (role !== 'seeker' && role !== 'recruiter') {
    return (
      <div style={{ minHeight: '60vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16, padding: 24 }}>
        <span className="label-signal">SYSTEM INITIALIZATION</span>
        <h1 className="display" style={{ fontSize: 32, color: 'var(--chalk)' }}>Select a role first</h1>
        <Link to="/role-select" className="btn-signal">Choose Role →</Link>
      </div>
    )
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const u = await register({ username: name, email, password, role })
      navigate('/setup-profile', { replace: true })
      return u
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: 'calc(100vh - 56px)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px 24px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', right: -150, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', opacity: 0.05 }}>
        <svg className="orbit-spin" width="500" height="500" viewBox="0 0 500 500" fill="none">
          <circle cx="250" cy="250" r="245" stroke="white" strokeWidth="0.75" />
          <ellipse cx="250" cy="250" rx="245" ry="88" stroke="white" strokeWidth="0.5" />
          <circle cx="250" cy="5" r="4" fill="white" />
        </svg>
      </div>

      <div className="animate-fade-up" style={{ width: '100%', maxWidth: 440, position: 'relative', zIndex: 1 }}>
        <div className="label-signal" style={{ marginBottom: 12 }}>
          System Initialization · {role === 'seeker' ? 'Job Seeker' : 'Recruiter'}
        </div>
        <h1 className="display" style={{ fontSize: 36, color: 'var(--chalk)', marginBottom: 8 }}>Create Account</h1>
        <p style={{ fontSize: 14, color: 'var(--chalk-3)', marginBottom: 32 }}>
          Already registered?
          <Link to="/login" style={{ color: 'var(--signal)', textDecoration: 'none', marginLeft: 4 }}>Sign in →</Link>
        </p>

        {error && (
          <div className="flash-msg" style={{ marginBottom: 20 }}>
            <p style={{ fontSize: 13, color: 'var(--chalk)' }}>{error}</p>
          </div>
        )}

        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div>
            <label className="label" style={{ display: 'block', marginBottom: 8 }}>Full Name</label>
            <input type="text" required placeholder="Jane Doe" className="input-field" autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label className="label" style={{ display: 'block', marginBottom: 8 }}>Email Address</label>
            <input type="email" required placeholder="you@example.com" className="input-field" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="label" style={{ display: 'block', marginBottom: 8 }}>Password</label>
            <input type="password" required minLength={6} placeholder="••••••••" className="input-field" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button type="submit" className="btn-signal" style={{ width: '100%', justifyContent: 'center', padding: '14px 24px', marginTop: 4 }} disabled={loading}>
            {loading ? 'Creating account…' : `Continue as ${role === 'seeker' ? 'Job Seeker' : 'Recruiter'} →`}
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '28px 0' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--wire)' }}></div>
          <span className="label">or continue with</span>
          <div style={{ flex: 1, height: 1, background: 'var(--wire)' }}></div>
        </div>

        <a href={apiUrl(`/login/google?role=${role}`)} className="btn-ghost" style={{ width: '100%', justifyContent: 'center', gap: 10, padding: '12px 24px' }}>
          <svg width="16" height="16" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
          </svg>
          Continue with Google
        </a>
      </div>
    </div>
  )
}
