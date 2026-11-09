import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { get } from '../lib/api'

export default function Dashboard() {
  const { user } = useAuth()
  const { toast } = useToast()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    get('/api/recruiter/dashboard')
      .then(setData)
      .catch((err) => {
        if (err.status === 404 && err.data && err.data.needs_setup) {
          setError('setup')
        } else {
          setError(err.message)
        }
      })
  }, [])

  if (error === 'setup') {
    return (
      <div style={{ maxWidth: 700, margin: '0 auto', padding: '80px 24px', textAlign: 'center', position: 'relative', zIndex: 1 }}>
        <div className="label-signal" style={{ marginBottom: 12 }}>Setup Required</div>
        <h1 className="display" style={{ fontSize: 32, color: 'var(--chalk)', marginBottom: 12 }}>Complete your company profile first</h1>
        <p style={{ fontSize: 13, color: 'var(--chalk-3)', marginBottom: 24 }}>Your dashboard unlocks once your company profile is on file.</p>
        <Link to="/setup-profile" className="btn-signal">Set Up Profile →</Link>
      </div>
    )
  }
  if (error) {
    return (
      <div style={{ maxWidth: 700, margin: '0 auto', padding: '80px 24px' }}>
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

  const { stats, jobs, candidates } = data
  const credits = stats.credits != null ? stats.credits : user?.credits

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16, marginBottom: 48 }} className="animate-fade-up">
        <div>
          <div className="label-signal" style={{ marginBottom: 8 }}>Recruiter Dashboard</div>
          <h1 className="display" style={{ fontSize: 'clamp(24px,3vw,40px)', color: 'var(--chalk)' }}>
            Welcome, {user?.name}
          </h1>
        </div>
        <Link to="/post-job" className="btn-signal">+ Post New Job</Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-px animate-fade-up" style={{ background: 'var(--wire)', marginBottom: 48, animationDelay: '0.05s' }}>
        <div className="stat-tile">
          <div className="label" style={{ marginBottom: 10 }}>Total Applicants</div>
          <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 36, fontWeight: 700, color: 'var(--chalk)', letterSpacing: '-0.03em' }}>{stats.total_applicants}</div>
        </div>
        <div className="stat-tile">
          <div className="label" style={{ marginBottom: 10 }}>Active Jobs</div>
          <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 36, fontWeight: 700, color: 'var(--chalk)', letterSpacing: '-0.03em' }}>{stats.active_jobs}</div>
        </div>
        <div className="stat-tile">
          <div className="label" style={{ marginBottom: 10 }}>Credits</div>
          <div style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 36, fontWeight: 700, color: 'var(--signal)', letterSpacing: '-0.03em' }}>{credits}</div>
        </div>
        <div className="stat-tile">
          <div className="label" style={{ marginBottom: 10 }}>Status</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }}></span>
            <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 12, color: 'var(--chalk-2)' }}>Active</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 animate-fade-up" style={{ animationDelay: '0.1s' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div className="section-label" style={{ marginBottom: 0 }}>
              <span className="label-signal">Active Postings</span>
            </div>
            <Link to="/post-job" style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: 'var(--signal)', letterSpacing: '0.08em', textTransform: 'uppercase', textDecoration: 'none' }}>+ New →</Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, background: 'var(--wire)' }}>
            {jobs.length > 0 ? jobs.map((job) => (
              <div key={job.id} className="job-row">
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--chalk)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', margin: 0 }}>{job.title}</h3>
                    {job.applicant_count > 0 && (
                      <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 9, background: 'var(--signal-dim)', color: 'var(--signal)', padding: '2px 7px', letterSpacing: '0.05em', flexShrink: 0 }}>{job.applicant_count} APPLICANTS</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    <span className="label">{job.location}</span>
                    <span className="label">{job.job_type}</span>
                  </div>
                </div>
                <Link to={`/applicants/${job.id}`} className="btn-ghost" style={{ padding: '7px 14px', fontSize: 12, flexShrink: 0, textDecoration: 'none' }}>
                  View →
                </Link>
              </div>
            )) : (
              <div style={{ padding: '48px 24px', textAlign: 'center', background: 'var(--ink-2)' }}>
                <p style={{ fontSize: 14, color: 'var(--chalk-3)' }}>No active jobs. <Link to="/post-job" style={{ color: 'var(--signal)', textDecoration: 'none' }}>Post one →</Link></p>
              </div>
            )}
          </div>
        </div>

        <div className="animate-fade-up" style={{ animationDelay: '0.15s' }}>
          <div className="section-label" style={{ marginBottom: 20 }}>
            <span className="label-signal">Recent Candidates</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, background: 'var(--wire)' }}>
            {candidates.length > 0 ? candidates.map((c, i) => (
              <div key={i} className="candidate-card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                  <div style={{ width: 32, height: 32, background: 'var(--ink)', border: '1px solid var(--wire-2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'JetBrains Mono',monospace", fontSize: 12, fontWeight: 700, color: 'var(--signal)', flexShrink: 0 }}>
                    {c.name ? c.name[0].toUpperCase() : '?'}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--chalk)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', margin: 0 }}>{c.name}</p>
                    <p className="label" style={{ marginTop: 2 }}>{c.email}</p>
                  </div>
                </div>
              </div>
            )) : (
              <div style={{ padding: '32px 20px', textAlign: 'center', background: 'var(--ink-2)' }}>
                <p style={{ fontSize: 13, color: 'var(--chalk-3)' }}>No candidates yet.</p>
              </div>
            )}
          </div>

          <div style={{ marginTop: 16 }}>
            <Link to="/talent" className="btn-ghost" style={{ width: '100%', justifyContent: 'center', padding: '12px 20px', fontSize: 12, display: 'flex', textDecoration: 'none' }}>
              Browse Talent Feed →
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
