const API_URL = import.meta.env.VITE_API_URL

export async function analyze(profile) {
  const res = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ profile })
  })

  const payload = await res.json().catch(async () => {
    const text = await res.text().catch(() => '')
    return { error: text || res.statusText }
  })

  if (!res.ok) {
    const validationErrors = Array.isArray(payload.validationErrors)
      ? `\n- ${payload.validationErrors.join('\n- ')}`
      : ''
    throw new Error(`${payload.error || `POST ${res.status}`}${validationErrors}`)
  }

  return payload
}
