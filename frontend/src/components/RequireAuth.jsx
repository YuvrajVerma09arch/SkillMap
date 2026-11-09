import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function FullPageLoader() {
  return (
    <div className="flex items-center justify-center" style={{ minHeight: '60vh' }}>
      <span className="label-signal animate-blink">● LOADING</span>
    </div>
  )
}

export default function RequireAuth({ role, needsProfile = false, children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageLoader />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (role && user.role !== role) return <Navigate to="/" replace />
  if (needsProfile) {
    const hasProfile = user.role === 'seeker' ? user.has_seeker_profile : user.has_recruiter_profile
    if (!hasProfile) return <Navigate to="/setup-profile" replace />
  }
  return children
}
