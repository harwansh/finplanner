import { useEffect, useMemo, useState } from 'react'
import Home from './pages/Home.jsx'
import './trust.css'
import './ten.css'

const seoRoutes = {
  '/ai-financial-planner-india': {
    kicker: 'AI financial planner India',
    title: 'AI financial planner for salaried India.',
    description: 'Plan salary, tax, SIPs, insurance, liabilities, goals and retirement with India-specific educational AI guidance.',
    bullets: ['Salary and cash-flow planning', 'Old vs new tax regime context', 'SIP and goal gap estimates', 'Insurance and retirement readiness'],
  },
  '/salary-tax-planner-india': {
    kicker: 'Salary tax planner India',
    title: 'Understand salary, HRA, EPF, NPS and tax trade-offs.',
    description: 'Connect income, deductions, tax paid, HRA, EPF, NPS and family goals before making planning decisions.',
    bullets: ['HRA and salary components', '80C, 80D and NPS context', 'Old vs new regime comparison', 'Cash-flow impact after tax'],
  },
  '/sip-goal-planner': {
    kicker: 'SIP goal planner',
    title: 'Map SIPs to real goals, not just returns.',
    description: 'Estimate inflation-adjusted goals, existing investment support and monthly SIP gaps for education, home, retirement and wealth goals.',
    bullets: ['Inflation-adjusted goals', 'Goal-linked SIPs', 'Existing investment mapping', 'Monthly gap estimates'],
  },
  '/retirement-planner-india': {
    kicker: 'Retirement planner India',
    title: 'Estimate retirement direction with clear assumptions.',
    description: 'Use current age, retirement age, investments, EPF, NPS, expenses and assumptions to understand retirement readiness.',
    bullets: ['Retirement age and horizon', 'EPF/NPS/SIP mapping', 'Inflation and withdrawal assumptions', 'Corpus direction'],
  },
  '/insurance-gap-calculator': {
    kicker: 'Insurance gap calculator',
    title: 'Check whether cover matches obligations.',
    description: 'Review life and health cover against expenses, dependents, liabilities and financial goals before assuming protection is enough.',
    bullets: ['Life cover gap', 'Health cover context', 'Liability protection', 'Dependent-aware planning'],
  },
}

const pageMeta = {
  '/': {
    title: 'SmartFinly — AI Financial Planner for Salaried India',
    description: 'Plan salary, tax, SIPs, insurance, liabilities, goals and retirement with educational AI guidance built for Indian families.',
  },
  '/planner': {
    title: 'SmartFinly Planner — Salary, Tax, SIPs, Insurance and Goals',
    description: 'Use the SmartFinly planner to turn salary, tax, SIPs, insurance, liabilities and goals into an educational AI planning report.',
  },
  '/learn': {
    title: 'Learn Personal Finance for Salaried India — SmartFinly',
    description: 'Plain-English guides for investments, loans, credit cards, taxes, insurance and financial planning in India.',
  },
  '/privacy': {
    title: 'Privacy Policy — SmartFinly',
    description: 'How SmartFinly handles financial planning inputs and what sensitive identifiers users should never enter.',
  },
  '/terms': {
    title: 'Terms of Use — SmartFinly',
    description: 'Terms for using SmartFinly educational AI financial planning tools and content.',
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

function normalizePath(pathname) {
  const cleaned = pathname.replace(/\/$/, '') || '/'
  if (cleaned === '/home') return '/learn'
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
    if (window.location.pathname.replace(/\/$/, '') === '/home') {
      window.history.replaceState({}, '', '/learn')
      setPath('/learn')
    }
  }, [])

  return [path, setPath]
}

function navigate(event, href, setPath) {
  if (!href.startsWith('/')) return
  event.preventDefault()
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

    return () => {
      console.info = originalInfo
    }
  }, [])
}

