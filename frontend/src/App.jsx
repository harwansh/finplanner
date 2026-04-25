import { useEffect, useMemo, useState } from 'react'
import Home from './pages/Home.jsx'
import './trust.css'
import './ten.css'
import './framework.css'

const frameworkModules = [
  ['Income Reality', 'Starts with salary structure, take-home income, fixed costs, EMIs, dependents and monthly surplus.'],
  ['Protection First', 'Checks emergency fund, health cover, life cover and liability protection before chasing returns.'],
  ['Goal Hierarchy', 'Separates must-have, should-have and aspirational goals across short, medium and long horizons.'],
  ['Tax-Aware Allocation', 'Connects EPF, NPS, 80C, 80D, HRA and regime choice with investible surplus.'],
  ['Risk Capacity', 'Uses age, dependents, job stability, debt burden, horizon and loss tolerance to frame risk capacity.'],
  ['Decision Rules', 'Turns the assessment into SIP gaps, goal priorities, insurance gaps and review actions.'],
]

const decisionFlow = [
  ['01', 'Map salary reality', 'Income, expenses, liabilities, dependents and existing investments.'],
  ['02', 'Secure the foundation', 'Emergency fund, insurance and debt-risk checks before investment decisions.'],
  ['03', 'Prioritize goals', 'Must-have, should-have and aspirational goals by urgency and time horizon.'],
  ['04', 'Choose investment direction', 'Tax-aware, risk-aware and goal-linked allocation guidance.'],
  ['05', 'Review and rebalance', 'Periodic review as income, family needs, tax rules and market conditions change.'],
]

const seoRoutes = {
  '/financial-goal-planning-framework-india': {
    kicker: 'Framework for India',
    title: 'A framework for financial goal planning among young salary earners in India.',
    description: 'A structured approach for young middle-class salary earners to plan goals, manage risk and make investment decisions.',
    bullets: ['Income and expense mapping', 'Goal hierarchy', 'Risk capacity', 'Tax-aware investment decisions'],
  },
  '/investment-decision-making-salary-earners': {
    kicker: 'Investment decision-making',
    title: 'Investment decisions should follow goals, risk capacity and cash-flow reality.',
    description: 'SmartFinly helps salary earners connect investment choices with goal timelines, tax context and household constraints.',
    bullets: ['Goal-linked SIPs', 'Risk-capacity checks', 'Tax-aware instruments', 'Review and rebalance rules'],
  },
  '/salary-tax-planner-india': {
    kicker: 'Salary and tax context',
    title: 'Salary, tax and surplus determine what can realistically be invested.',
    description: 'Connect take-home pay, HRA, EPF, NPS, 80C, 80D, EMIs and surplus before setting investment targets.',
    bullets: ['Take-home income', 'Old vs new tax regime', 'Deductions and NPS', 'Investible surplus'],
  },
  '/sip-goal-planner': {
    kicker: 'Goal-linked SIP planning',
    title: 'SIPs should be mapped to goals, not selected in isolation.',
    description: 'Estimate inflation-adjusted goals, existing support and monthly SIP gaps for education, home, retirement and wealth goals.',
    bullets: ['Inflation-adjusted goals', 'SIP gap estimates', 'Existing investment mapping', 'Goal review'],
  },
  '/insurance-gap-calculator': {
    kicker: 'Protection-first planning',
    title: 'Investment planning starts with protection gaps.',
    description: 'Review life and health cover against dependents, liabilities and essential expenses before taking higher investment risk.',
    bullets: ['Life cover gap', 'Health cover context', 'Liability protection', 'Emergency fund'],
  },
}

const pageMeta = {
  '/': {
    title: 'SmartFinly — Financial Goal Planning Framework for Salary Earners in India',
    description: 'A structured framework for financial goal planning and investment decision-making among young middle-class salary earners in India.',
  },
  '/planner': {
    title: 'SmartFinly Framework Planner — Goals, Risk, Tax and Investment Decisions',
    description: 'Use the SmartFinly framework planner to connect salary, expenses, protection, goals, risk capacity, tax and investment decisions.',
  },
  '/learn': {
    title: 'Learn Financial Goal Planning for Salary Earners — SmartFinly',
    description: 'Plain-English guides for salary earners in India on goals, investments, tax, insurance, loans and retirement planning.',
  },
  '/privacy': {
    title: 'Privacy Policy — SmartFinly',
    description: 'How SmartFinly handles financial planning inputs and what sensitive identifiers users should never enter.',
  },
  '/terms': {
    title: 'Terms of Use — SmartFinly',
    description: 'Terms for using SmartFinly educational financial planning tools and framework content.',
  },
  '/disclaimer': {
    title: 'Disclaimer — SmartFinly',
    description: 'SmartFinly is educational only and is not SEBI-registered investment advice, tax filing, insurance broking, lending or product execution.',
  },
  '/security': {
    title: 'Security — SmartFinly',
    description: 'SmartFinly security posture, sensitive-data boundaries and production deployment recommendations.',
  },
  ...Object.fromEntries(Object.entries(seoRoutes).map(([path, page]) => [path, {
    title: `${page.title} — SmartFinly`,
    description: page.description,
  }])),
}

