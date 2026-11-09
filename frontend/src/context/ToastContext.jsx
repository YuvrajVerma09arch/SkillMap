import { createContext, useContext, useState, useCallback, useRef } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const idRef = useRef(0)

  const dismiss = useCallback((id) => {
    setToasts((t) => t.filter((x) => x.id !== id))
  }, [])

  const toast = useCallback((message, type = 'success') => {
    const id = ++idRef.current
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => dismiss(id), 4000)
  }, [dismiss])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed top-16 right-4 flex flex-col gap-2 max-w-xs w-full" style={{ zIndex: 500 }}>
        {toasts.map((t) => (
          <div key={t.id} className="flash-msg flex items-center justify-between gap-3 animate-fade-up">
            <div className="flex items-center gap-2">
              <span
                className="animate-blink"
                style={{ color: t.type === 'error' ? 'var(--signal)' : '#4ade80', fontSize: '8px' }}
              >
                ●
              </span>
              <p style={{ fontSize: '13px', color: 'var(--chalk)' }}>{t.message}</p>
            </div>
            <button
              onClick={() => dismiss(t.id)}
              style={{ color: 'var(--chalk-3)', background: 'none', border: 'none', cursor: 'pointer', fontSize: '14px', padding: 0 }}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
