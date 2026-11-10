import { useEffect, useRef, useState } from 'react'

const SALARY_LABELS = { in: 'India', us: 'United States' }

function money(n, currency) {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currency || 'USD',
      maximumFractionDigits: 0,
    }).format(n)
  } catch {
    return `${n}`
  }
}

// Renders a generated prep pack: sticky section jump-nav (with scroll spy),
// numbered round stepper, sourced question rows, week-by-week timeline,
// tips and live salary bands.
export default function PrepResult({ result, onReset }) {
  const headRef = useRef(null)
  const [activeSec, setActiveSec] = useState('')

  const { company, role, mode, pack = {}, salary, cached } = result || {}
  const rounds = Array.isArray(pack.rounds) ? pack.rounds : []
  const questions = Array.isArray(pack.questions) ? pack.questions : []
  const plan = Array.isArray(pack.study_plan) ? pack.study_plan : []
  const tips = Array.isArray(pack.tips) ? pack.tips : []
  const bands =
    salary && typeof salary === 'object'
      ? Object.entries(salary).filter(([, v]) => v && v.min && v.max)
      : []

  const sections = [
    rounds.length && { id: 'prep-rounds', label: 'Rounds' },
    questions.length && { id: 'prep-questions', label: 'Questions' },
    plan.length && { id: 'prep-plan', label: 'Study plan' },
    tips.length && { id: 'prep-tips', label: 'Tips' },
    bands.length && { id: 'prep-salary', label: 'Salary' },
  ].filter(Boolean)

  // Focus the heading so screen-reader / keyboard users land on the result.
  useEffect(() => {
    headRef.current?.focus()
  }, [])

  // Scroll spy for the sticky jump-nav.
  useEffect(() => {
    const els = sections.map((s) => document.getElementById(s.id)).filter(Boolean)
    if (!els.length) return undefined
    setActiveSec(els[0].id)
    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        if (visible[0]) setActiveSec(visible[0].target.id)
      },
      { rootMargin: '-140px 0px -55% 0px', threshold: 0 }
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result])

  return (
    <section className="prep-result animate-fade-up" aria-label="Your prep pack">
      <div className="prep-result-head">
        <div>
          <span className="label-signal">
            {mode === 'role' ? 'Role pack · any company' : 'Company pack'}
          </span>
          <h2 className="display prep-result-title" tabIndex={-1} ref={headRef}>
            {role}
          </h2>
          <p className="prep-result-sub">
            {company || 'Any company'} · {questions.length} questions ·{' '}
            {rounds.length} rounds · {plan.length}-week plan
          </p>
          <div className="prep-badges">
            <span className={`prep-badge${mode === 'role' ? ' signal' : ''}`}>
              {mode === 'role' ? 'whole-corpus search' : 'company corpus'}
            </span>
            <span className={`prep-badge${cached ? '' : ' fresh'}`}>
              {cached ? 'instant · cached' : 'freshly generated'}
            </span>
          </div>
        </div>
        <button type="button" className="btn-ghost" onClick={onReset}>
          <i className="bi bi-arrow-left-right" aria-hidden="true" />
          New pack
        </button>
      </div>

      {sections.length === 0 && (
        <div className="prep-error" role="alert">
          <i className="bi bi-exclamation-triangle-fill" aria-hidden="true" />
          <span>The model returned an empty pack. Try generating again.</span>
        </div>
      )}

      {sections.length > 1 && (
        <nav className="prep-jump" aria-label="Pack sections">
          {sections.map((s) => (
            <a
              key={s.id}
              href={`#${s.id}`}
              className={`feed-tab${activeSec === s.id ? ' active' : ''}`}
            >
              {s.label}
            </a>
          ))}
        </nav>
      )}

      {rounds.length > 0 && (
        <section id="prep-rounds" className="prep-sec">
          <h3 className="prep-sec-title">Interview rounds</h3>
          <ol className="prep-stepper">
            {rounds.map((r, i) => (
              <li className="prep-step" key={`${r.name}-${i}`}>
                <span className="prep-step-n" aria-hidden="true">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <div className="prep-step-body">
                  <h4 className="prep-step-name">{r.name}</h4>
                  {r.focus && <p className="prep-step-focus">{r.focus}</p>}
                  {r.tips && (
                    <p className="prep-step-tips">
                      <i className="bi bi-bookmark-star" aria-hidden="true" />
                      {r.tips}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {questions.length > 0 && (
        <section id="prep-questions" className="prep-sec">
          <h3 className="prep-sec-title">Top questions ({questions.length})</h3>
          <ol className="prep-qlist">
            {questions.map((q, i) => (
              <li className="prep-q" key={`${q.question}-${i}`}>
                <span className="prep-q-idx" aria-hidden="true">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <div className="prep-q-body">
                  <p className="prep-q-text">{q.question}</p>
                  {q.why && (
                    <p className="prep-q-why">
                      <i className="bi bi-lightning-charge-fill" aria-hidden="true" />
                      <span>{q.why}</span>
                    </p>
                  )}
                  <div className="prep-q-tags">
                    {q.category && <span className="skill-tag">{q.category}</span>}
                    {q.source === 'corpus' ? (
                      q.source_url ? (
                        <a
                          className="prep-src prep-src-corpus"
                          href={q.source_url}
                          target="_blank"
                          rel="noreferrer noopener"
                          title="Copied verbatim from the scraped corpus — opens the original source"
                        >
                          <i className="bi bi-patch-check-fill" aria-hidden="true" />
                          verified
                          <i className="bi bi-box-arrow-up-right" aria-hidden="true" />
                        </a>
                      ) : (
                        <span
                          className="prep-src prep-src-corpus"
                          title="Copied verbatim from the scraped corpus"
                        >
                          <i className="bi bi-patch-check-fill" aria-hidden="true" />
                          verified
                        </span>
                      )
                    ) : (
                      <span
                        className="prep-src prep-src-synth"
                        title="Typical question synthesized by the model for this pack"
                      >
                        <i className="bi bi-stars" aria-hidden="true" />
                        likely
                      </span>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {plan.length > 0 && (
        <section id="prep-plan" className="prep-sec">
          <h3 className="prep-sec-title">{plan.length}-week study plan</h3>
          <ol className="prep-timeline">
            {plan.map((w, i) => (
              <li className="prep-tl-item" key={`${w.week}-${i}`}>
                <span className="prep-tl-dot" aria-hidden="true" />
                <div className="prep-tl-body">
                  <span className="prep-tl-week">{w.week}</span>
                  <h4 className="prep-tl-focus">{w.focus}</h4>
                  {Array.isArray(w.actions) && w.actions.length > 0 && (
                    <ul className="prep-tl-actions">
                      {w.actions.map((a, j) => (
                        <li key={j}>{a}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      {tips.length > 0 && (
        <section id="prep-tips" className="prep-sec">
          <h3 className="prep-sec-title">Interview tips</h3>
          <ul className="prep-tips">
            {tips.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </section>
      )}

      {bands.length > 0 && (
        <section id="prep-salary" className="prep-sec">
          <h3 className="prep-sec-title">Salary band · {role}</h3>
          <div className="prep-salary-grid">
            {bands.map(([k, v]) => (
              <div className="prep-salary-tile" key={k}>
                <div className="prep-salary-country">{SALARY_LABELS[k] || k.toUpperCase()}</div>
                <div className="prep-salary-range">
                  {money(v.min, v.currency)} – {money(v.max, v.currency)}
                </div>
                <div className="prep-salary-note">sampled from {v.sample} live listings</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <p className="prep-note">
        <i className="bi bi-info-circle" aria-hidden="true" /> Questions marked{' '}
        <strong>verified</strong> are copied from scraped LeetCode company lists and
        InterviewBit; <strong>likely</strong> questions are model-generated and typical
        for this {mode === 'role' ? 'role' : 'company'}. Salary bands come from live
        Adzuna listings.
      </p>
    </section>
  )
}
