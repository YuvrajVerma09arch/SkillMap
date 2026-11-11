import { useState, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { apiUrl } from '../lib/api'

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  )
}

export default function Login() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(params.get('error') || '')
  const [notice, setNotice] = useState(
    params.get('registered') ? 'Registration received. Sign in to continue.' : ''
  )
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) navigate('/', { replace: true })
  }, [user, navigate])

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setNotice('')
    setLoading(true)
    try {
      const u = await login(email, password)
      navigate(u.role === 'seeker' ? '/' : '/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-grid" style={{ minHeight: 'calc(100vh - 56px)', display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
      <div className="auth-left" style={{ background: 'var(--ink-2)', borderRight: '1px solid var(--wire)', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', padding: 60, position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'relative', width: 300, height: 300, marginBottom: 48 }}>
          <svg className="orbit-a" style={{ position: 'absolute', inset: 0 }} width="300" height="300" viewBox="0 0 300 300" fill="none">
            <circle cx="150" cy="150" r="145" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
            <ellipse cx="150" cy="150" rx="145" ry="52" stroke="rgba(255,255,255,0.04)" strokeWidth="0.75" />
            <circle cx="150" cy="5" r="3" fill="rgba(255,255,255,0.3)" />
            <circle cx="295" cy="150" r="2" fill="rgba(255,255,255,0.2)" />
          </svg>
          <svg className="orbit-b" style={{ position: 'absolute', inset: 20 }} width="260" height="260" viewBox="0 0 260 260" fill="none">
            <ellipse cx="130" cy="130" rx="120" ry="42" stroke="rgba(230,57,70,0.2)" strokeWidth="0.75" />
            <circle cx="130" cy="10" r="3" fill="#e63946" opacity="0.7" />
          </svg>
          <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: 44, height: 44, background: 'var(--ink)', border: '1px solid var(--wire-2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="22" height="22" viewBox="0 0 28 28" fill="none">
              <circle cx="14" cy="14" r="13" stroke="#e63946" strokeWidth="1" />
              <circle cx="14" cy="14" r="3" fill="#e63946" />
              <ellipse cx="14" cy="14" rx="13" ry="5" stroke="rgba(255,255,255,0.2)" strokeWidth="0.75" />
            </svg>
          </div>
        </div>

        <div style={{ textAlign: 'center', maxWidth: 260 }}>
          <h2 className="display" style={{ fontSize: 22, color: 'var(--chalk)', marginBottom: 12 }}>Career Intelligence<br />System</h2>
          <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.7 }}>
            Authenticate to access your AI-powered career dashboard and tools.
          </p>
        </div>

        <div style={{ position: 'absolute', bottom: 24, left: 24, right: 24, display: 'flex', justifyContent: 'space-between' }}>
          <span className="label">SKILLMAP · AUTH</span>
          <span className="label">v2025.1</span>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '60px 48px', width: '100%', maxWidth: 480, margin: '0 auto' }}>
        <div className="animate-fade-up">
          <div className="label-signal" style={{ marginBottom: 12 }}>Authentication</div>
          <h1 className="display" style={{ fontSize: 36, color: 'var(--chalk)', marginBottom: 8 }}>Sign In</h1>
          <p style={{ fontSize: 14, color: 'var(--chalk-3)', marginBottom: 40 }}>
            New here?
            <Link to="/role-select" style={{ color: 'var(--signal)', textDecoration: 'none', marginLeft: 4 }}>Create an account →</Link>
          </p>

          {notice && !error && (
            <div className="flash-msg" style={{ marginBottom: 20, borderColor: 'var(--signal)' }}>
              <p style={{ fontSize: 13, color: 'var(--chalk)' }}>{notice}</p>
            </div>
          )}

          {error && (
            <div className="flash-msg" style={{ marginBottom: 20 }}>
              <p style={{ fontSize: 13, color: 'var(--chalk)' }}>{error}</p>
            </div>
          )}

          <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div>
              <label className="label" style={{ display: 'block', marginBottom: 8 }}>Email Address</label>
              <input type="email" required placeholder="you@example.com" className="input-field" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>

            <div>
              <label className="label" style={{ display: 'block', marginBottom: 8 }}>Password</label>
              <input type="password" required placeholder="••••••••" className="input-field" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>

            <button type="submit" className="btn-signal" style={{ width: '100%', justifyContent: 'center', marginTop: 4, padding: '14px 24px', fontSize: 14 }} disabled={loading}>
              {loading ? 'Authenticating…' : 'Authenticate →'}
            </button>
          </form>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '28px 0' }}>
            <div style={{ flex: 1, height: 1, background: 'var(--wire)' }}></div>
            <span className="label">or continue with</span>
            <div style={{ flex: 1, height: 1, background: 'var(--wire)' }}></div>
          </div>

          <a href={apiUrl('/login/google')} className="btn-ghost" style={{ width: '100%', justifyContent: 'center', gap: 10, padding: '12px 24px' }}>
            <GoogleIcon />
            Continue with Google
          </a>
        </div>
      </div>
    </div>
  )
}