function trackEvent(name, detail = {}) {
  window.dispatchEvent(new CustomEvent('smartfinly:event', { detail: { name, ...detail } }))
  if (window.plausible) window.plausible(name, { props: detail })
  if (import.meta.env.DEV) console.debug('[SmartFinly event]', name, detail)
}

function normalizePath(pathname) {
  const cleaned = pathname.replace(/\/$/, '') || '/'
  if (cleaned === '/home') return '/learn'
  if (cleaned === '/ai-financial-planner-india') return '/financial-goal-planning-framework-india'
  if (cleaned === '/retirement-planner-india') return '/sip-goal-planner'
  return pageMeta[cleaned] ? cleaned : '/'
}

function usePathname() {
  const [path, setPath] = useState(() => normalizePath(window.location.pathname))

  useEffect(() => {
    const onPopState = () => setPath(normalizePath(window.location.pathname))
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  useEffect(() => {
    const normalized = normalizePath(window.location.pathname)
    if (normalized !== window.location.pathname.replace(/\/$/, '') && normalized !== '/') {
      window.history.replaceState({}, '', normalized)
      setPath(normalized)
    }
  }, [])

  return [path, setPath]
}

function navigate(event, href, setPath, eventName = 'navigation_click') {
  if (!href.startsWith('/')) return
  event.preventDefault()
  trackEvent(eventName, { target: href })
  const next = normalizePath(href)
  window.history.pushState({}, '', next)
  setPath(next)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function useDocumentMeta(path) {
  useEffect(() => {
    const meta = pageMeta[path] || pageMeta['/']
    document.title = meta.title
    const description = document.querySelector('meta[name="description"]')
    if (description) description.setAttribute('content', meta.description)
    let canonical = document.querySelector('link[rel="canonical"]')
    if (!canonical) {
      canonical = document.createElement('link')
      canonical.setAttribute('rel', 'canonical')
      document.head.appendChild(canonical)
    }
    canonical.setAttribute('href', `https://www.smartfinly.com${path === '/' ? '/' : path}`)
    trackEvent('page_view', { path })
  }, [path])
}

function useProductionPrivacyGuard() {
  useEffect(() => {
    if (import.meta.env.DEV) return undefined
    const originalInfo = console.info
    console.info = (...args) => {
      if (args[0] === 'SmartFinly FINAL submit payload') return
      originalInfo.apply(console, args)
    }
    return () => { console.info = originalInfo }
  }, [])
}

function SiteHeader({ path, setPath }) {
  const navItems = [
    ['/', 'Framework'],
    ['/planner', 'Planner'],
    ['/learn', 'Learn'],
    ['/security', 'Security'],
    ['/privacy', 'Privacy'],
  ]

  return (
    <header className="sf-header">
      <div className="sf-brand-lockup">
        <a className="brand" href="/" onClick={(event) => navigate(event, '/', setPath)} aria-label="SmartFinly home">SmartFinly</a>
        <span className="sf-brand-badge">Goal-planning framework for salary earners</span>
      </div>
      <nav className="sf-nav" aria-label="Primary navigation">
        {navItems.map(([href, label]) => (
          <a key={href} href={href} className={path === href ? 'active' : ''} onClick={(event) => navigate(event, href, setPath)}>{label}</a>
        ))}
      </nav>
    </header>
  )
}

function LandingHero({ setPath }) {
  return (
    <section className="sf-top-hero sf-framework-hero" id="top" aria-label="SmartFinly framework overview">
      <div className="sf-hero-copy">
        <div className="sf-eyebrow">A framework, not a product-pushing advisor</div>
        <h1>Financial goal planning and investment decision-making for young salary earners in India.</h1>
        <p>
          SmartFinly helps young middle-class salary earners convert monthly income, family responsibilities,
          tax context, protection needs and life goals into a structured financial decision framework.
        </p>
        <div className="sf-hero-actions">
          <a className="sf-primary-link" href="/planner" onClick={(event) => navigate(event, '/planner', setPath, 'start_framework_planner')}>Use the framework planner</a>
          <a className="sf-secondary-link" href="/financial-goal-planning-framework-india" onClick={(event) => navigate(event, '/financial-goal-planning-framework-india', setPath, 'view_framework_page')}>View framework</a>
        </div>
        <div className="sf-hero-microcopy">
          Built for salary-first households: cash flow, protection, goals, tax and investment decisions in one sequence.
        </div>
      </div>

      <div className="sf-proof-card sf-report-card" id="trust">
        <strong>Framework output</strong>
        <div className="sf-score-preview">
          <span>Decision readiness</span>
          <strong>Goal-led</strong>
          <em>No product sales. No guaranteed returns.</em>
        </div>
        <div className="sf-mini-report">
          <span>Income reality</span>
          <span>Protection gap</span>
          <span>Goal hierarchy</span>
          <span>Risk capacity</span>
          <span>Tax-aware allocation</span>
          <span>Review rules</span>
        </div>
      </div>
    </section>
  )
}

function FrameworkModules() {
  return (
    <section className="sf-section sf-framework-modules" aria-label="SmartFinly framework modules">
      <div className="sf-section-heading">
        <span>The SmartFinly framework</span>
        <h2>Six modules that turn salary into structured decisions.</h2>
        <p>
          The framework is designed for young middle-class earners whose financial choices are constrained by
          monthly salary, EMIs, dependents, tax rules, inflation and competing life goals.
        </p>
      </div>
      <div className="sf-feature-grid">
        {frameworkModules.map(([title, body]) => (
          <article className="sf-feature-card" key={title}><strong>{title}</strong><p>{body}</p></article>
        ))}
      </div>
    </section>
  )
}

function DecisionFlow() {
  return (
    <section className="sf-section sf-decision-flow" aria-label="Decision-making flow">
      <div className="sf-section-heading">
        <span>Decision sequence</span>
        <h2>Investment decisions come after goal clarity and risk capacity.</h2>
      </div>
      <div className="sf-flow-grid">
        {decisionFlow.map(([step, title, body]) => (
          <article key={step}>
            <span>{step}</span>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function TrustBar() {
  return (
    <section className="sf-trust-bar" aria-label="SmartFinly trust guarantees">
      <div><strong>Goal</strong><span>planning before investing</span></div>
      <div><strong>No</strong><span>PAN / Aadhaar / OTP</span></div>
      <div><strong>India</strong><span>salary + tax context</span></div>
      <div><strong>Rules</strong><span>risk-aware decisions</span></div>
    </section>
  )
}

function StatusStrip() {
  return (
    <section className="sf-status-strip" aria-label="SmartFinly service status">
      <span className="sf-status-dot" aria-hidden="true" />
      <strong>Framework planner online</strong>
      <p>Educational planning is available. Inputs are used to generate a structured planning report, not product recommendations.</p>
    </section>
  )
}

function WhoItServes() {
  const users = [
    ['Early-career earners', 'People starting SIPs, building emergency funds and learning tax basics.'],
    ['Young families', 'Households balancing rent or home loans, insurance, children’s goals and retirement.'],
    ['Middle-class professionals', 'Salary earners who need disciplined, goal-linked investing instead of ad hoc decisions.'],
  ]
  return <section className="sf-section"><div className="sf-section-heading"><span>Who it serves</span><h2>Designed around the Indian salary-earner lifecycle.</h2></div><div className="sf-feature-grid">{users.map(([title, body]) => <article className="sf-feature-card" key={title}><strong>{title}</strong><p>{body}</p></article>)}</div></section>
}

function SecuritySection({ setPath }) {
  return (
    <section className="sf-section sf-security" aria-label="Security and compliance boundaries">
      <div>
        <span className="sf-kicker">Education and compliance boundary</span>
        <h2>Framework guidance, not regulated advice.</h2>
        <p>
          SmartFinly is an educational planning framework. It does not ask for regulated identifiers,
          banking credentials or brokerage access, and it does not provide buy/sell calls or guaranteed returns.
        </p>
        <div className="sf-inline-links">
          <a href="/privacy" onClick={(event) => navigate(event, '/privacy', setPath)}>Privacy policy</a>
          <a href="/disclaimer" onClick={(event) => navigate(event, '/disclaimer', setPath)}>Disclaimer</a>
          <a href="/security" onClick={(event) => navigate(event, '/security', setPath)}>Security</a>
        </div>
      </div>
      <div className="sf-security-list">
        <div><strong>Never enter</strong><span>PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs or brokerage credentials.</span></div>
        <div><strong>Educational only</strong><span>Not SEBI-registered investment advice, research, portfolio management or tax filing.</span></div>
        <div><strong>Decision framework</strong><span>Outputs help users structure goals, risk and investment choices for further review.</span></div>
      </div>
    </section>
  )
}

function PlannerIntro() {
  return <section className="sf-planner-intro" aria-label="Planner start"><span className="sf-kicker">Framework planner</span><h2>Apply the framework to salary, goals, protection, risk and investment decisions.</h2><p>Use the demo profile or your own numbers to see how salary reality, protection needs, goal hierarchy, tax context and risk capacity interact.</p><button className="sf-print-button" type="button" onClick={() => { trackEvent('print_framework_report'); window.print() }}>Print or save framework report as PDF</button></section>
}

function FAQSection() {
  const faqs = [
    ['Is this investment advice?', 'No. SmartFinly provides an educational framework for goal planning and investment decision-making. It is not registered investment, tax, legal, insurance, lending or securities advice.'],
    ['Who is this built for?', 'Young middle-class salary earners in India who need to connect salary, taxes, EMIs, dependents, insurance, goals and investing.'],
    ['Why framework-first?', 'Because investment choices should follow cash-flow capacity, protection needs, goal timelines, risk capacity and tax context.'],
    ['Do I need to share PAN or bank details?', 'No. Do not enter PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs or brokerage credentials.'],
  ]
  return <section className="sf-section sf-faq" aria-label="Frequently asked questions"><div className="sf-section-heading"><span>FAQ</span><h2>Questions before you start</h2></div><div className="sf-faq-grid">{faqs.map(([question, answer]) => <details key={question}><summary>{question}</summary><p>{answer}</p></details>)}</div></section>
}

function LearnPage({ setPath }) {
  const guides = [
    ['Goal hierarchy', 'Separate essential, lifestyle and aspirational goals before choosing investments.', '/financial-goal-planning-framework-india'],
    ['Investment decisions', 'Use time horizon, risk capacity, tax context and liquidity needs to frame investment choices.', '/investment-decision-making-salary-earners'],
    ['Salary and tax context', 'Understand take-home pay, HRA, EPF, NPS, deductions and investible surplus.', '/salary-tax-planner-india'],
    ['SIP and goal gaps', 'Estimate SIP requirements based on goal amount, inflation and existing investments.', '/sip-goal-planner'],
    ['Protection planning', 'Review emergency fund, life cover and health cover before increasing risk.', '/insurance-gap-calculator'],
    ['Review discipline', 'Revisit the plan when salary, family needs, tax rules or market conditions change.', '/planner'],
  ]
  return <main className="sf-page"><section className="sf-section-heading sf-page-hero"><span>Learn the framework</span><h1>Financial planning concepts for young salary earners in India.</h1><p>Use the guides to understand the decision framework, then apply it with the planner.</p><a className="sf-primary-link" href="/planner" onClick={(event) => navigate(event, '/planner', setPath, 'learn_to_planner_click')}>Open framework planner</a></section><section className="sf-feature-grid">{guides.map(([title, body, href]) => <article className="sf-feature-card" key={title}><strong>{title}</strong><p>{body}</p><a href={href} onClick={(event) => navigate(event, href, setPath)}>Explore</a></article>)}</section></main>
}

function SeoLandingPage({ page, setPath }) {
  return <main className="sf-page sf-seo-page"><section className="sf-section-heading sf-page-hero"><span>{page.kicker}</span><h1>{page.title}</h1><p>{page.description}</p><a className="sf-primary-link" href="/planner" onClick={(event) => navigate(event, '/planner', setPath, 'seo_to_planner_click')}>Apply the framework</a></section><section className="sf-legal-grid">{page.bullets.map((bullet) => <article className="sf-feature-card" key={bullet}><strong>{bullet}</strong><p>Use SmartFinly to connect this planning area with salary, risk, tax, protection and goal hierarchy.</p></article>)}</section><DecisionFlow /><FAQSection /></main>
}

function LegalPage({ type }) {
  const content = useMemo(() => ({
    privacy: { kicker: 'Privacy policy', title: 'Privacy-first planning boundaries.', sections: [['What SmartFinly processes', 'The planner may process salary, expenses, liabilities, insurance, investments, tax and goal inputs to generate educational framework output.'], ['What not to enter', 'Do not enter PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs, brokerage credentials or other sensitive identifiers.'], ['Demo vs production', 'The demo deployment is for sample data. Use the authenticated production deployment before collecting real user financial data.'], ['User control', 'A production deployment should define retention, deletion and export controls before launch.']] },
    terms: { kicker: 'Terms of use', title: 'Use SmartFinly as an educational framework.', sections: [['Educational use', 'SmartFinly helps users understand personal-finance scenarios and does not replace a qualified professional.'], ['No misuse', 'Do not use the planner to enter sensitive identifiers, credentials, unlawful content or another person’s data without consent.'], ['No guarantees', 'Outputs depend on assumptions and user inputs. They are not guarantees of returns, tax savings or financial outcomes.'], ['Availability', 'The app may change, pause or remove features as the framework evolves.']] },
    disclaimer: { kicker: 'Disclaimer', title: 'SmartFinly is not regulated financial advice.', sections: [['Not investment advice', 'SmartFinly is not SEBI-registered investment advice, research analysis, portfolio management or product distribution.'], ['Not tax or legal advice', 'Tax calculations are educational estimates and not tax filing, legal advice or professional certification.'], ['Not insurance or lending', 'SmartFinly is not insurance broking, lending, credit underwriting or product execution.'], ['Review assumptions', 'All outputs should be reviewed with qualified professionals before financial decisions.']] },
    security: { kicker: 'Security', title: 'Security posture and production-readiness checklist.', sections: [['Sensitive-data rejection', 'The backend rejects common sensitive identifiers such as PAN, Aadhaar, OTP, passwords, account numbers and UPI-like data.'], ['Authenticated deployment', 'Use the Cognito + HTTP API JWT-authenticated SAM template for production deployments.'], ['Rate limits', 'Protect Bedrock and API usage with API throttling, WAF rules and per-user application limits.'], ['Logging', 'Production logs should never contain full financial payloads or sensitive user inputs.']] },
  })[type], [type])
  return <main className="sf-page sf-legal-page"><section className="sf-section-heading sf-page-hero"><span>{content.kicker}</span><h1>{content.title}</h1></section><section className="sf-legal-grid">{content.sections.map(([title, body]) => <article className="sf-feature-card" key={title}><strong>{title}</strong><p>{body}</p></article>)}</section></main>
}

function PlannerPage() {
  return <main id="planner"><PlannerIntro /><StatusStrip /><Home /></main>
}

function HomePage({ setPath }) {
  return <><LandingHero setPath={setPath} /><TrustBar /><StatusStrip /><FrameworkModules /><DecisionFlow /><WhoItServes /><SecuritySection setPath={setPath} /><FAQSection /></>
}

function SiteFooter({ setPath }) {
  const links = [['/privacy', 'Privacy'], ['/terms', 'Terms'], ['/disclaimer', 'Disclaimer'], ['/security', 'Security'], ['/learn', 'Learn']]
  return <footer className="sf-footer" id="privacy"><div><strong>Framework-first finance</strong><p>SmartFinly helps young salary earners structure goals, risk, protection, tax context and investment decisions without product selling.</p></div><div><strong>Compliance boundary</strong><p>SmartFinly is an educational framework. It is not SEBI-registered investment advice, research, portfolio management, insurance broking, tax filing, lending or product execution.</p></div><div><strong>Site links</strong><p className="sf-footer-links">{links.map(([href, label]) => <a key={href} href={href} onClick={(event) => navigate(event, href, setPath)}>{label}</a>)}</p></div></footer>
}

function StickyCTA({ setPath }) {
  return <div className="sf-sticky-cta"><span>Apply the framework to your salary and goals.</span><a href="/planner" onClick={(event) => navigate(event, '/planner', setPath, 'sticky_cta_click')}>Start</a></div>
}

export default function App() {
  useProductionPrivacyGuard()
  const [path, setPath] = usePathname()
  useDocumentMeta(path)

  let page = <HomePage setPath={setPath} />
  if (path === '/planner') page = <PlannerPage />
  if (path === '/learn') page = <LearnPage setPath={setPath} />
  if (path === '/privacy') page = <LegalPage type="privacy" />
  if (path === '/terms') page = <LegalPage type="terms" />
  if (path === '/disclaimer') page = <LegalPage type="disclaimer" />
  if (path === '/security') page = <LegalPage type="security" />
  if (seoRoutes[path]) page = <SeoLandingPage page={seoRoutes[path]} setPath={setPath} />

  return <div className="shell"><SiteHeader path={path} setPath={setPath} />{page}<SiteFooter setPath={setPath} /><StickyCTA setPath={setPath} /></div>
}
