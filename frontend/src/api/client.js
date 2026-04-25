
function parseApiError(status, text) {
  let message = text || `Request failed with status ${status}`
  try {
    const parsed = JSON.parse(text)
    if (parsed?.error) message = parsed.error
    if (parsed?.message) message = parsed.message
  } catch {
    // keep raw text
  }

  if (status === 400) {
    return `Please check your inputs: ${message}`
  }
  if (status === 502 || status === 504) {
    return 'Backend is temporarily unavailable. Please redeploy and check CloudWatch logs.'
  }
  if (status >= 500) {
    return `Server error: ${message}`
  }
  return message
}

const API_URL = import.meta.env.VITE_API_URL

export async function analyze(profile) {
  const res = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile)
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
