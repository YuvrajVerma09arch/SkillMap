import { useEffect, useState, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { get, post, postForm } from '../lib/api'

const INDUSTRIES = ['Tech', 'Finance', 'Healthcare', 'Education', 'Manufacturing', 'Retail', 'Other']
const SIZES = ['1-10', '11-50', '51-200', '200-500', '500+']
const EXPERIENCE = ['', '0-1', '1-3', '3-5', '5+']

function Field({ label, children }) {
  return (
    <div>
      <label className="label" style={{ display: 'block', marginBottom: 8 }}>{label}</label>
      {children}
    </div>
  )
}

function SeekerForm({ existing, onSaved }) {
  const { refresh, user } = useAuth()
  const { toast } = useToast()
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    full_name: existing?.full_name || user?.name || '',
    headline: '',
    phone: '',
    location: '',
    experience_years: '',
    qualification: '',
    college: '',
    grad_year: '',
    skills: '',
    project_title: '',
    project_link: '',
    linkedin: '',
    portfolio: '',
  })
  const picRef = useRef(null)
  const resumeRef = useRef(null)

  useEffect(() => {
    if (!existing) return
    setForm((f) => ({
      ...f,
      full_name: existing.full_name || user?.name || '',
      headline: existing.headline || '',
      phone: existing.phone || '',
      location: existing.location || '',
      experience_years: existing.experience_years != null ? String(existing.experience_years) : '',
      skills: (existing.skills || []).join(', '),
      linkedin: existing.linkedin_url || '',
      portfolio: existing.portfolio_url || '',
    }))
  }, [existing, user])

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => fd.append(k, v))
      if (picRef.current?.files?.[0]) fd.append('profile_pic', picRef.current.files[0])
      if (resumeRef.current?.files?.[0]) fd.append('resume', resumeRef.current.files[0])
      await postForm('/api/profile/seeker', fd)
      await refresh()
      toast('Profile saved.')
      onSaved()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <Field label="Full Name *">
        <input type="text" required className="input-field" value={form.full_name} onChange={set('full_name')} placeholder="Jane Doe" />
      </Field>
      <Field label="Headline">
        <input type="text" className="input-field" value={form.headline} onChange={set('headline')} placeholder="e.g. Frontend Developer | React & TypeScript" />
      </Field>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Phone">
          <input type="tel" className="input-field" value={form.phone} onChange={set('phone')} placeholder="+91 98765 43210" />
        </Field>
        <Field label="Location">
          <input type="text" className="input-field" value={form.location} onChange={set('location')} placeholder="Bengaluru, India" />
        </Field>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Years of Experience">
          <select className="input-field" style={{ cursor: 'pointer' }} value={form.experience_years} onChange={set('experience_years')}>
            {EXPERIENCE.map((v) => <option key={v} value={v}>{v || 'Select'}</option>)}
          </select>
        </Field>
        <Field label="Graduation Year">
          <input type="text" className="input-field" value={form.grad_year} onChange={set('grad_year')} placeholder="2023" />
        </Field>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Degree / Qualification">
          <input type="text" className="input-field" value={form.qualification} onChange={set('qualification')} placeholder="B.Tech Computer Science" />
        </Field>
        <Field label="College / University">
          <input type="text" className="input-field" value={form.college} onChange={set('college')} placeholder="IIT Bombay" />
        </Field>
      </div>
      <Field label="Skills (comma-separated)">
        <input type="text" className="input-field" value={form.skills} onChange={set('skills')} placeholder="React, JavaScript, Python, SQL" />
      </Field>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="LinkedIn URL">
          <input type="url" className="input-field" value={form.linkedin} onChange={set('linkedin')} placeholder="https://linkedin.com/in/..." />
        </Field>
        <Field label="Portfolio URL">
          <input type="url" className="input-field" value={form.portfolio} onChange={set('portfolio')} placeholder="https://yoursite.dev" />
        </Field>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Project Title">
          <input type="text" className="input-field" value={form.project_title} onChange={set('project_title')} placeholder="E-commerce platform" />
        </Field>
        <Field label="Project Link">
          <input type="url" className="input-field" value={form.project_link} onChange={set('project_link')} placeholder="https://github.com/..." />
        </Field>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Profile Photo">
          <input type="file" ref={picRef} accept="image/*" className="input-field" style={{ padding: '10px 12px', fontSize: 13 }} />
        </Field>
        <Field label="Resume (PDF)">
          <input type="file" ref={resumeRef} accept=".pdf,.doc,.docx" className="input-field" style={{ padding: '10px 12px', fontSize: 13 }} />
        </Field>
      </div>
      <div style={{ display: 'flex', gap: 12, paddingTop: 8, borderTop: '1px solid var(--wire)', marginTop: 8 }}>
        <button type="submit" className="btn-signal" style={{ padding: '14px 32px' }} disabled={saving}>
          {saving ? 'Saving…' : 'Save Profile →'}
        </button>
      </div>
    </form>
  )
}

