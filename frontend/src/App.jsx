import { Outlet, Link, useNavigate } from 'react-router-dom'
import { signOut } from 'aws-amplify/auth'
import { useEffect, useState } from 'react'
import { getCurrentUser } from 'aws-amplify/auth'

export default function App() {
  const [email, setEmail] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    getCurrentUser()
      .then(u => setEmail(u.signInDetails?.loginId || u.username))
      .catch(() => setEmail(null))
  }, [])

  return (
    <div className="shell">
      <header>
        <Link to="/dashboard" className="brand">FinPlanner</Link>
        <nav>
          {email ? (
            <>
              <span className="muted">{email}</span>
              <button onClick={async () => { await signOut(); navigate('/login') }}>
                Sign out
              </button>
            </>
          ) : (
            <Link to="/login">Sign in</Link>
          )}
        </nav>
      </header>
      <main><Outlet /></main>
    </div>
  )
}
