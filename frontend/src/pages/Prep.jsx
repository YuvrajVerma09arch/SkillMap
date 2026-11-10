import { useEffect, useState } from 'react'
import { post } from '../lib/api'
import CompanyCombobox from '../components/prep/CompanyCombobox'
import PrepResult from '../components/prep/PrepResult'

// Company Prep Pack — free, login-gated. Company (optional) + role in,
// structured pack out: round breakdown, 12 sourced questions, 4-week study
// plan, salary bands. No company = role-only pack across the whole corpus.

const ROLE_CHIPS = [
  'Software Engineer',
  'Frontend Engineer',
  'Backend Engineer',
  'Full Stack Developer',
  'Data Analyst',
  'Data Scientist',
  'Machine Learning Engineer',
  'Product Manager',
  'DevOps Engineer',
  'QA Engineer',
]

// First build for an uncached pack takes ~68s (embedding model + Groq);
// cached packs return in ~1.2s. Stage copy tracks elapsed seconds.
const STAGES = [
  [3, 'Checking pack cache'],
  [14, 'Retrieving corpus matches'],
  [35, 'Synthesizing rounds & questions'],
  [55, 'Building the 4-week study plan'],
  [Infinity, 'Finalizing pack'],
]

export default function Prep() {
  const [company, setCompany] = useState(null) // {slug, name, has_rounds, question_count}
  const [role, setRole] = useState('')
  const [loading, setLoading] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [result, setResult] = useState(null) // {company, role, mode, pack, salary, cached}
  const [error, setError] = useState('')

  // Elapsed-seconds ticker while a pack is generating.
  useEffect(() => {
    if (!loading) return undefined
    const t = setInterval(() => setElapsed((e) => e + 1), 1000)
    return () => clearInterval(t)
  }, [loading])

  const generate = async (e) => {
    e.preventDefault()
    const r = role.trim()
    if (!r) {
      setError('Pick a role to prep for.')
      return
    }
    setError('')
    setResult(null)
    setElapsed(0)
    setLoading(true)
    try {
      const data = await post('/api/prep/generate', {
        company_slug: company ? company.slug : '',
        role: r,
      })
      setResult(data)
    } catch (err) {
      setError(
        err.status === 429
          ? 'Rate limited — wait a few seconds and try again.'
          : err.message || 'Pack generation failed. Try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setResult(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const stage = (STAGES.find(([sec]) => elapsed < sec) || STAGES[STAGES.length - 1])[1]
  const progress = Math.min(96, (elapsed / 70) * 100)
  const mmss = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, '0')}`
  const roleLower = role.trim().toLowerCase()

  return (
    <div className="prep-page">
      <div className="animate-fade-up" style={{ marginBottom: 32 }}>
        <div className="label-signal" style={{ marginBottom: 8 }}>
          Prep // Free
        </div>
        <h1 className="display" style={{ fontSize: 'clamp(24px,3vw,40px)', color: 'var(--chalk)' }}>
          Company Prep Pack
        </h1>
        <p style={{ fontSize: 13, color: 'var(--chalk-3)', marginTop: 8, maxWidth: 640 }}>
          Round breakdown, 12 sourced questions, a 4-week study plan and live salary bands —
          built from 432 companies' real interview data. No credits, no card.
        </p>
      </div>

      <form
        className="card prep-form animate-fade-up"
        style={{ animationDelay: '0.05s' }}
        onSubmit={generate}
        aria-busy={loading}
      >
        <div className="prep-field">
          <label className="prep-label" htmlFor="prep-company">
            Company <span>— optional</span>
          </label>
          <CompanyCombobox value={company} onChange={setCompany} disabled={loading} />
          <p className="prep-help">Leave blank to build a role-only pack across the whole corpus.</p>
        </div>

        <div className="prep-field">
          <label className="prep-label" htmlFor="prep-role">
            Role <span>— required</span>
          </label>
          <input
            id="prep-role"
            type="text"
            className="input-field"
            disabled={loading}
            placeholder="e.g. Software Engineer"
            value={role}
            maxLength={80}
            onChange={(e) => setRole(e.target.value)}
          />
          <div className="prep-chips" role="group" aria-label="Quick-pick roles">
            {ROLE_CHIPS.map((r) => {
              const selected = roleLower === r.toLowerCase()
              return (
                <button
                  type="button"
                  key={r}
                  disabled={loading}
                  aria-pressed={selected}
                  className={`skill-chip${selected ? ' selected' : ''}`}
                  onClick={() => setRole(r)}
                >
                  {r}
                </button>
              )
            })}
          </div>
        </div>

        <p className="prep-hint">
          <span aria-hidden="true">&gt;</span> {company ? company.name : 'any company'}
          {' × '}
          {role.trim() || '…'} →{' '}
          <strong>{company ? 'company pack' : 'role pack · whole corpus'}</strong>
        </p>

        {error && (
          <div className="prep-error" role="alert">
            <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
            <span>{error}</span>
            <button type="button" onClick={() => setError('')} aria-label="Dismiss error">
              <i className="bi bi-x-lg" aria-hidden="true" />
            </button>
          </div>
        )}

        <div className="prep-actions">
          <button type="submit" className="btn-signal" disabled={loading}>
            {loading ? (
              <>
                <span className="prep-btn-spin" aria-hidden="true" />
                Generating…
              </>
            ) : (
              <>
                <i className="bi bi-lightning-charge-fill" aria-hidden="true" />
                Build prep pack
              </>
            )}
          </button>
          <span className="prep-actions-note">
            free · zero credits · first build ~60s, then instant
          </span>
        </div>
      </form>

      {loading && (
        <div className="card prep-loading animate-fade-up" role="status" aria-live="polite">
          <div className="prep-loading-row">
            <span className="prep-scan" aria-hidden="true" />
            <div className="prep-loading-copy">
              <div className="label-signal">{stage}</div>
              <p className="prep-help">
                {elapsed < 3
                  ? 'Cached packs return in about a second.'
                  : 'First build for this pack downloads the embedding model — ~60s total.'}
              </p>
            </div>
            <span className="prep-timer" aria-label={`${elapsed} seconds elapsed`}>
              {mmss}
            </span>
          </div>
          <div className="prep-progress" aria-hidden="true">
            <span style={{ width: `${progress}%` }} />
          </div>
        </div>
      )}

      {!loading && result && <PrepResult result={result} onReset={reset} />}
    </div>
  )
}
