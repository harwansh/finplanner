import { trackEvent } from './analytics.js'

function once(id, create) {
  if (document.getElementById(id)) return
  create()
}

function addHomepageProof() {
  const preview = document.querySelector('.sf-product-preview')
  if (!preview) return

  once('sf-preview-dashboard', () => {
    const dashboard = document.createElement('div')
    dashboard.id = 'sf-preview-dashboard'
    dashboard.className = 'sf-preview-dashboard'
    dashboard.innerHTML = `
      <article><small>Cash-flow</small><strong>₹42k surplus</strong><span>Income, EMIs, expenses and SIP capacity together.</span></article>
      <article><small>Tax</small><strong>Old vs new</strong><span>Compare deductions, tax paid and regime context.</span></article>
      <article><small>Goals</small><strong>3 priority gaps</strong><span>Inflation-adjusted education, home and retirement goals.</span></article>
      <article><small>Insurance</small><strong>Cover check</strong><span>Life and health cover mapped to dependents and liabilities.</span></article>
      <article><small>Retirement</small><strong>Direction</strong><span>EPF, NPS, SIPs and assumptions in one view.</span></article>
      <article><small>AI report</small><strong>Next steps</strong><span>Educational priorities without product selling.</span></article>
    `
    preview.appendChild(dashboard)
  })
}

function addPlannerUtilities() {
  if (window.location.pathname !== '/planner') return
  const planner = document.getElementById('planner')
  if (!planner) return

  once('sf-planner-utility-bar', () => {
    const bar = document.createElement('section')
    bar.id = 'sf-planner-utility-bar'
    bar.className = 'sf-planner-utility-bar'
    bar.innerHTML = `
      <div><strong>Planner status</strong><span>Online. Inputs are used only to generate this educational plan.</span></div>
      <button type="button" id="sf-print-plan">Save / print plan as PDF</button>
    `
    planner.prepend(bar)

    document.getElementById('sf-print-plan')?.addEventListener('click', () => {
      trackEvent('navigation_click', { label: 'save_print_pdf', href: '/planner#print' })
      window.print()
    })
  })
}

function addLegalDepth() {
  const legalPaths = ['/privacy', '/terms', '/disclaimer', '/security']
  if (!legalPaths.includes(window.location.pathname)) return
  const page = document.querySelector('.sf-legal-page')
  if (!page) return

  once('sf-legal-depth', () => {
    const panel = document.createElement('section')
    panel.id = 'sf-legal-depth'
    panel.className = 'sf-legal-depth'
    panel.innerHTML = `
      <h2>Production readiness commitments</h2>
      <div>
        <article><strong>Data minimization</strong><span>Collect only what is needed for educational planning.</span></article>
        <article><strong>Retention clarity</strong><span>Define retention and deletion before storing user profiles.</span></article>
        <article><strong>User rights</strong><span>Support deletion/export workflows before authenticated production launch.</span></article>
        <article><strong>Responsible AI</strong><span>Use deterministic calculations first and AI for explanation.</span></article>
      </div>
    `
    page.appendChild(panel)
  })
}

function enhance() {
  addHomepageProof()
  addPlannerUtilities()
  addLegalDepth()
}

if (typeof window !== 'undefined') {
  enhance()
  window.addEventListener('popstate', () => window.setTimeout(enhance, 50))
  document.addEventListener('click', () => window.setTimeout(enhance, 80), true)
  window.setTimeout(enhance, 250)
}