function SiteHeader({ path, setPath }) {
  const navItems = [
    ['/', 'Home'],
    ['/planner', 'Planner'],
    ['/learn', 'Learn'],
    ['/security', 'Security'],
    ['/privacy', 'Privacy'],
  ]

  return (
    <header className="sf-header">
      <div className="sf-brand-lockup">
        <a className="brand" href="/" onClick={(event) => navigate(event, '/', setPath)} aria-label="SmartFinly home">SmartFinly</a>
        <span className="sf-brand-badge">AI planner for salaried India</span>
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
    <section className="sf-top-hero sf-hero-10" id="top" aria-label="SmartFinly overview">
      <div className="sf-hero-copy">
        <div className="sf-eyebrow">Educational AI planning, not product selling</div>
        <h1>One financial plan for your salary, tax, SIPs, insurance and goals.</h1>
        <p>
          SmartFinly helps Indian families understand cash flow, tax impact, goal readiness,
          insurance gaps and retirement direction using deterministic calculations plus AI explanation.
        </p>
        <div className="sf-hero-actions">
          <a className="sf-primary-link" href="/planner" onClick={(event) => navigate(event, '/planner', setPath)}>Start free planner</a>
          <a className="sf-secondary-link" href="/planner" onClick={(event) => navigate(event, '/planner', setPath)}>Try demo profile</a>
        </div>
        <div className="sf-hero-microcopy">
          No PAN, Aadhaar, OTP, bank account, UPI ID, password or brokerage login required.
        </div>
      </div>

      <div className="sf-proof-card sf-report-card" id="trust">
        <strong>What the report covers</strong>
        <div className="sf-mini-report">
          <span>Cash-flow surplus</span>
          <span>Tax regime context</span>
          <span>Goal gaps</span>
          <span>Insurance readiness</span>
          <span>Retirement direction</span>
          <span>Next-step priorities</span>
        </div>
      </div>
    </section>
  )
}

function TrustBar() {
  return (
    <section className="sf-trust-bar" aria-label="SmartFinly trust guarantees">
      <div><strong>0</strong><span>product sales</span></div>
      <div><strong>No</strong><span>PAN / Aadhaar / OTP</span></div>
      <div><strong>India</strong><span>salary + tax context</span></div>
      <div><strong>AI + math</strong><span>deterministic first</span></div>
    </section>
  )
}

function ConfidenceStrip() {
  return (
    <section className="sf-confidence-strip" id="how-it-works" aria-label="How SmartFinly works">
      <div><strong>1</strong><span>Load the demo profile or enter your own numbers.</span></div>
      <div><strong>2</strong><span>Review salary, tax, liabilities, insurance, investments and goals.</span></div>
      <div><strong>3</strong><span>Generate an educational AI planning report with clear next steps.</span></div>
    </section>
  )
}

function FeatureGrid() {
  const features = [
    ['Salary + cash flow', 'Connect take-home income, expenses, EMIs, bonus and surplus in one view.'],
    ['India tax context', 'Model old vs new regime, HRA, 80C, 80D, EPF, NPS and tax already paid.'],
    ['Goal readiness', 'Estimate goal gaps, inflation-adjusted needs and SIP requirements.'],
    ['Insurance gap', 'Compare current life and health cover with family obligations and expenses.'],
    ['Investment map', 'Link EPF, NPS, mutual funds, SIPs, gold, debt and other assets to goals.'],
    ['AI explanation layer', 'Turn calculations into plain-English educational guidance and priorities.'],
  ]

  return (
    <section className="sf-section" id="features" aria-label="SmartFinly features">
      <div className="sf-section-heading">
        <span>Built for real Indian household decisions</span>
        <h2>More complete than a budget tracker. Safer than an AI chatbot.</h2>
        <p>
          The planner first structures your numbers, then uses deterministic calculations before generating
          an educational explanation. That keeps the math grounded and the advice boundary clear.
        </p>
      </div>
      <div className="sf-feature-grid">
        {features.map(([title, body]) => <article className="sf-feature-card" key={title}><strong>{title}</strong><p>{body}</p></article>)}
      </div>
    </section>
  )
}

function ComparisonSection() {
  const rows = [
    ['Generic finance blog', 'Explains concepts', 'Does not connect your salary, tax, goals and insurance together.'],
    ['Spreadsheet', 'Flexible calculations', 'Hard to maintain and does not explain trade-offs clearly.'],
    ['AI chatbot', 'Easy conversation', 'Can hallucinate math or cross compliance boundaries.'],
    ['SmartFinly', 'Structured + explainable', 'Uses deterministic calculations first, then AI for educational explanation.'],
  ]

  return (
    <section className="sf-section sf-comparison" aria-label="SmartFinly comparison">
      <div className="sf-section-heading"><span>Why SmartFinly</span><h2>Built between a spreadsheet and a financial coach.</h2></div>
      <div className="sf-comparison-grid">
        {rows.map(([name, strength, gap]) => <article key={name}><strong>{name}</strong><em>{strength}</em><p>{gap}</p></article>)}
      </div>
    </section>
  )
}

function AssumptionsSection() {
  const assumptions = ['Inflation matters', 'Expected returns are assumptions', 'Tax rules can change', 'Insurance needs depend on dependents', 'AI output is educational']
  return (
    <section className="sf-section sf-assumptions" aria-label="Planning assumptions">
      <div className="sf-section-heading"><span>Transparent assumptions</span><h2>No black-box promises.</h2><p>SmartFinly keeps planning language grounded by showing assumptions, gaps and educational boundaries.</p></div>
      <div className="sf-pill-row">{assumptions.map((item) => <span key={item}>{item}</span>)}</div>
    </section>
  )
}

