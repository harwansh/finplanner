import { trackEvent } from './analytics.js'

function classifyLink(target) {
  const anchor = target?.closest?.('a')
  if (!anchor) return null

  const href = anchor.getAttribute('href') || ''
  const label = anchor.textContent?.trim()?.slice(0, 80) || 'link'

  if (href.includes('/planner')) {
    return { name: label.toLowerCase().includes('demo') ? 'cta_demo_profile' : 'cta_start_planner', href, label }
  }
  if (href.includes('/learn')) {
    return { name: 'cta_learn', href, label }
  }
  if (href.startsWith('/')) {
    return { name: 'navigation_click', href, label }
  }
  return null
}

function trackPageView() {
  const path = window.location.pathname || '/'
  const kind = path === '/planner' ? 'planner_route_view' : path.match(/privacy|terms|disclaimer|security/) ? 'legal_route_view' : 'page_view'
  trackEvent(kind, { path })
}

if (typeof window !== 'undefined') {
  trackPageView()

  window.addEventListener('popstate', trackPageView)

  document.addEventListener('click', (event) => {
    const classified = classifyLink(event.target)
    if (!classified) return
    trackEvent(classified.name, {
      href: classified.href,
      label: classified.label
    })

    window.setTimeout(trackPageView, 0)
  }, { capture: true })
}
