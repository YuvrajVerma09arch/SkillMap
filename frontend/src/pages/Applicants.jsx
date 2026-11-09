import { useEffect, useState, useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useToast } from '../context/ToastContext'
import { get, post } from '../lib/api'

const ACTIONS = [
  { status: 'Shortlisted', icon: 'bi-star-fill', cls: 'shortlist', title: 'Shortlist for Interview' },
  { status: 'Accepted', icon: 'bi-check-lg', cls: 'accept', title: 'Accept / Hire' },
  { status: 'Rejected', icon: 'bi-x-lg', cls: 'reject', title: 'Reject' },
]

export default function Applicants() {
  const { jobId } = useParams()
  const { toast } = useToast()
  const [job, setJob] = useState(null)
  const [applicants, setApplicants] = useState(null)
  const [error, setError] = useState('')
  const [busyId, setBusyId] = useState(null)

  const load = useCallback(() => {
    get(`/api/recruiter/jobs/${jobId}/applicants`)
      .then((data) => {
        setJob(data.job)
        setApplicants(data.applicants)
      })
      .catch((err) => setError(err.message))
  }, [jobId])

  useEffect(() => { load() }, [load])

  const setStatus = async (appId, status) => {
    setBusyId(appId)
    try {
      const data = await post(`/api/applications/${appId}/status`, { status })
      if (data.email_sent === false) {
        toast(`Status updated, but email failed: ${data.email_error || 'unknown error'}`, 'error')
      } else {
        toast(`Marked ${data.application.status}.`)
      }
      load()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setBusyId(null)
    }
  }

  if (error) {
    return (
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 24px' }}>
        <div className="flash-msg"><p style={{ fontSize: 13 }}>{error}</p></div>
        <div style={{ marginTop: 16 }}><Link to="/dashboard" className="btn-ghost">← Dashboard</Link></div>
      </div>
    )
  }
  if (applicants === null) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '50vh' }}>
        <span className="label-signal animate-blink">● LOADING</span>
      </div>
    )
  }

  const count = applicants.length

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 32 }}>
        <div>
          <div className="label-signal" style={{ marginBottom: 8 }}>Applicants</div>
          <h1 className="display" style={{ fontSize: 'clamp(24px,3vw,40px)', color: 'var(--chalk)' }}>
            {job.title}
          </h1>
          <p style={{ fontSize: 13, color: 'var(--chalk-3)', marginTop: 6, fontFamily: "'JetBrains Mono',monospace" }}>
            {count} application{count !== 1 ? 's' : ''}
          </p>
        </div>
        <Link to="/dashboard" className="btn-ghost" style={{ padding: '10px 20px', fontSize: 12 }}>
          ← Dashboard
        </Link>
      </div>

      {count > 0 ? (
        <div className="animate-fade-up" style={{ animationDelay: '0.05s', overflowX: 'auto' }}>
          <table className="app-table">
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Experience</th>
                <th>Skills</th>
                <th>Applied</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {applicants.map((app) => {
                const locked = ['Accepted', 'Rejected'].includes(app.status)
                const skills = app.skills || []
                return (
                  <tr key={app.id} className={locked ? 'locked' : ''}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div className="candidate-avatar">{app.name ? app.name[0].toUpperCase() : '?'}</div>
                        <div style={{ minWidth: 0 }}>
                          <div className="candidate-name">{app.name}</div>
                          <div className="candidate-email">{app.email}</div>
                        </div>
                      </div>
                    </td>

                    <td style={{ fontWeight: 600, color: 'var(--chalk)' }}>
                      {app.experience != null ? `${app.experience} yrs` : '—'}
                    </td>

                    <td>
                      {skills.slice(0, 3).map((s) => (
                        <span key={s} className="skill-badge" style={{ marginRight: 4, marginBottom: 2 }}>{s}</span>
                      ))}
                      {skills.length > 3 && <span className="skill-badge" style={{ marginRight: 4, marginBottom: 2 }}>+{skills.length - 3}</span>}
                    </td>

                    <td style={{ fontSize: 12, color: 'var(--chalk-3)', fontFamily: "'JetBrains Mono',monospace" }}>
                      {app.applied_at || '—'}
                    </td>

                    <td>
                      <span className={`status-badge status-${(app.status || '').toLowerCase()}`}>{app.status}</span>
                    </td>

                    <td style={{ textAlign: 'right' }}>
                      {!locked ? (
                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                          {ACTIONS.map((a) => (
                            <button
                              key={a.status}
                              type="button"
                              className={`action-btn ${a.cls}`}
                              title={a.title}
                              disabled={busyId === app.id}
                              onClick={() => setStatus(app.id, a.status)}
                            >
                              <i className={`bi ${a.icon}`}></i>
                            </button>
                          ))}
                        </div>
                      ) : (
                        <span style={{ fontSize: 11, color: 'var(--chalk-3)', fontFamily: "'JetBrains Mono',monospace", display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <i className="bi bi-lock-fill"></i> Locked
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="animate-fade-up" style={{ textAlign: 'center', padding: '80px 24px', background: 'var(--ink-2)', border: '1px solid var(--wire)' }}>
          <i className="bi bi-inbox" style={{ fontSize: 48, color: 'var(--chalk-3)', marginBottom: 16, display: 'block', opacity: 0.5 }}></i>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--chalk-2)', marginBottom: 8 }}>No applicants yet</h3>
          <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.6 }}>
            Applications will appear here when candidates apply to this job posting.
          </p>
        </div>
      )}
    </div>
  )
}
