import { useEffect, useRef, useState } from 'react'
import { post } from '../../lib/api'

// Company typeahead for the Prep page — ARIA 1.2 combobox pattern:
// the input owns aria-expanded/aria-controls/aria-activedescendant and the
// listbox lives next to it. Keys: ↓/↑ move, Enter picks, Esc closes.
// Picking a company swaps the field for a locked chip with a Change button.
export default function CompanyCombobox({ value, onChange, disabled }) {
  const [query, setQuery] = useState('')
  const [items, setItems] = useState([])
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [searching, setSearching] = useState(false)

  const debounceRef = useRef(null)
  const seqRef = useRef(0)
  const wrapRef = useRef(null)
  const listId = 'prep-company-listbox'

  // Debounced search against /api/prep/companies (2 chars minimum).
  useEffect(() => {
    const seq = ++seqRef.current
    if (value) return undefined
    clearTimeout(debounceRef.current)
    const q = query.trim()
    if (q.length < 2) {
      setItems([])
      setOpen(false)
      setSearching(false)
      return undefined
    }
    setSearching(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await post('/api/prep/companies', { query: q })
        if (seq !== seqRef.current) return // stale response
        setItems(data.companies || [])
        setActive(-1)
        setOpen(true)
      } catch {
        if (seq === seqRef.current) setItems([])
      } finally {
        if (seq === seqRef.current) setSearching(false)
      }
    }, 250)
    return () => clearTimeout(debounceRef.current)
  }, [query, value])

  // Close when clicking outside the field.
  useEffect(() => {
    const onDown = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [])

  if (value) {
    return (
      <div className="prep-selected" ref={wrapRef}>
        <i className="bi bi-buildings-fill prep-selected-icon" aria-hidden="true" />
        <span className="prep-selected-body">
          <strong>{value.name}</strong>
          <span className="prep-selected-meta">
            {value.has_rounds ? 'round structure on file' : 'questions only'}
            {' · '}
            {value.question_count} questions
          </span>
        </span>
        <button
          type="button"
          className="btn-ghost prep-selected-change"
          onClick={() => {
            onChange(null)
            setQuery('')
            setItems([])
            setOpen(false)
          }}
          aria-label={`Change company (currently ${value.name})`}
        >
          <i className="bi bi-pencil" aria-hidden="true" />
          Change
        </button>
      </div>
    )
  }

  const choose = (c) => {
    onChange(c)
    setQuery('')
    setItems([])
    setOpen(false)
    setActive(-1)
  }

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (!items.length) return
      setOpen(true)
      setActive((a) => (a + 1) % items.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (!items.length) return
      setActive((a) => (a <= 0 ? items.length - 1 : a - 1))
    } else if (e.key === 'Enter') {
      if (open && active >= 0 && items[active]) {
        e.preventDefault()
        choose(items[active])
      }
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  const showList = open && (searching || items.length > 0)
  const showEmpty = open && !searching && items.length === 0 && query.trim().length >= 2

  return (
    <div className="prep-combo" ref={wrapRef}>
      <input
        id="prep-company"
        type="text"
        className="input-field"
        role="combobox"
        autoComplete="off"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={
          showList && active >= 0 && items[active] ? `prep-sug-${active}` : undefined
        }
        placeholder="Search 432 companies — or leave blank for role-only"
        value={query}
        disabled={disabled}
        onChange={(e) => {
          setQuery(e.target.value)
          if (!e.target.value.trim()) setOpen(false)
        }}
        onFocus={() => {
          if (items.length) setOpen(true)
        }}
        onKeyDown={onKeyDown}
      />

      {showList && (
        <ul className="prep-sug" role="listbox" id={listId} aria-label="Company suggestions">
          {searching && items.length === 0 && (
            <li className="prep-sug-empty" role="presentation">
              searching…
            </li>
          )}
          {items.map((c, i) => (
            <li
              key={c.slug}
              id={`prep-sug-${i}`}
              role="option"
              aria-selected={i === active}
              className={`prep-sug-item${i === active ? ' active' : ''}`}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => {
                e.preventDefault() // keep focus in the input
                choose(c)
              }}
            >
              <span className="prep-sug-name">{c.name}</span>
              <span className="prep-sug-meta">
                {c.has_rounds && (
                  <i className="bi bi-check-circle-fill" title="Round structure on file" />
                )}
                {c.question_count} Q
              </span>
            </li>
          ))}
        </ul>
      )}

      {showEmpty && (
        <div className="prep-sug prep-sug-wrap-empty">
          <p className="prep-sug-empty">
            No match — leave the field blank to build a role-only pack instead.
          </p>
        </div>
      )}
    </div>
  )
}