function SecuritySection({ setPath }) {
  return (
    <section className="sf-section sf-security" aria-label="Security and compliance boundaries">
      <div>
        <span className="sf-kicker">Privacy and compliance</span>
        <h2>Clear boundaries before users enter financial data.</h2>
        <p>
          SmartFinly is designed for educational planning. It does not ask for regulated identifiers,
          banking credentials or product execution access, and it avoids recommendation language such as
          guaranteed returns or buy/sell calls.
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
        <div><strong>Production path</strong><span>Use the authenticated SAM template before collecting real user financial data.</span></div>
      </div>
    </section>
  )
}

function PlannerIntro() {
  return <section className="sf-planner-intro" aria-label="Planner start"><span className="sf-kicker">Try the planner</span><h2>Start with the demo profile or build your own plan step by step.</h2><p>The planner below is intentionally detailed because real financial decisions connect across salary, taxes, debt, insurance, investments and goals. Use the demo profile for a fast preview.</p></section>
}

function FAQSection() {
  const faqs = [
    ['Is this investment advice?', 'No. SmartFinly provides educational planning output only. It is not registered investment, tax, legal, insurance, lending or securities advice.'],
    ['Do I need to share PAN or bank details?', 'No. Do not enter PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs or brokerage credentials.'],
    ['Who is this built for?', 'The workflow is optimized for salaried Indian users and families who want to connect cash flow, tax, insurance, investments and goals.'],
    ['Can this be made production-ready?', 'Yes. The repo includes an authenticated SAM template with Cognito, HTTP API JWT auth and throttling as the production starting point.'],
  ]
  return <section className="sf-section sf-faq" aria-label="Frequently asked questions"><div className="sf-section-heading"><span>FAQ</span><h2>Questions before you start</h2></div><div className="sf-faq-grid">{faqs.map(([question, answer]) => <details key={question}><summary>{question}</summary><p>{answer}</p></details>)}</div></section>
}

function LearnPage({ setPath }) {
  const guides = [
    ['Investments', 'SIP basics, asset allocation, EPF, PPF, NPS, mutual funds and goal-linked investing.', '/sip-goal-planner'],
    ['Tax planning', 'Old vs new regime, HRA, 80C, 80D, NPS and salary-structure planning.', '/salary-tax-planner-india'],
    ['Loans', 'EMIs, home-loan affordability, prepayment decisions and debt-risk checks.', '/planner'],
    ['Credit cards', 'Responsible usage, rewards, interest traps, credit scores and repayment discipline.', '/planner'],
    ['Insurance', 'Life cover, health cover, critical illness and emergency-fund readiness.', '/insurance-gap-calculator'],
    ['Retirement', 'Retirement corpus, withdrawal assumptions, inflation and long-term investing.', '/retirement-planner-india'],
  ]
  return <main className="sf-page"><section className="sf-section-heading sf-page-hero"><span>Learn</span><h1>Personal finance guides for salaried India.</h1><p>Use the guides to understand the concepts, then use the planner to connect them to your own numbers.</p><a className="sf-primary-link" href="/planner" onClick={(event) => navigate(event, '/planner', setPath)}>Open planner</a></section><section className="sf-feature-grid">{guides.map(([title, body, href]) => <article className="sf-feature-card" key={title}><strong>{title}</strong><p>{body}</p><a href={href} onClick={(event) => navigate(event, href, setPath)}>Explore</a></article>)}</section></main>
}

function SeoLandingPage({ page, setPath }) {
  return <main className="sf-page sf-seo-page"><section className="sf-section-heading sf-page-hero"><span>{page.kicker}</span><h1>{page.title}</h1><p>{page.description}</p><a className="sf-primary-link" href="/planner" onClick={(event) => navigate(event, '/planner', setPath)}>Open SmartFinly planner</a></section><section className="sf-legal-grid">{page.bullets.map((bullet) => <article className="sf-feature-card" key={bullet}><strong>{bullet}</strong><p>Use SmartFinly to connect this planning area with cash flow, tax, goals, insurance and retirement context.</p></article>)}</section><FAQSection /></main>
}

