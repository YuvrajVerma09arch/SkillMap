import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { post } from '../lib/api'

export default function Roadmap() {
  const { refresh, user } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()

  const [form, setForm] = useState({ current_skills: '', target_role: '' })
  const [loading, setLoading] = useState(false)
  const [roadmap, setRoadmap] = useState(null)
  const [targetRole, setTargetRole] = useState('')
  const [emailing, setEmailing] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const data = await post('/api/tools/roadmap', form)
      setRoadmap(data.roadmap)
      setTargetRole(data.target_role)
      await refresh()
      toast('Roadmap generated.')
    } catch (err) {
      if (err.status === 402 && err.data && err.data.redirect) {
        toast(err.message, 'error')
        navigate(err.data.redirect)
        return
      }
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const emailRoadmap = async () => {
    setEmailing(true)
    try {
      const data = await post('/api/emails/roadmap')
      if (data.sent) toast(`Roadmap sent to ${data.email}.`)
      else toast('Could not send email.', 'error')
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setEmailing(false)
    }
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ marginBottom: 48 }}>
        <div className="label-signal" style={{ marginBottom: 8 }}>Career Path</div>
        <h1 className="display" style={{ fontSize: 'clamp(24px,3vw,40px)', color: 'var(--chalk)' }}>Your Roadmap</h1>
        <p style={{ fontSize: 13, color: 'var(--chalk-3)', marginTop: 8 }}>
          Tell us where you are and where you want to go. The AI builds a month-by-month plan. 1 credit per generation.
          {user && (
            <>
              {' '}· <span style={{ color: 'var(--signal)', fontFamily: "'JetBrains Mono',monospace", fontSize: 11 }}>CREDITS: {user.credits}</span>
            </>
          )}
        </p>
      </div>

      <form onSubmit={submit} className="animate-fade-up card" style={{ animationDelay: '0.05s', padding: 32, marginBottom: 40, display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div>
          <label className="label" style={{ display: 'block', marginBottom: 8 }}>Current Skills *</label>
          <input
            type="text"
            required
            className="input-field"
            placeholder="e.g. Python, SQL, basic JavaScript"
            value={form.current_skills}
            onChange={(e) => setForm((f) => ({ ...f, current_skills: e.target.value }))}
          />
        </div>
        <div>
          <label className="label" style={{ display: 'block', marginBottom: 8 }}>Target Role *</label>
          <input
            type="text"
            required
            className="input-field"
            placeholder="e.g. Full-Stack Developer"
            value={form.target_role}
            onChange={(e) => setForm((f) => ({ ...f, target_role: e.target.value }))}
          />
        </div>
        <div>
          <button type="submit" className="btn-signal" style={{ padding: '14px 32px' }} disabled={loading}>
            {loading ? 'Generating…' : 'Generate Roadmap →'}
          </button>
        </div>
      </form>

      {roadmap && (
        <div className="animate-fade-up">
          <div className="section-label" style={{ marginBottom: 24 }}>
            <span className="label-signal">Plan · {targetRole}</span>
            <button type="button" className="btn-ghost" style={{ padding: '7px 14px', fontSize: 12 }} onClick={emailRoadmap} disabled={emailing}>
              <i className="bi bi-envelope" style={{ marginRight: 6 }}></i>
              {emailing ? 'Sending…' : 'Email Me This Plan'}
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 2, background: 'var(--wire)' }}>
            {roadmap.map((step, i) => (
              <div key={i} className="job-card" style={{ animationDelay: `${i * 0.05}s` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                  <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, background: 'var(--signal-dim)', color: 'var(--signal)', padding: '3px 8px', letterSpacing: '0.05em' }}>
                    {(step.month || `Step ${i + 1}`).toUpperCase()}
                  </span>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--chalk)', margin: 0 }}>{step.topic}</h3>
                </div>
                {step.description && (
                  <p style={{ fontSize: 13, color: 'var(--chalk-2)', lineHeight: 1.6, margin: 0 }}>{step.description}</p>
                )}
                {Array.isArray(step.action_items) && step.action_items.length > 0 && (
                  <ul style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingLeft: 0, listStyle: 'none', margin: 0 }}>
                    {step.action_items.map((item, j) => (
                      <li key={j} style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.6, paddingLeft: 16, position: 'relative' }}>
                        <span style={{ position: 'absolute', left: 0, color: 'var(--signal)' }}>—</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>

          <div style={{ marginTop: 24, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <Link to="/profile" className="btn-ghost">Review My Skills →</Link>
            <Link to="/prep" className="btn-ghost">Company Prep Pack →</Link>
          </div>
        </div>
      )}
    </div>
  )
}
