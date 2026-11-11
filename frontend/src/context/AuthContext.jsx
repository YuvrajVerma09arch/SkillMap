import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { get, post } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const data = await get('/api/auth/me')
      setUser(data.authenticated ? data.user : null)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const login = useCallback(async (email, password) => {
    const data = await post('/api/auth/login', { email, password })
    setUser(data.user)
    return data.user
  }, [])

  const register = useCallback(async ({ username, email, password, role }) => {
    // F4: register no longer logs you in (and returns the same response whether
    // or not the email already existed), so we just surface the message.
    const data = await post('/api/auth/register', { username, email, password, role })
    return data.message || 'If this email is new, your account has been created. Please sign in to continue.'
  }, [])

  const logout = useCallback(async () => {
    await post('/api/auth/logout')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, setUser, loading, refresh, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
