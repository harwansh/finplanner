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

function parseChatError(status, payload) {
  if (payload?.answer) return payload.answer
  if (payload?.error) return payload.error
  if (status === 400) return 'Please enter a finance education question without personal identifiers.'
  return 'SmartFinly could not answer right now. Please try again in a moment.'
}

const API_URL = import.meta.env.VITE_API_URL
const CHAT_API_URL = import.meta.env.VITE_CHAT_API_URL

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

export async function chat(message, accessToken = '') {
  if (!CHAT_API_URL) {
    throw new Error('The learning chat is not configured yet.')
  }

  const headers = { 'Content-Type': 'application/json' }
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  trackEvent('chat_request_started')
  let res
  try {
    res = await fetch(CHAT_API_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message }),
    })
  } catch {
    trackEvent('chat_request_failed', { reason: 'network_error' })
    throw new Error('We could not reach the learning chat. Please check your connection and try again.')
  }

  const payload = await res.json().catch(async () => {
    const text = await res.text().catch(() => '')
    return { error: text || res.statusText }
  })

  if (!res.ok) {
    trackEvent('chat_request_failed', { status: res.status })
    throw new Error(parseChatError(res.status, payload))
  }

  trackEvent('chat_request_succeeded', { source: payload.source })
  return payload
}
