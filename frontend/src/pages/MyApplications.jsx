import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useToast } from '../context/ToastContext'
import { get } from '../lib/api'

const STATUS_CLASS = {
  Applied: 'status-pending',
  Shortlisted: 'status-shortlisted',
  Accepted: 'status-accepted',
  Rejected: 'status-rejected',
}

export default function MyApplications() {
  const { toast } = useToast()
  const [applications, setApplications] = useState(null)
  const [needsSetup, setNeedsSetup] = useState(false)

  useEffect(() => {
    get('/api/applications/me')
      .then((data) => {
        setApplications(data.applications)
        setNeedsSetup(Boolean(data.needs_setup))
      })
      .catch((err) => {
        toast(err.message, 'error')
        setApplications([])
      })
  }, [])

  if (applications === null) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '50vh' }}>
        <span className="label-signal animate-blink">● LOADING</span>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ marginBottom: 48 }}>
        <div className="label-signal" style={{ marginBottom: 8 }}>Tracking</div>
        <h1 className="display" style={{ fontSize: 'clamp(24px,3vw,40px)', color: 'var(--chalk)' }}>
          My Applications
        </h1>
        <p style={{ fontSize: 13, color: 'var(--chalk-3)', marginTop: 8 }}>
          Track every role you have applied to and where each application stands.
        </p>
      </div>

      {needsSetup && (
        <div className="flash-msg animate-fade-up" style={{ marginBottom: 32 }}>
          <p style={{ fontSize: 13 }}>
            Complete your profile to start applying.{' '}
            <Link to="/setup-profile" style={{ color: 'var(--signal)' }}>Set up profile →</Link>
          </p>
        </div>
      )}

      {applications.length > 0 ? (
        <div className="animate-fade-up" style={{ animationDelay: '0.05s', display: 'flex', flexDirection: 'column', gap: 2, background: 'var(--wire)' }}>
          {applications.map((app) => (
            <div key={app.id} className="job-row">
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
                  <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--chalk)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', margin: 0 }}>
                    {app.job ? app.job.title : 'Job removed'}
                  </h3>
                  <span className={`status-badge ${STATUS_CLASS[app.status] || 'status-pending'}`}>{app.status}</span>
                </div>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
                  <span className="label" style={{ fontFamily: "'JetBrains Mono',monospace" }}>{app.job ? app.job.company_name : ''}</span>
                  {app.job && <span className="label">{app.job.location}</span>}
                  {app.job && <span className="label">{app.job.job_type}</span>}
                  {app.match_score != null && (
                    <span className="label" style={{ color: 'var(--signal)' }}>MATCH {Math.round(app.match_score)}%</span>
                  )}
                  {app.applied_at && (
                    <span className="label" style={{ fontFamily: "'JetBrains Mono',monospace" }}>
                      APPLIED {app.applied_at.slice(0, 10)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : !needsSetup ? (
        <div className="animate-fade-up" style={{ textAlign: 'center', padding: '80px 24px', background: 'var(--ink-2)', border: '1px solid var(--wire)' }}>
          <i className="bi bi-send" style={{ fontSize: 48, color: 'var(--chalk-3)', marginBottom: 16, display: 'block', opacity: 0.5 }}></i>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--chalk-2)', marginBottom: 8 }}>No applications yet</h3>
          <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.6 }}>
            Browse the job feed and apply to roles that match your skills.
          </p>
          <div style={{ marginTop: 20 }}>
            <Link to="/jobs" className="btn-signal">Browse Jobs →</Link>
          </div>
        </div>
      ) : null}
    </div>
  )
}
