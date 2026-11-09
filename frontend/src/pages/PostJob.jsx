import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useToast } from '../context/ToastContext'
import { post } from '../lib/api'

const SKILL_CHIPS = ['Python', 'Java', 'C++', 'JavaScript', 'React', 'Node.js', 'SQL', 'AWS', 'Docker', 'Git', 'Flutter', 'HTML/CSS']

function Field({ label, children, hint }) {
  return (
    <div>
      <label className="label" style={{ display: 'block', marginBottom: 8 }}>{label}</label>
      {children}
      {hint && <p style={{ fontSize: 11, color: 'var(--chalk-3)', fontFamily: "'JetBrains Mono',monospace", marginTop: 6 }}>{hint}</p>}
    </div>
  )
}

export default function PostJob() {
  const { toast } = useToast()
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)
  const [selected, setSelected] = useState([])
  const [form, setForm] = useState({
    title: '',
    location: '',
    job_type: 'On-Site',
    salary_range: '',
    experience_required: '0-1 Years',
    description: '',
    responsibilities: '',
    nice_to_have: '',
    benefits: '',
  })

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const toggleSkill = (skill) => {
    setSelected((s) => (s.includes(skill) ? s.filter((x) => x !== skill) : [...s, skill]))
  }

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await post('/api/recruiter/jobs', {
        ...form,
        required_skills: selected,
      })
      toast('Job published.')
      navigate('/dashboard')
    } catch (err) {
      if (err.status === 403 && err.data && err.data.redirect) {
        toast(err.message, 'error')
        navigate(err.data.redirect)
        return
      }
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '60px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ marginBottom: 48 }}>
        <Link to="/dashboard" style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: 'var(--chalk-3)', textDecoration: 'none', letterSpacing: '0.05em', display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 20 }}>
          ← Dashboard
        </Link>
        <div className="label-signal" style={{ marginBottom: 8 }}>New Posting</div>
        <h1 className="display" style={{ fontSize: 'clamp(28px,4vw,44px)', color: 'var(--chalk)' }}>Post a Job</h1>
      </div>

      <form onSubmit={submit} className="animate-fade-up" style={{ animationDelay: '0.1s' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <Field label="Job Title">
            <input type="text" required placeholder="e.g. Senior Backend Engineer" className="input-field" value={form.title} onChange={set('title')} />
          </Field>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Location">
              <input type="text" required placeholder="e.g. Bangalore / Remote" className="input-field" value={form.location} onChange={set('location')} />
            </Field>
            <Field label="Work Type">
              <select name="job_type" className="input-field" style={{ cursor: 'pointer' }} value={form.job_type} onChange={set('job_type')}>
                <option value="On-Site">On-Site</option>
                <option value="Remote">Remote</option>
                <option value="Hybrid">Hybrid</option>
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Salary Range">
              <input type="text" placeholder="e.g. ₹8L – ₹12L PA" className="input-field" value={form.salary_range} onChange={set('salary_range')} />
            </Field>
            <Field label="Experience Required">
              <select className="input-field" style={{ cursor: 'pointer' }} value={form.experience_required} onChange={set('experience_required')}>
                <option value="0-1 Years">Fresher (0–1 Years)</option>
                <option value="1-3 Years">Junior (1–3 Years)</option>
                <option value="3-5 Years">Mid-Level (3–5 Years)</option>
                <option value="5+ Years">Senior (5+ Years)</option>
              </select>
            </Field>
          </div>

          <Field label="Job Description">
            <textarea required rows={4} placeholder="Brief overview of the role and what you're looking for..." className="input-field" value={form.description} onChange={set('description')} />
          </Field>

          <Field label="Key Responsibilities" hint="Enter each point on a new line.">
            <textarea rows={4} placeholder={'• Design and maintain APIs\n• Collaborate with cross-functional teams\n• Write clean, testable code'} className="input-field" value={form.responsibilities} onChange={set('responsibilities')} />
          </Field>

          <Field label="Required Skills" hint="Click to select required skills for smart candidate matching.">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
              {SKILL_CHIPS.map((skill) => (
                <label key={skill} className={`skill-chip${selected.includes(skill) ? ' selected' : ''}`} onClick={() => toggleSkill(skill)}>
                  <input type="checkbox" checked={selected.includes(skill)} readOnly style={{ display: 'none' }} />
                  {skill}
                </label>
              ))}
            </div>
          </Field>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Nice to Have (optional)">
              <textarea rows={2} placeholder="e.g. AWS, Docker, Kubernetes" className="input-field" value={form.nice_to_have} onChange={set('nice_to_have')} />
            </Field>
            <Field label="Benefits (optional)">
              <textarea rows={2} placeholder="e.g. Health insurance, flexible hours" className="input-field" value={form.benefits} onChange={set('benefits')} />
            </Field>
          </div>

          <div style={{ display: 'flex', gap: 12, paddingTop: 8, borderTop: '1px solid var(--wire)', marginTop: 8 }}>
            <button type="submit" className="btn-signal" style={{ padding: '14px 32px' }} disabled={saving}>
              {saving ? 'Publishing…' : 'Publish Job →'}
            </button>
            <Link to="/dashboard" className="btn-ghost" style={{ padding: '14px 24px', textDecoration: 'none' }}>Cancel</Link>
          </div>
        </div>
      </form>
    </div>
  )
}
