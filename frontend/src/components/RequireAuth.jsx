import { useEffect, useState } from 'react'
import { Outlet, Navigate } from 'react-router-dom'
import { getCurrentUser } from 'aws-amplify/auth'

export default function RequireAuth() {
  const [state, setState] = useState('checking')
  useEffect(() => {
    getCurrentUser().then(() => setState('ok')).catch(() => setState('no'))
  }, [])
  if (state === 'checking') return <div className="card">Loading…</div>
  if (state === 'no') return <Navigate to="/login" replace />
  return <Outlet />
}
