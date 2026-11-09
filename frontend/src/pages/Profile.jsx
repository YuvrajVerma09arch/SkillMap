import { useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { get, apiUrl } from '../lib/api'

export default function Profile() {
  const { user } = useAuth()
  const { userId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  const targetId = userId || user?.id

  useEffect(() => {
    if (!targetId) return
    setData(null)
    get(`/api/profiles/${targetId}`)
      .then(setData)
      .catch((err) => {
        if (err.data && err.data.needs_setup) navigate('/setup-profile', { replace: true })
        else setError(err.message)
      })
  }, [targetId, navigate])

  if (error) {
    return (
      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 24px' }}>
        <div className="flash-msg"><p style={{ fontSize: 13 }}>{error}</p></div>
      </div>
    )
  }
  if (!data) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '50vh' }}>
        <span className="label-signal animate-blink">● LOADING</span>
      </div>
    )
  }

  const { user: target, profile, is_own_profile, is_recruiter } = data
  const skills = profile?.skills || []

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 32 }}>
        <Link to={is_own_profile ? '/' : '/talent'} style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: 'var(--chalk-3)', textDecoration: 'none', letterSpacing: '0.05em', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          ← {is_own_profile ? 'Home' : 'Talent Feed'}
        </Link>
      </div>

      <div className="profile-header animate-fade-up" style={{ animationDelay: '0.05s' }}>
        <div className="profile-avatar">{target.name ? target.name[0].toUpperCase() : '?'}</div>
        <div style={{ flex: 1 }}>
          <h1 className="display" style={{ fontSize: 'clamp(24px,4vw,40px)', color: 'var(--chalk)', marginBottom: 4 }}>{target.name}</h1>
          <p style={{ fontSize: 14, color: 'var(--signal)', marginBottom: 8, fontFamily: "'JetBrains Mono',monospace" }}>
            {profile?.headline || 'Aspiring Professional'}
          </p>
          <p style={{ fontSize: 13, color: 'var(--chalk-3)' }}>
            <i className="bi bi-geo-alt" style={{ marginRight: 4 }}></i>{profile?.location || 'India'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, flexDirection: 'column' }}>
          {is_own_profile ? (
            <>
              <Link to="/setup-profile" className="btn-ghost" style={{ padding: '10px 16px', fontSize: 12, whiteSpace: 'nowrap', textDecoration: 'none' }}>
                ✎ Edit Profile
              </Link>
              <button onClick={() => alert('Share feature coming soon')} className="btn-signal" style={{ padding: '10px 16px', fontSize: 12, whiteSpace: 'nowrap' }}>
                Share Profile
              </button>
            </>
          ) : is_recruiter && profile?.resume_file ? (
            <a href={apiUrl(`/static/uploads/${profile.resume_file}`)} download className="btn-signal" style={{ padding: '10px 16px', fontSize: 12, whiteSpace: 'nowrap', textDecoration: 'none', textAlign: 'center' }}>
              Download Resume
            </a>
          ) : null}
        </div>
      </div>

      <div className="info-grid animate-fade-up" style={{ animationDelay: '0.1s' }}>
        <div className="info-tile">
          <div className="label">Credits</div>
          <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 24, fontWeight: 700, color: 'var(--chalk)', marginTop: 4 }}>
            {is_own_profile ? user.credits : '—'}
          </div>
        </div>
        <div className="info-tile">
          <div className="label">Skills</div>
          <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 24, fontWeight: 700, color: 'var(--chalk)', marginTop: 4 }}>{skills.length}</div>
        </div>
        <div className="info-tile">
          <div className="label">Experience</div>
          <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 14, fontWeight: 600, color: 'var(--chalk)', marginTop: 4 }}>
            {profile?.experience_years || '0'} years
          </div>
        </div>
        <div className="info-tile">
          <div className="label">Profile</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }}></span>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12, color: 'var(--chalk-2)' }}>Complete</span>
          </div>
        </div>
      </div>

      <div className="animate-fade-up" style={{ animationDelay: '0.15s' }}>
        <div className="section-label" style={{ marginBottom: 16 }}>
          <span className="label-signal">Skills</span>
        </div>
        {skills.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, background: 'var(--ink-2)', border: '1px solid var(--wire)', padding: 16 }}>
            {skills.map((s) => (
              <span key={s} style={{ display: 'inline-block', background: 'var(--ink-3)', border: '1px solid var(--wire-2)', padding: '6px 12px', fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: 'var(--chalk-2)' }}>
                {s}
              </span>
            ))}
          </div>
        ) : (
          <div style={{ padding: 24, textAlign: 'center', background: 'var(--ink-2)', border: '1px solid var(--wire)' }}>
            <p style={{ fontSize: 13, color: 'var(--chalk-3)' }}>
              No skills added yet.{' '}
              {is_own_profile && (
                <Link to="/setup-profile" style={{ color: 'var(--signal)', textDecoration: 'none' }}>Add skills →</Link>
              )}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
