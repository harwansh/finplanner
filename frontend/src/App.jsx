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

function TrustHeader() {
  return (
    <>
      <header className="sf-header">
        <div className="sf-brand-lockup">
          <span className="brand">SmartFinly</span>
          <span className="sf-brand-badge">India-first AI financial planning</span>
        </div>
        <nav className="sf-nav" aria-label="Trust navigation">
          <a href="#planner">Planner</a>
          <a href="#trust">Trust</a>
          <a href="#privacy">Privacy</a>
        </nav>
      </header>

      <section className="sf-top-hero" aria-label="SmartFinly overview">
        <div className="sf-hero-copy">
          <div className="sf-eyebrow">Educational planning, not product selling</div>
          <h1>Turn salary, tax, SIPs, insurance and goals into one clear action plan.</h1>
          <p>
            SmartFinly helps Indian families understand cash flow, goal readiness, tax impact,
            insurance gaps and retirement direction using deterministic calculations plus AI explanation.
          </p>
          <div className="sf-hero-actions">
            <a className="sf-primary-link" href="#planner">Start planner</a>
            <a className="sf-secondary-link" href="#trust">Review trust checks</a>
          </div>
        </div>

        <div className="sf-proof-card" id="trust">
          <strong>Trust posture</strong>
          <ul>
            <li>No PAN, Aadhaar, OTP, bank account or password required.</li>
            <li>Educational output only; no buy/sell calls or guaranteed returns.</li>
            <li>Production template includes Cognito, JWT auth and throttling.</li>
            <li>Frontend API client supports bearer-token authenticated requests.</li>
          </ul>
        </div>
      </section>

      <section className="sf-confidence-strip" aria-label="Product confidence checks">
        <div><strong>1</strong><span>Load demo profile or enter your own numbers.</span></div>
        <div><strong>2</strong><span>Review salary, tax, liabilities, insurance and goals.</span></div>
        <div><strong>3</strong><span>Generate an educational AI planning report.</span></div>
      </section>
    </>
  )
}

function TrustFooter() {
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
      <TrustHeader />
      <main id="planner"><Home /></main>
      <TrustFooter />
    </div>
  )
}
