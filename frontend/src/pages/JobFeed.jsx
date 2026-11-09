import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useToast } from '../context/ToastContext'
import { get, post } from '../lib/api'

const JOB_TYPES = ['', 'Full-time', 'Part-time', 'Contract', 'Internship', 'Remote']

export default function JobFeed() {
  const { toast } = useToast()
  const [jobs, setJobs] = useState([])
  const [appliedIds, setAppliedIds] = useState([])
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(null)
  const [filters, setFilters] = useState({ role: '', location: '', type: '' })
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [total, setTotal] = useState(0)

  const load = async (f = filters, p = 1) => {
    setLoading(true)
    try {
      const qs = new URLSearchParams()
      if (f.role) qs.set('role', f.role)
      if (f.location) qs.set('location', f.location)
      if (f.type) qs.set('type', f.type)
      qs.set('page', p)
      qs.set('per_page', 10)
      const data = await get(`/api/jobs?${qs.toString()}`)
      setJobs(data.jobs)
      setAppliedIds(data.applied_ids)
      setPage(data.page)
      setPages(data.pages)
      setTotal(data.total)
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const setFilter = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }))

  const applyFilters = (e) => {
    e.preventDefault()
    load(filters, 1)
  }

  const goPage = (p) => {
    load(filters, p)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const apply = async (jobId) => {
    setApplying(jobId)
    try {
      await post(`/api/jobs/${jobId}/apply`)
      setAppliedIds((ids) => [...ids, jobId])
      toast('Application submitted.')
    } catch (err) {
      if (err.status === 403 && err.data && err.data.redirect) {
        toast('Complete your profile first.', 'error')
        return
      }
      toast(err.message, 'error')
    } finally {
      setApplying(null)
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ marginBottom: 40 }}>
        <div className="label-signal" style={{ marginBottom: 8 }}>Job Discovery</div>
        <h1 className="display" style={{ fontSize: 'clamp(24px,3vw,40px)', color: 'var(--chalk)' }}>
          Matching Jobs
        </h1>
        <p style={{ fontSize: 13, color: 'var(--chalk-3)', marginTop: 8 }}>
          Browse opportunities matched to your skills and career goals.
        </p>
      </div>

      <form onSubmit={applyFilters} className="animate-fade-up" style={{ animationDelay: '0.05s', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 32 }}>
        <input type="text" className="input-field" placeholder="Role keyword" value={filters.role} onChange={setFilter('role')} />
        <input type="text" className="input-field" placeholder="Location" value={filters.location} onChange={setFilter('location')} />
        <select className="input-field" style={{ cursor: 'pointer' }} value={filters.type} onChange={setFilter('type')}>
          {JOB_TYPES.map((t) => <option key={t} value={t}>{t || 'All types'}</option>)}
        </select>
        <button type="submit" className="btn-signal" style={{ justifyContent: 'center', padding: '12px 20px' }}>Filter →</button>
      </form>

      {loading ? (
        <div className="flex items-center justify-center" style={{ minHeight: '30vh' }}>
          <span className="label-signal animate-blink">● LOADING</span>
        </div>
      ) : jobs.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, background: 'var(--wire)' }}>
          {jobs.map((job, i) => {
            const applied = appliedIds.includes(job.id)
            const skills = job.required_skills || []
            return (
              <div key={job.id} className="job-card animate-fade-up" style={{ animationDelay: `${i * 0.05}s` }}>
                <div>
                  <h2 className="job-title">{job.title}</h2>
                  <p className="job-company">{job.company_name}</p>
                </div>

                <div className="job-meta">
                  <span><i className="bi bi-geo-alt" style={{ marginRight: 4 }}></i>{job.location}</span>
                  <span><i className="bi bi-briefcase" style={{ marginRight: 4 }}></i>{job.job_type}</span>
                  {job.salary_range && (
                    <span><i className="bi bi-cash-stack" style={{ marginRight: 4 }}></i>{job.salary_range}</span>
                  )}
                </div>

                <p className="job-desc">
                  {(job.description || '').slice(0, 120)}{(job.description || '').length > 120 ? '...' : ''}
                </p>

                <div className="job-footer">
                  <div className="skill-badges">
                    {skills.slice(0, 3).map((s) => (
                      <span key={s} className="skill-badge">{s}</span>
                    ))}
                    {skills.length > 3 && <span className="skill-badge">+{skills.length - 3}</span>}
                  </div>
                  {job.external_link ? (
                    <a
                      href={job.external_link}
                      target="_blank"
                      rel="noreferrer"
                      className="btn-signal"
                      style={{ padding: '8px 16px', fontSize: 12, whiteSpace: 'nowrap', textAlign: 'center', textDecoration: 'none', justifyContent: 'center' }}
                    >
                      Apply ↗
                    </a>
                  ) : (
                    <button
                      type="button"
                      className={applied ? 'btn-ghost' : 'btn-signal'}
                      style={{ padding: '8px 16px', fontSize: 12, whiteSpace: 'nowrap' }}
                      disabled={applied || applying === job.id}
                      onClick={() => apply(job.id)}
                    >
                      {applied ? 'Applied ✓' : applying === job.id ? 'Applying…' : 'Apply Now →'}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="animate-fade-up" style={{ textAlign: 'center', padding: '80px 24px', background: 'var(--ink-2)', border: '1px solid var(--wire)' }}>
          <i className="bi bi-briefcase" style={{ fontSize: 48, color: 'var(--chalk-3)', marginBottom: 16, display: 'block', opacity: 0.5 }}></i>
          <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--chalk-2)', marginBottom: 8 }}>No jobs available</h3>
          <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.6 }}>
            Check back soon for new opportunities, or complete your profile to get better matches.
          </p>
          <div style={{ marginTop: 20 }}>
            <Link to="/applications" className="btn-ghost">My Applications →</Link>
          </div>
        </div>
      )}

      {jobs.length > 0 && (
        <div style={{ marginTop: 32, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
          {pages > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <button
                type="button"
                className="btn-ghost"
                style={{ padding: '8px 16px', fontSize: 12, opacity: page <= 1 ? 0.4 : 1 }}
                disabled={page <= 1 || loading}
                onClick={() => goPage(page - 1)}
              >
                ← Prev
              </button>
              <span style={{ fontSize: 12, color: 'var(--chalk-3)', whiteSpace: 'nowrap' }}>
                Page {page} of {pages} · {total} jobs
              </span>
              <button
                type="button"
                className="btn-ghost"
                style={{ padding: '8px 16px', fontSize: 12, opacity: page >= pages ? 0.4 : 1 }}
                disabled={page >= pages || loading}
                onClick={() => goPage(page + 1)}
              >
                Next →
              </button>
            </div>
          )}
          <Link to="/applications" className="btn-ghost">Track My Applications →</Link>
        </div>
      )}
    </div>
  )
}