function RecruiterForm({ existing, onSaved }) {
  const { refresh, user } = useAuth()
  const { toast } = useToast()
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    company_name: '',
    website: '',
    industry: '',
    size: '',
    location: '',
    recruiter_name: '',
    role_title: '',
    work_email: '',
  })

  useEffect(() => {
    if (!existing) return
    setForm({
      company_name: existing.company_name || '',
      website: existing.website || '',
      industry: existing.industry || '',
      size: existing.company_size || '',
      location: existing.location || '',
      recruiter_name: existing.recruiter_name || user?.name || '',
      role_title: existing.role_title || '',
      work_email: existing.work_email || user?.email || '',
    })
  }, [existing, user])

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await post('/api/profile/recruiter', form)
      await refresh()
      toast('Company profile saved.')
      onSaved()
    } catch (err) {
      toast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      <Field label="Company Name *">
        <input type="text" required className="input-field" value={form.company_name} onChange={set('company_name')} placeholder="e.g. Acme Corporation" />
      </Field>
      <Field label="Website (optional)">
        <input type="url" className="input-field" value={form.website} onChange={set('website')} placeholder="https://example.com" />
      </Field>
      <Field label="Industry">
        <select required className="input-field" style={{ cursor: 'pointer' }} value={form.industry} onChange={set('industry')}>
          <option value="">Select an industry</option>
          {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
        </select>
      </Field>
      <Field label="Company Size">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {SIZES.map((s) => (
            <label key={s} className={`size-chip${form.size === s ? ' selected' : ''}`}>
              <input type="radio" name="size" value={s} checked={form.size === s} onChange={() => setForm((f) => ({ ...f, size: s }))} style={{ display: 'none' }} />
              {s}
            </label>
          ))}
        </div>
      </Field>
      <Field label="Location">
        <input type="text" className="input-field" value={form.location} onChange={set('location')} placeholder="Mumbai, India" />
      </Field>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label="Recruiter Name">
          <input type="text" className="input-field" value={form.recruiter_name} onChange={set('recruiter_name')} placeholder="Your full name" />
        </Field>
        <Field label="Role / Title">
          <input type="text" className="input-field" value={form.role_title} onChange={set('role_title')} placeholder="e.g. Talent Acquisition Lead" />
        </Field>
      </div>
      <Field label="Work Email">
        <input type="email" className="input-field" value={form.work_email} onChange={set('work_email')} placeholder="you@company.com" />
      </Field>
      <div style={{ display: 'flex', gap: 12, paddingTop: 8, borderTop: '1px solid var(--wire)', marginTop: 8 }}>
        <button type="submit" className="btn-signal" style={{ padding: '14px 32px' }} disabled={saving}>
          {saving ? 'Saving…' : 'Save Profile →'}
        </button>
      </div>
    </form>
  )
}

export default function SetupProfile() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [existing, setExisting] = useState(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (loading || !user) return
    const endpoint = user.role === 'seeker' ? '/api/profile/seeker' : '/api/profile/recruiter'
    get(endpoint)
      .then((d) => setExisting(d.profile))
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [user, loading])

  const onSaved = () => {
    navigate(user.role === 'seeker' ? '/profile' : '/dashboard', { replace: true })
  }

  if (!user || !loaded) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '50vh' }}>
        <span className="label-signal animate-blink">● LOADING</span>
      </div>
    )
  }

  const isSeeker = user.role === 'seeker'
  const isFirst = params.get('first') === '1'

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: '60px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ marginBottom: 48 }}>
        <div className="label-signal" style={{ marginBottom: 8 }}>
          {isFirst ? 'Welcome · One-time setup' : 'Profile Setup'}
        </div>
        <h1 className="display" style={{ fontSize: 'clamp(28px,4vw,44px)', color: 'var(--chalk)', marginBottom: 12 }}>
          {isSeeker ? 'Your Profile' : 'Company Profile'}
        </h1>
        <p style={{ fontSize: 13, color: 'var(--chalk-3)', lineHeight: 1.6 }}>
          {isSeeker
            ? 'Complete your profile so AI tools can personalize roadmaps and recruiters can find you.'
            : 'Complete your company profile to help candidates understand your organization and attract top talent.'}
        </p>
      </div>

      <div className="animate-fade-up" style={{ animationDelay: '0.1s' }}>
        {isSeeker ? (
          <SeekerForm existing={existing} onSaved={onSaved} />
        ) : (
          <RecruiterForm existing={existing} onSaved={onSaved} />
        )}
      </div>
    </div>
  )
}
