import { useEffect, useRef, useState } from 'react'
import { useToast } from '../context/ToastContext'
import { post } from '../lib/api'

// Company Prep Pack — free, login-gated. Company + role in, structured pack out:
// round breakdown, top questions with attribution, 4-week study plan, salary band.
export default function Prep() {
  const { toast } = useToast()

  const [query, setQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [showSug, setShowSug] = useState(false)
  const [company, setCompany] = useState(null) // {slug, name, has_rounds, question_count}
  const [role, setRole] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)   // {company, role, pack, salary, cached}
  const [error, setError] = useState('')

  const debounceRef = useRef(null)
  const boxRef = useRef(null)

  // Debounced typeahead against /api/prep/companies
  useEffect(() => {
    if (company) return
    clearTimeout(debounceRef.current)
    const q = query.trim()
    if (q.length < 2) {
      setSuggestions([])
      return
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await post('/api/prep/companies', { query: q })
        setSuggestions(data.companies || [])
        setShowSug(true)
      } catch {
        setSuggestions([])
      }
    }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [query, company])

  // Close dropdown on outside click
  useEffect(() => {
    const h = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setShowSug(false)
    }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])

  const pick = (c) => {
    setCompany(c)
    setQuery(c.name)
    setShowSug(false)
    setSuggestions([])
  }

  const clearCompany = () => {
    setCompany(null)
    setQuery('')
    setResult(null)
  }

  const generate = async (e) => {
    e.preventDefault()
    setError('')
    if (!role.trim()) {
      toast('Enter the role you are preparing for.', 'error')
      return
    }
    if (!company && query.trim()) {
      toast('No match in our list — generating a role-based pack instead.', 'success')
    }
    setLoading(true)
    setResult(null)
    try {
      const data = await post('/api/prep/generate', {
        company_slug: company ? company.slug : '',
        role: role.trim(),
      })
      setResult(data)
      toast(data.cached ? 'Loaded your saved pack.' : 'Prep pack generated.')
    } catch (err) {
      setError(err.message || 'Generation failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const fmtMoney = (n, currency) => {
    if (n == null) return '—'
    try {
      return new Intl.NumberFormat(undefined, {
        style: 'currency',
        currency: currency || 'USD',
        maximumFractionDigits: 0,
        notation: n >= 100000 ? 'compact' : 'standard',
      }).format(n)
    } catch {
      return `${n} ${currency || ''}`.trim()
    }
  }

  const pack = result?.pack
  const salary = result?.salary

  return (
    <div className="container animate-fade-up" style={{ paddingBottom: 64 }}>
      <div style={{ maxWidth: 860, margin: '0 auto' }}>
        <span className="label-signal">FREE · NO CREDITS</span>
        <h1 style={{ margin: '8px 0 6px' }}>Company Prep Pack</h1>
        <p style={{ color: 'var(--muted)', marginTop: 0 }}>
          Pick a company and a role — get the interview round structure, the top
          questions candidates actually face (with sources), a 4-week study plan,
          and a market salary band. <strong>Company not in the list?</strong> Just
          fill the role and generate anyway — you'll get a role-based pack.
        </p>

        {/* ── Input form ─────────────────────────────────────────────── */}
        <form className="card" onSubmit={generate} style={{ marginTop: 18 }}>
          <div ref={boxRef} style={{ position: 'relative' }}>
            <label className="label-signal" htmlFor="prep-company">Company</label>
            {company ? (
              <div
                className="input-field"
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
              >
                <span>
                  {company.name}{' '}
                  <small style={{ color: 'var(--muted)' }}>
                    {company.question_count} questions
                    {company.has_rounds ? ' · round info' : ''}
                  </small>
                </span>
                <button
                  type="button"
                  onClick={clearCompany}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--muted)' }}
                  aria-label="Change company"
                >
                  ✕
                </button>
              </div>
            ) : (
              <>
                <input
                  id="prep-company"
                  className="input-field"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onFocus={() => suggestions.length && setShowSug(true)}
                  placeholder="e.g. Amazon, Google, TCS…"
                  autoComplete="off"
                />
                {showSug && suggestions.length > 0 && (
                  <ul
                    style={{
                      position: 'absolute', zIndex: 20, top: '100%', left: 0, right: 0,
                      margin: '4px 0 0', padding: 6, listStyle: 'none',
                      background: 'var(--bg, #0d1117)', border: '1px solid var(--border, #30363d)',
                      borderRadius: 8, maxHeight: 260, overflowY: 'auto',
                    }}
                  >
                    {suggestions.map((c) => (
                      <li key={c.slug}>
                        <button
                          type="button"
                          onClick={() => pick(c)}
                          style={{
                            display: 'flex', width: '100%', justifyContent: 'space-between',
                            gap: 10, padding: '8px 10px', cursor: 'pointer',
                            background: 'none', border: 'none', color: 'inherit',
                            borderRadius: 6, textAlign: 'left',
                          }}
                        >
                          <span>{c.name}</span>
                          <small style={{ color: 'var(--muted)', whiteSpace: 'nowrap' }}>
                            {c.question_count} Qs{c.has_rounds ? ' · rounds ✓' : ''}
                          </small>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>

          <div style={{ marginTop: 14 }}>
            <label className="label-signal" htmlFor="prep-role">Target role</label>
            <input
              id="prep-role"
              className="input-field"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="e.g. Software Engineer, Data Analyst…"
            />
          </div>

          <button className="btn-signal" type="submit" disabled={loading} style={{ marginTop: 16 }}>
            {loading ? 'Building your pack…' : 'Generate Prep Pack'}
          </button>

          {loading && (
            <p style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 0 }}>
              First pack for a company takes ~10 seconds (we research + cite sources).
              The same pack is cached afterwards, so it loads instantly next time.
            </p>
          )}
          {error && <p style={{ color: '#f85149' }}>{error}</p>}
        </form>

        {/* ── Result ─────────────────────────────────────────────────── */}
        {pack && result && (
          <div className="animate-fade-up" style={{ marginTop: 26 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
              <h2 style={{ margin: 0 }}>
                {result.company ? `${result.company} · ` : ''}{result.role}
              </h2>
              {result.mode === 'role' && (
                <span className="label-signal" style={{ opacity: 0.8 }}>role-based pack</span>
              )}
              {result.cached && (
                <span className="label-signal" style={{ opacity: 0.8 }}>saved pack</span>
              )}
            </div>

            {/* Salary band */}
            {salary && (
              <div className="card" style={{ marginTop: 12 }}>
                <span className="label-signal">Market salary band</span>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 8 }}>
                  {Object.entries(salary).map(([k, b]) => (
                    <div key={k} className="job-card" style={{ flex: '1 1 220px', margin: 0 }}>
                      <strong>{k.toUpperCase()}</strong>
                      <div style={{ fontSize: 20, margin: '4px 0' }}>
                        {fmtMoney(b.min, b.currency)} – {fmtMoney(b.max, b.currency)}
                      </div>
                      <small style={{ color: 'var(--muted)' }}>
                        from {b.sample} live listings
                      </small>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Rounds */}
            {Array.isArray(pack.rounds) && pack.rounds.length > 0 && (
              <div className="card" style={{ marginTop: 14 }}>
                <span className="label-signal">Interview rounds</span>
                <ol style={{ paddingLeft: 20, marginTop: 8 }}>
                  {pack.rounds.map((r, i) => (
                    <li key={i} style={{ marginBottom: 8 }}>
                      <strong>{r.name}</strong>
                      {r.focus && <> — {r.focus}</>}
                      {r.tips && (
                        <div style={{ color: 'var(--muted)', fontSize: 13 }}>💡 {r.tips}</div>
                      )}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* Questions */}
            {Array.isArray(pack.questions) && pack.questions.length > 0 && (
              <div className="card" style={{ marginTop: 14 }}>
                <span className="label-signal">Top {pack.questions.length} likely questions</span>
                <ol style={{ paddingLeft: 20, marginTop: 8 }}>
                  {pack.questions.map((q, i) => (
                    <li key={i} style={{ marginBottom: 10 }}>
                      <span>{q.question}</span>{' '}
                      {q.source === 'corpus' && q.source_url ? (
                        <a
                          href={q.source_url}
                          target="_blank"
                          rel="noreferrer noopener"
                          style={{ fontSize: 12, whiteSpace: 'nowrap' }}
                        >
                          [source ↗]
                        </a>
                      ) : (
                        <span style={{ fontSize: 12, color: 'var(--muted)' }}>[likely]</span>
                      )}
                      {q.category && (
                        <span style={{ fontSize: 12, color: 'var(--muted)' }}> · {q.category}</span>
                      )}
                      {q.why && (
                        <div style={{ color: 'var(--muted)', fontSize: 13 }}>{q.why}</div>
                      )}
                    </li>
                  ))}
                </ol>
                <p style={{ color: 'var(--muted)', fontSize: 12, marginBottom: 0 }}>
                  <strong>source ↗</strong> = question verified in our company question
                  corpus (LeetCode frequency data / InterviewBit).{' '}
                  <strong>[likely]</strong> = synthesized from this company's published
                  interview process.
                </p>
              </div>
            )}

            {/* Study plan */}
            {Array.isArray(pack.study_plan) && pack.study_plan.length > 0 && (
              <div className="card" style={{ marginTop: 14 }}>
                <span className="label-signal">4-week study plan</span>
                <div style={{ display: 'grid', gap: 10, marginTop: 8 }}>
                  {pack.study_plan.map((w, i) => (
                    <div key={i} className="job-card" style={{ margin: 0 }}>
                      <strong>{w.week || `Week ${i + 1}`}</strong>
                      {w.focus && <> — {w.focus}</>}
                      {Array.isArray(w.actions) && (
                        <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
                          {w.actions.map((a, j) => (
                            <li key={j} style={{ fontSize: 14 }}>{a}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tips */}
            {Array.isArray(pack.tips) && pack.tips.length > 0 && (
              <div className="card" style={{ marginTop: 14 }}>
                <span className="label-signal">Interview tips</span>
                <ul style={{ paddingLeft: 20, marginTop: 8 }}>
                  {pack.tips.map((t, i) => (
                    <li key={i} style={{ marginBottom: 4 }}>{t}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
