import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { get } from '../lib/api'

export default function CompanyProfile() {
  const { user } = useAuth()
  const { userId } = useParams()
  const targetId = userId || user?.id
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!targetId) return
    get(`/api/companies/${targetId}`)
      .then(setData)
      .catch((err) => setError(err.message))
  }, [targetId])

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

  const { profile, jobs, is_owner, total_applicants } = data

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 32 }}>
        <Link to="/dashboard" style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: 'var(--chalk-3)', textDecoration: 'none', letterSpacing: '0.05em', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
          ← Dashboard
        </Link>
      </div>

      <div className="profile-header animate-fade-up" style={{ animationDelay: '0.05s', padding: 48, gap: 32 }}>
        <div className="profile-avatar" style={{ width: 100, height: 100, fontSize: 40 }}>
          {profile.company_name ? profile.company_name[0].toUpperCase() : '?'}
        </div>
        <div style={{ flex: 1 }}>
          <h1 className="display" style={{ fontSize: 'clamp(24px,4vw,40px)', color: 'var(--chalk)', marginBottom: 8 }}>{profile.company_name}</h1>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginBottom: 12 }}>
            {profile.company_size && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--chalk-3)' }}>
                <i className="bi bi-people-fill" style={{ color: 'var(--signal)' }}></i>
                <span>{profile.company_size} employees</span>
              </div>
            )}
            {profile.website && (
              <a href={profile.website} target="_blank" rel="noreferrer" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--signal)', textDecoration: 'none' }}>
                <i className="bi bi-globe"></i>
                <span>Visit website</span>
              </a>
            )}
            {profile.location && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--chalk-3)' }}>
                <i className="bi bi-geo-alt"></i>
                <span>{profile.location}</span>
              </div>
            )}
          </div>
          <p style={{ fontSize: 13, color: 'var(--chalk-2)', lineHeight: 1.6 }}>
            {profile.company_name} is a leading organization in the <strong style={{ color: 'var(--signal)' }}>{profile.industry}</strong> sector.
          </p>
        </div>
        {is_owner && (
          <div style={{ display: 'flex', gap: 8, flexDirection: 'column' }}>
            <Link to="/setup-profile" className="btn-ghost" style={{ padding: '10px 16px', fontSize: 12, whiteSpace: 'nowrap', textDecoration: 'none' }}>
              ✎ Edit Profile
            </Link>
            <Link to="/post-job" className="btn-signal" style={{ padding: '10px 16px', fontSize: 12, whiteSpace: 'nowrap' }}>
              + Post Job
            </Link>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-px animate-fade-up" style={{ background: 'var(--wire)', marginBottom: 48, animationDelay: '0.1s' }}>
        <div className="info-card">
          <i className="bi bi-briefcase-fill" style={{ fontSize: 20, color: 'var(--signal)', flexShrink: 0 }}></i>
          <div>
            <div className="label">Active Jobs</div>
            <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 24, fontWeight: 700, color: 'var(--chalk)' }}>{jobs.length}</div>
          </div>
        </div>
        <div className="info-card">
          <i className="bi bi-people-fill" style={{ fontSize: 20, color: 'var(--signal)', flexShrink: 0 }}></i>
          <div>
            <div className="label">Total Applicants</div>
            <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 24, fontWeight: 700, color: 'var(--chalk)' }}>{total_applicants}</div>
          </div>
        </div>
        <div className="info-card">
          <i className="bi bi-calendar-event" style={{ fontSize: 20, color: 'var(--signal)', flexShrink: 0 }}></i>
          <div>
            <div className="label">Member Since</div>
            <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 14, fontWeight: 600, color: 'var(--chalk)' }}>2024</div>
          </div>
        </div>
      </div>

      <div className="animate-fade-up" style={{ animationDelay: '0.15s' }}>
        <div className="section-label" style={{ marginBottom: 16 }}>
          <span className="label-signal">Active Postings</span>
        </div>

        {jobs.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, background: 'var(--wire)' }}>
            {jobs.map((job) => (
              <div key={job.id} style={{ background: 'var(--ink-2)', border: '1px solid var(--wire)', borderLeft: '2px solid transparent', padding: '20px 24px', transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--chalk)', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{job.title}</h3>
                    {job.applicant_count > 0 && (
                      <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, background: 'var(--signal-dim)', color: 'var(--signal)', padding: '2px 7px', letterSpacing: '0.05em', flexShrink: 0 }}>
                        {job.applicant_count} APPLICANTS
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    <span className="label">{job.location}</span>
                    <span className="label">{job.job_type}</span>
                  </div>
                </div>
                {is_owner && (
                  <Link to={`/applicants/${job.id}`} className="btn-ghost" style={{ padding: '8px 14px', fontSize: 12, flexShrink: 0, whiteSpace: 'nowrap' }}>
                    View Applicants →
                  </Link>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '48px 24px', textAlign: 'center', background: 'var(--ink-2)', border: '1px solid var(--wire)' }}>
            <p style={{ fontSize: 14, color: 'var(--chalk-3)' }}>
              No active jobs.{' '}
              {is_owner && <Link to="/post-job" style={{ color: 'var(--signal)', textDecoration: 'none' }}>Post one →</Link>}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
