import { useEffect } from 'react'
import Home from './pages/Home.jsx'
import './trust.css'

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

function SiteHeader() {
  return (
    <header className="sf-header">
      <div className="sf-brand-lockup">
        <a className="brand" href="#top" aria-label="SmartFinly home">SmartFinly</a>
        <span className="sf-brand-badge">AI planner for salaried India</span>
      </div>
      <nav className="sf-nav" aria-label="Primary navigation">
        <a href="#how-it-works">How it works</a>
        <a href="#features">Features</a>
        <a href="#trust">Trust</a>
        <a href="#planner">Planner</a>
      </nav>
    </header>
  )
}

function LandingHero() {
  return (
    <section className="sf-top-hero" id="top" aria-label="SmartFinly overview">
      <div className="sf-hero-copy">
        <div className="sf-eyebrow">Educational AI planning, not product selling</div>
        <h1>One financial plan for your salary, tax, SIPs, insurance and goals.</h1>
        <p>
          SmartFinly helps Indian families understand cash flow, tax impact, goal readiness,
          insurance gaps and retirement direction using deterministic calculations plus AI explanation.
        </p>
        <div className="sf-hero-actions">
          <a className="sf-primary-link" href="#planner">Start free planner</a>
          <a className="sf-secondary-link" href="#how-it-works">See how it works</a>
        </div>
        <div className="sf-hero-microcopy">
          No PAN, Aadhaar, OTP, bank account, UPI ID, password or brokerage login required.
        </div>
      </div>

      <div className="sf-proof-card" id="trust">
        <strong>Why users can trust it</strong>
        <ul>
          <li>Education-first output with no buy/sell calls or guaranteed returns.</li>
          <li>India-specific workflow for salary, HRA, EPF, NPS, tax deductions and family goals.</li>
          <li>Backend rejects sensitive identifiers such as PAN, Aadhaar, OTP and account details.</li>
          <li>Production deployment path includes Cognito, JWT auth and API throttling.</li>
        </ul>
      </div>
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
        {features.map(([title, body]) => (
          <article className="sf-feature-card" key={title}>
            <strong>{title}</strong>
            <p>{body}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

function SecuritySection() {
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
  return (
    <section className="sf-planner-intro" aria-label="Planner start">
      <span className="sf-kicker">Try the planner</span>
      <h2>Start with the demo profile or build your own plan step by step.</h2>
      <p>
        The planner below is intentionally detailed because real financial decisions connect across salary,
        taxes, debt, insurance, investments and goals. Use the demo profile for a fast preview.
      </p>
    </section>
  )
}

function FAQSection() {
  const faqs = [
    ['Is this investment advice?', 'No. SmartFinly provides educational planning output only. It is not registered investment, tax, legal, insurance, lending or securities advice.'],
    ['Do I need to share PAN or bank details?', 'No. Do not enter PAN, Aadhaar, OTP, passwords, bank account numbers, UPI IDs or brokerage credentials.'],
    ['Who is this built for?', 'The workflow is optimized for salaried Indian users and families who want to connect cash flow, tax, insurance, investments and goals.'],
    ['Can this be made production-ready?', 'Yes. The repo includes an authenticated SAM template with Cognito, HTTP API JWT auth and throttling as the production starting point.'],
  ]

  return (
    <section className="sf-section sf-faq" aria-label="Frequently asked questions">
      <div className="sf-section-heading">
        <span>FAQ</span>
        <h2>Questions before you start</h2>
      </div>
      <div className="sf-faq-grid">
        {faqs.map(([question, answer]) => (
          <details key={question}>
            <summary>{question}</summary>
            <p>{answer}</p>
          </details>
        ))}
      </div>
    </section>
  )
}

function SiteFooter() {
  return (
    <footer className="sf-footer" id="privacy">
      <div>
        <strong>Privacy-first finance UX</strong>
        <p>
          SmartFinly is designed to work without PAN, Aadhaar, OTP, passwords, bank account numbers,
          UPI IDs or brokerage credentials. Do not enter sensitive identifiers into the planner.
        </p>
      </div>
      <div>
        <strong>Compliance boundary</strong>
        <p>
          SmartFinly is an educational AI planning sample. It is not SEBI-registered investment advice,
          research, portfolio management, insurance broking, tax filing, lending or product execution.
        </p>
      </div>
      <div>
        <strong>Production readiness</strong>
        <p>
          Use <code>infrastructure/template.authenticated.yaml</code> before collecting real user financial data.
        </p>
      </div>
    </footer>
  )
}

export default function App() {
  useProductionPrivacyGuard()

  return (
    <div className="shell">
      <SiteHeader />
      <LandingHero />
      <ConfidenceStrip />
      <FeatureGrid />
      <SecuritySection />
      <main id="planner">
        <PlannerIntro />
        <Home />
      </main>
      <FAQSection />
      <SiteFooter />
    </div>
  )
}