function LegalPage({ type }) {
  const content = useMemo(() => ({
    privacy: { kicker: 'Privacy policy', title: 'Privacy-first financial planning boundaries.', sections: [['What SmartFinly processes', 'The planner may process salary, expenses, liabilities, insurance, investments, tax and goal inputs to generate educational planning output.'], ['What not to enter', 'Do not enter PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs, brokerage credentials or other sensitive identifiers.'], ['Demo vs production', 'The demo deployment is for sample data. Use the authenticated production deployment before collecting real user financial data.'], ['User control', 'A production deployment should define retention, deletion and export controls before launch.']] },
    terms: { kicker: 'Terms of use', title: 'Use SmartFinly as an educational planning tool.', sections: [['Educational use', 'SmartFinly helps users understand personal-finance scenarios and does not replace a qualified professional.'], ['No misuse', 'Do not use the planner to enter sensitive identifiers, credentials, unlawful content or another person’s data without consent.'], ['No guarantees', 'Outputs depend on assumptions and user inputs. They are not guarantees of returns, tax savings or financial outcomes.'], ['Availability', 'The app may change, pause or remove features as the product evolves.']] },
    disclaimer: { kicker: 'Disclaimer', title: 'SmartFinly is not regulated financial advice.', sections: [['Not investment advice', 'SmartFinly is not SEBI-registered investment advice, research analysis, portfolio management or product distribution.'], ['Not tax or legal advice', 'Tax calculations are educational estimates and not tax filing, legal advice or professional certification.'], ['Not insurance or lending', 'SmartFinly is not insurance broking, lending, credit underwriting or product execution.'], ['Review assumptions', 'All outputs should be reviewed with qualified professionals before financial decisions.']] },
    security: { kicker: 'Security', title: 'Security posture and production-readiness checklist.', sections: [['Sensitive-data rejection', 'The backend rejects common sensitive identifiers such as PAN, Aadhaar, OTP, passwords, account numbers and UPI-like data.'], ['Authenticated deployment', 'Use the Cognito + HTTP API JWT-authenticated SAM template for production deployments.'], ['Rate limits', 'Protect Bedrock and API usage with API throttling, WAF rules and per-user application limits.'], ['Logging', 'Production logs should never contain full financial payloads or sensitive user inputs.']] },
  })[type], [type])
  return <main className="sf-page sf-legal-page"><section className="sf-section-heading sf-page-hero"><span>{content.kicker}</span><h1>{content.title}</h1></section><section className="sf-legal-grid">{content.sections.map(([title, body]) => <article className="sf-feature-card" key={title}><strong>{title}</strong><p>{body}</p></article>)}</section></main>
}

function PlannerPage() {
  return <main id="planner"><PlannerIntro /><Home /></main>
}

function HomePage({ setPath }) {
  return <><LandingHero setPath={setPath} /><TrustBar /><ConfidenceStrip /><FeatureGrid /><ComparisonSection /><SecuritySection setPath={setPath} /><AssumptionsSection /><section className="sf-section sf-product-preview"><div className="sf-section-heading"><span>Product preview</span><h2>The planner connects decisions users usually review separately.</h2><p>Cash flow, tax, goals, insurance and investment planning are presented together so trade-offs are visible.</p></div><div className="sf-feature-grid"><article className="sf-feature-card"><strong>Cash-flow summary</strong><p>Income, expenses, EMIs, existing investments and surplus.</p></article><article className="sf-feature-card"><strong>Tax comparison</strong><p>Old/new regime context, deductions and tax already paid.</p></article><article className="sf-feature-card"><strong>Goal gap analysis</strong><p>Inflation-adjusted goals and monthly SIP requirement.</p></article></div><a className="sf-primary-link" href="/planner" onClick={(event) => navigate(event, '/planner', setPath)}>Try with demo profile</a></section><FAQSection /></>
}

function SiteFooter({ setPath }) {
  const links = [['/privacy', 'Privacy'], ['/terms', 'Terms'], ['/disclaimer', 'Disclaimer'], ['/security', 'Security'], ['/learn', 'Learn']]
  return <footer className="sf-footer" id="privacy"><div><strong>Privacy-first finance UX</strong><p>SmartFinly is designed to work without PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs or brokerage credentials. Do not enter sensitive identifiers into the planner.</p></div><div><strong>Compliance boundary</strong><p>SmartFinly is an educational AI planning sample. It is not SEBI-registered investment advice, research, portfolio management, insurance broking, tax filing, lending or product execution.</p></div><div><strong>Site links</strong><p className="sf-footer-links">{links.map(([href, label]) => <a key={href} href={href} onClick={(event) => navigate(event, href, setPath)}>{label}</a>)}</p></div></footer>
}

function StickyCTA({ setPath }) {
  return <div className="sf-sticky-cta"><span>Build your educational plan in minutes.</span><a href="/planner" onClick={(event) => navigate(event, '/planner', setPath)}>Start free</a></div>
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
