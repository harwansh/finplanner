const ALLOWED_EVENTS = new Set([
  'page_view',
  'navigation_click',
  'cta_start_planner',
  'cta_demo_profile',
  'cta_learn',
  'planner_route_view',
  'legal_route_view',
  'api_request_started',
  'api_request_succeeded',
  'api_request_failed'
])

function cleanProps(props = {}) {
  return Object.fromEntries(
    Object.entries(props)
      .filter(([, value]) => ['string', 'number', 'boolean'].includes(typeof value))
      .map(([key, value]) => [String(key).slice(0, 60), String(value).slice(0, 120)])
  )
}

export function trackEvent(name, props = {}) {
  if (!ALLOWED_EVENTS.has(name)) return

  const safeProps = cleanProps(props)

  if (typeof window === 'undefined') return

  if (typeof window.plausible === 'function') {
    window.plausible(name, { props: safeProps })
    return
  }

  if (typeof window.umami?.track === 'function') {
    window.umami.track(name, safeProps)
    return
  }

  if (typeof window.gtag === 'function') {
    window.gtag('event', name, safeProps)
    return
  }

  if (import.meta.env.DEV) {
    console.debug('[analytics]', name, safeProps)
  }
}
