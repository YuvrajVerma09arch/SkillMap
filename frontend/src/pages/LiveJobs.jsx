import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useToast } from '../context/ToastContext'
import { get } from '../lib/api'

const TABS = [
  { id: 'remote', icon: 'bi-wifi', label: 'Remote Tech' },
  { id: 'india', icon: 'bi-geo-alt-fill', label: 'India Tech' },
  { id: 'rss', icon: 'bi-rss', label: 'RSS Feeds' },
  { id: 'usa', icon: 'bi-stars', label: 'USAJOBS' },
  { id: 'europe', icon: 'bi-globe-europe-africa', label: 'Europe' },
  { id: 'aicte-govt', icon: 'bi-building', label: 'Govt Internships' },
  { id: 'aicte-private', icon: 'bi-briefcase', label: 'Private Internships' },
  { id: 'carrerlift', icon: 'bi-mortarboard', label: 'Fresher Jobs' },
]

export default function LiveJobs() {
  const { toast } = useToast()
  const navigate = useNavigate()
  const [feed, setFeed] = useState('india')
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async (f) => {
    setLoading(true)
    try {
      const data = await get(`/api/live-jobs?feed=${f}`)
      setJobs(data.jobs)
      setFeed(data.feed)
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load('india') }, [])

  const analyzeFit = (job) => {
    navigate('/resume-checker', { state: { jobDescription: job.clean_description || '' } })
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ marginBottom: 32 }}>
        <div className="label-signal" style={{ marginBottom: 8 }}>Live Feed</div>
        <h1 className="display" style={{ fontSize: 'clamp(24px,3vw,40px)', color: 'var(--chalk)' }}>
          Global Opportunities
        </h1>
        <p style={{ fontSize: 13, color: 'var(--chalk-3)', marginTop: 8 }}>
          Real-time jobs from multiple sources. Click "Analyze Fit" to see how well you match.
        </p>
      </div>

      <div className="feed-tabs animate-fade-up" style={{ animationDelay: '0.05s' }}>
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={`feed-tab${feed === t.id ? ' active' : ''}`}
            onClick={() => load(t.id)}
          >
            <i className={`bi ${t.icon}`} style={{ marginRight: 4 }}></i>{t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center" style={{ minHeight: '30vh' }}>
          <span className="label-signal animate-blink">● FETCHING LIVE JOBS</span>
        </div>
      ) : jobs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-up" style={{ animationDelay: '0.1s' }}>
          {jobs.map((job, i) => (
            <div key={i} className="live-job-card">
              <div className="live-badge">Live</div>

              <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--chalk)', margin: 0 }}>{job.title}</h3>
              <p style={{ fontSize: 12, color: 'var(--chalk-3)', margin: 0, fontFamily: "'JetBrains Mono',monospace" }}>{job.company}</p>

              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 4 }}>
                <span style={{ fontSize: 11, color: 'var(--chalk-3)' }}><i className="bi bi-geo-alt" style={{ marginRight: 3 }}></i>{job.location || 'Remote'}</span>
                {job.stipend && (
                  <span style={{ fontSize: 11, color: 'var(--chalk-3)', fontFamily: "'JetBrains Mono',monospace" }}><i className="bi bi-cash-coin" style={{ marginRight: 3 }}></i>{job.stipend}</span>
                )}
                <span style={{ fontSize: 11, color: 'var(--chalk-3)', fontFamily: "'JetBrains Mono',monospace" }}>{job.source}</span>
              </div>

              <p style={{ fontSize: 12, color: 'var(--chalk-2)', lineHeight: 1.5, marginTop: 8, flex: 1 }}>
                {(job.clean_description || '').slice(0, 80)}...
              </p>

              <div style={{ display: 'flex', gap: 8, marginTop: 'auto' }}>
                <a href={job.url} target="_blank" rel="noreferrer" className="btn-signal" style={{ flex: 1, padding: '10px 12px', fontSize: 12, textAlign: 'center', textDecoration: 'none', justifyContent: 'center' }}>
                  <i className="bi bi-box-arrow-up-right" style={{ marginRight: 4 }}></i>Apply
                </a>
                <button type="button" className="btn-ghost" style={{ flex: 1, padding: '10px 12px', fontSize: 12, justifyContent: 'center' }} onClick={() => analyzeFit(job)}>
                  <i className="bi bi-magic" style={{ marginRight: 4 }}></i>Fit
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="animate-fade-up" style={{ textAlign: 'center', padding: '80px 24px', background: 'var(--ink-2)', border: '1px solid var(--wire)' }}>
          <i className="bi bi-cloud-slash" style={{ fontSize: 48, color: 'var(--chalk-3)', marginBottom: 16, display: 'block', opacity: 0.5 }}></i>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--chalk-2)', marginBottom: 8 }}>Could not fetch jobs</h3>
          <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.6 }}>
            The API might be taking a quick nap. Try refreshing or check back soon!
          </p>
        </div>
      )}
    </div>
  )
}
