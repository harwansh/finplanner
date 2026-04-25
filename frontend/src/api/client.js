const API_URL = import.meta.env.VITE_API_URL

export async function analyze(profile) {
  const res = await fetch(`${API_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile })
  })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`POST /analyze ${res.status}: ${txt || res.statusText}`)
  }
  return res.json()
}
