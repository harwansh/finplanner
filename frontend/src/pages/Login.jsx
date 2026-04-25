import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { signIn, signUp, confirmSignUp } from 'aws-amplify/auth'

export default function Login() {
  const [mode, setMode] = useState('signin') // signin | signup | confirm
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setErr(''); setBusy(true)
    try {
      if (mode === 'signin') {
        await signIn({ username: email, password })
        navigate('/dashboard')
      } else if (mode === 'signup') {
        await signUp({
          username: email,
          password,
          options: { userAttributes: { email } }
        })
        setMode('confirm')
      } else {
        await confirmSignUp({ username: email, confirmationCode: code })
        await signIn({ username: email, password })
        navigate('/onboarding')
      }
    } catch (e) {
      setErr(e.message || String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card narrow">
      <h2>
        {mode === 'signin' && 'Sign in'}
        {mode === 'signup' && 'Create account'}
        {mode === 'confirm' && 'Confirm email'}
      </h2>
      <form onSubmit={submit}>
        <label>Email
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} required />
        </label>
        {mode !== 'confirm' && (
          <label>Password
            <input type="password" value={password} onChange={e=>setPassword(e.target.value)}
              minLength={8} required />
            <small className="muted">Min 8 chars, upper + lower + number.</small>
          </label>
        )}
        {mode === 'confirm' && (
          <label>Confirmation code (check your email)
            <input value={code} onChange={e=>setCode(e.target.value)} required />
          </label>
        )}
        {err && <div className="err">{err}</div>}
        <button disabled={busy} type="submit">
          {busy ? '…' : mode === 'signin' ? 'Sign in' : mode === 'signup' ? 'Create account' : 'Confirm'}
        </button>
      </form>
      <div className="switch">
        {mode === 'signin' && (
          <a onClick={()=>setMode('signup')}>No account? Sign up</a>
        )}
        {mode === 'signup' && (
          <a onClick={()=>setMode('signin')}>Already have an account? Sign in</a>
        )}
        {mode === 'confirm' && (
          <a onClick={()=>setMode('signin')}>Back to sign in</a>
        )}
      </div>
    </div>
  )
}
