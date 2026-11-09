import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useToast } from '../context/ToastContext'
import { get } from '../lib/api'

export default function TalentFeed() {
  const { toast } = useToast()
  const navigate = useNavigate()
  const [seekers, setSeekers] = useState(null)

  useEffect(() => {
    get('/api/talent')
      .then((data) => setSeekers(data.seekers))
      .catch((err) => {
        toast(err.message, 'error')
        setSeekers([])
      })
  }, [])

  if (seekers === null) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '50vh' }}>
        <span className="label-signal animate-blink">● LOADING</span>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 48 }}>
        <div>
          <div className="label-signal" style={{ marginBottom: 8 }}>Talent Discovery</div>
          <h1 className="display" style={{ fontSize: 'clamp(24px,3vw,40px)', color: 'var(--chalk)' }}>
            Browse Candidates
          </h1>
        </div>
        <Link to="/dashboard" className="btn-ghost" style={{ padding: '10px 20px', fontSize: 12 }}>
          ← Dashboard
        </Link>
      </div>

      {seekers.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-up" style={{ animationDelay: '0.05s' }}>
          {seekers.map((seeker) => (
            <div key={seeker.id} className="talent-card">
              <div className="talent-avatar">{seeker.name ? seeker.name[0].toUpperCase() : '?'}</div>

              <h3 className="talent-name">{seeker.name}</h3>
              <p className="talent-headline">{seeker.headline || 'Aspiring Professional'}</p>
              <div className="talent-location">
                <i className="bi bi-geo-alt" style={{ marginRight: 4 }}></i>{seeker.location || 'India'}
              </div>

              {(seeker.skills || []).length > 0 && (
                <div className="skill-list">
                  {seeker.skills.slice(0, 3).map((s) => (
                    <span key={s} className="skill-tag">{s}</span>
                  ))}
                  {seeker.skills.length > 3 && <span className="skill-tag">+{seeker.skills.length - 3}</span>}
                </div>
              )}

              <div style={{ display: 'flex', gap: 8, width: '100%', marginTop: 'auto' }}>
                <button
                  type="button"
                  className="btn-ghost"
                  style={{ flex: 1, padding: '10px 12px', fontSize: 12 }}
                  onClick={() => navigate(`/talent/${seeker.id}`)}
                >
                  View Profile
                </button>
                <button
                  type="button"
                  className="btn-signal"
                  style={{ flex: 1, padding: '10px 12px', fontSize: 12 }}
                  onClick={() => toast('Message feature coming soon')}
                >
                  Message
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="animate-fade-up" style={{ textAlign: 'center', padding: '80px 24px', background: 'var(--ink-2)', border: '1px solid var(--wire)' }}>
          <i className="bi bi-search" style={{ fontSize: 48, color: 'var(--chalk-3)', marginBottom: 16, display: 'block', opacity: 0.5 }}></i>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--chalk-2)', marginBottom: 8 }}>No candidates yet</h3>
          <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.6 }}>
            Candidates will appear here as they complete their profiles on SkillMap.
          </p>
        </div>
      )}
    </div>
  )
}
