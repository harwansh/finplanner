import { trackEvent } from '../analytics.js'

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
    return `Please review your planner inputs. ${message}`
  }
  if (status === 401 || status === 403) {
    return 'Please sign in again before generating your plan. Your inputs were not saved by SmartFinly.'
  }
  if (status === 408 || status === 429) {
    return 'SmartFinly is receiving too many planning requests right now. Your inputs were not saved. Please try again in a few minutes.'
  }
  if (status === 502 || status === 503 || status === 504) {
    return 'We could not generate your plan right now because the planning service is temporarily unavailable. Your inputs were not saved. Please try again in a few minutes.'
  }
  if (status >= 500) {
    return 'We could not generate your plan right now. Your inputs were not saved. Please try again in a few minutes.'
  }
  return message
}

const API_URL = import.meta.env.VITE_API_URL

export async function analyze(profile, accessToken = '') {
  if (!API_URL) {
    trackEvent('api_request_failed', { reason: 'missing_api_url' })
    throw new Error('The planner is not configured yet. Please try again after deployment is complete.')
  }

  const headers = {
    'Content-Type': 'application/json',
  }

  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`
  }

  trackEvent('api_request_started')

  let res
  try {
    res = await fetch(API_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify(profile)
    })
  } catch {
    trackEvent('api_request_failed', { reason: 'network_error' })
    throw new Error('We could not reach the planning service. Your inputs were not saved. Please check your connection and try again.')
  }

  const payload = await res.json().catch(async () => {
    const text = await res.text().catch(() => '')
    return { error: text || res.statusText }
  })

  if (!res.ok) {
    const validationErrors = Array.isArray(payload.validationErrors)
      ? `\n- ${payload.validationErrors.join('\n- ')}`
      : ''
    const message = payload.error || payload.message || parseApiError(res.status, JSON.stringify(payload))
    trackEvent('api_request_failed', { status: res.status })
    throw new Error(`${message}${validationErrors}`)
  }

  trackEvent('api_request_succeeded')
  return payload
}
