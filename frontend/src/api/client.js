import { fetchAuthSession } from 'aws-amplify/auth'
import { API_URL } from '../auth/config'

async function authHeaders() {
  const session = await fetchAuthSession()
  const token = session.tokens?.idToken?.toString()
  return token ? { Authorization: token } : {}
}

export async function getProfile() {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/profile`, { headers })
  if (!res.ok) throw new Error(`GET /profile ${res.status}`)
  return (await res.json()).profile
}

export async function saveProfile(profile) {
  const headers = { ...(await authHeaders()), 'Content-Type': 'application/json' }
  const res = await fetch(`${API_URL}/profile`, {
    method: 'PUT',
    headers,
    body: JSON.stringify({ profile })
  })
  if (!res.ok) throw new Error(`PUT /profile ${res.status}`)
  return res.json()
}

export async function analyze() {
  const headers = { ...(await authHeaders()), 'Content-Type': 'application/json' }
  const res = await fetch(`${API_URL}/analyze`, { method: 'POST', headers })
  if (!res.ok) throw new Error(`POST /analyze ${res.status}`)
  return res.json()
}
