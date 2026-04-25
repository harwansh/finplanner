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
  if (status === 401 || status === 403) {
    return 'Please sign in again before generating your plan.'
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

export async function analyze(profile, accessToken = '') {
  if (!API_URL) {
    throw new Error('Missing VITE_API_URL. Please configure the frontend environment.')
  }

  const headers = {
    'Content-Type': 'application/json',
  }

  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  }

  const res = await fetch(API_URL, {
    method: 'POST',
    headers,
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
    const message = payload.error || payload.message || parseApiError(res.status, JSON.stringify(payload))
    throw new Error(`${message}${validationErrors}`)
  }

  return payload
}
