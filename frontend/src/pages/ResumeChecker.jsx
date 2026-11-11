import { useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { postForm } from '../lib/api'

export default function ResumeChecker() {
  const { user, refresh } = useAuth()
  const { toast } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const fileRef = useRef(null)

  const prefilledJD = location.state?.jobDescription || ''
  const hasSavedResume = Boolean(user && user.has_seeker_profile && user.resume_file)

  const [jobDescription, setJobDescription] = useState(prefilledJD)
  const [useExisting, setUseExisting] = useState(hasSavedResume)
  const [fileName, setFileName] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    if (!useExisting && !fileRef.current?.files?.[0]) {
      toast('Please upload a resume or use your saved one.', 'error')
      return
    }
    setAnalyzing(true)
    setResults(null)
    try {
      const fd = new FormData()
      fd.append('job_description', jobDescription)
      if (useExisting) {
        fd.append('use_existing', '1')
      } else {
        fd.append('resume', fileRef.current.files[0])
      }
      const data = await postForm('/api/tools/resume-check', fd)
      setResults(data.results)
      await refresh()
      toast('Analysis complete.')
    } catch (err) {
      if (err.status === 402 && err.data && err.data.redirect) {
        toast(err.message, 'error')
        navigate(err.data.redirect)
        return
      }
      toast(err.message, 'error')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '48px 24px', position: 'relative', zIndex: 1 }}>
      <div className="animate-fade-up" style={{ marginBottom: 48 }}>
        <div className="label-signal" style={{ marginBottom: 8 }}>Analysis</div>
        <h1 className="display" style={{ fontSize: 'clamp(24px,3vw,40px)', color: 'var(--chalk)' }}>Resume Checker</h1>
        <p style={{ fontSize: 13, color: 'var(--chalk-3)', marginTop: 8 }}>
          Score your resume against a job description. 5 credits per successful analysis — new accounts start with 5 free credits.
          {user && (
            <>
              {' '}· <span style={{ color: 'var(--signal)', fontFamily: "'JetBrains Mono',monospace", fontSize: 11 }}>CREDITS: {user.credits}</span>
            </>
          )}
        </p>
      </div>

      <form onSubmit={submit} className="animate-fade-up" style={{ animationDelay: '0.1s', display: 'flex', flexDirection: 'column', gap: 24 }}>
        <div>
          <label className="label" style={{ display: 'block', marginBottom: 8 }}>Job Description *</label>
          <textarea
            required
            rows={6}
            className="input-field"
            placeholder="Paste the job description you want to match against…"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            style={{ resize: 'vertical', minHeight: 120 }}
          />
        </div>

        {hasSavedResume && (
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, color: 'var(--chalk-2)' }}>
            <input type="checkbox" checked={useExisting} onChange={(e) => setUseExisting(e.target.checked)} style={{ accentColor: 'var(--signal)' }} />
            Use the resume saved on my profile
          </label>
        )}

        {!useExisting && (
          <div
            className="upload-dropzone"
            style={{ border: '2px dashed var(--wire)', padding: 32, textAlign: 'center', cursor: 'pointer', transition: 'all 0.2s' }}
            onClick={() => fileRef.current?.click()}
            onMouseOver={(e) => { e.currentTarget.style.borderColor = 'var(--signal)' }}
            onMouseOut={(e) => { e.currentTarget.style.borderColor = 'var(--wire)' }}
          >
            <i className="bi bi-cloud-upload" style={{ fontSize: 32, color: 'var(--chalk-3)', marginBottom: 12, display: 'block' }}></i>
            <p style={{ fontSize: 13, color: 'var(--chalk-2)', margin: 0 }}>
              {fileName || 'Click to upload resume or drag & drop'}
            </p>
            <input
              type="file"
              ref={fileRef}
              accept=".pdf,.doc,.docx"
              style={{ display: 'none' }}
              onChange={(e) => setFileName(e.target.files?.[0]?.name || '')}
            />
          </div>
        )}

        <div>
          <button type="submit" className="btn-signal" style={{ padding: '14px 32px' }} disabled={analyzing}>
            {analyzing ? 'Analyzing…' : 'Analyze Resume →'}
          </button>
        </div>
      </form>

      {results && (
        <div className="animate-fade-up" style={{ marginTop: 48 }}>
          <div className="section-label" style={{ marginBottom: 20 }}>
            <span className="label-signal">Result</span>
          </div>

          <div className="card" style={{ padding: 32, display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div>
              <div className="label" style={{ marginBottom: 10 }}>Match Score</div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontFamily: "'Space Grotesk',sans-serif", fontSize: 48, fontWeight: 700, color: 'var(--signal)', letterSpacing: '-0.03em' }}>
                  {results.match_score}
                </span>
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 14, color: 'var(--chalk-3)' }}>/ 100</span>
              </div>
              <div style={{ height: 4, background: 'var(--ink-3)', marginTop: 12, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${results.match_score}%`, background: 'var(--signal)', transition: 'width 0.6s' }}></div>
              </div>
            </div>

            {Array.isArray(results.missing_required_skills) && results.missing_required_skills.length > 0 && (
              <div>
                <div className="label" style={{ marginBottom: 10 }}>Missing / Flagged Skills</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {results.missing_required_skills.map((s, i) => (
                    <span key={i} className="skill-badge">{s}</span>
                  ))}
                </div>
              </div>
            )}

            {Array.isArray(results.explanation) && results.explanation.length > 0 && (
              <div>
                <div className="label" style={{ marginBottom: 10 }}>Explanation</div>
                <ul style={{ display: 'flex', flexDirection: 'column', gap: 8, listStyle: 'none', padding: 0, margin: 0 }}>
                  {results.explanation.map((line, i) => (
                    <li key={i} style={{ fontSize: 13, color: 'var(--chalk-2)', lineHeight: 1.6, paddingLeft: 16, position: 'relative' }}>
                      <span style={{ position: 'absolute', left: 0, color: 'var(--signal)' }}>—</span>
                      {line}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
