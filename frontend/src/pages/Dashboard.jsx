import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { analyze, getProfile } from '../api/client'

export default function Dashboard() {
  const [state, setState] = useState({ status: 'init' })

  const run = async () => {
    setState({ status: 'loading' })
    try {
      const profile = await getProfile()
      if (!profile) return setState({ status: 'no-profile' })
      const result = await analyze()
      setState({ status: 'ok', ...result })
    } catch (e) {
      setState({ status: 'err', error: e.message })
    }
  }

  useEffect(() => { run() }, [])

  if (state.status === 'init' || state.status === 'loading') {
    return <div className="card">Crunching your numbers…</div>
  }

  if (state.status === 'no-profile') {
    return (
      <div className="card narrow">
        <h2>Welcome 👋</h2>
        <p>Tell us about your finances and we'll generate your personalized plan.</p>
        <Link to="/onboarding"><button>Start onboarding</button></Link>
      </div>
    )
  }

  if (state.status === 'err') {
    return (
      <div className="card">
        <div className="err">Failed: {state.error}</div>
        <button onClick={run}>Retry</button>
      </div>
    )
  }

  const { summary, goals } = state
  return (
    <div className="grid">
      <div className="card">
        <div className="row spread">
          <h2>Net worth</h2>
          <Link to="/onboarding" className="link">Edit profile</Link>
        </div>
        <div className="kpi-grid">
          <Kpi label="Net worth" value={fmt(summary.netWorth)} big />
          <Kpi label="Total assets" value={fmt(summary.totalAssets)} />
          <Kpi label="Total liabilities" value={fmt(summary.totalLiabilities)} />
          <Kpi label="Monthly surplus" value={fmt(summary.monthlySurplus)} />
          <Kpi label="Savings rate" value={`${summary.savingsRatePct}%`} />
          <Kpi label="Emergency fund" value={`${summary.emergencyFundMonths} mo`} />
        </div>
      </div>

      <Bucket title="🛡️ Must-have (5)" goals={goals.mustHave} tone="critical" />
      <Bucket title="📈 Good-to-have (5)" goals={goals.goodToHave} tone="medium" />
      <Bucket title="✨ Optional (5)" goals={goals.optional} tone="optional" />
    </div>
  )
}

function Kpi({ label, value, big }) {
  return (
    <div className={`kpi ${big ? 'big' : ''}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
    </div>
  )
}

function Bucket({ title, goals, tone }) {
  if (!Array.isArray(goals)) return null
  return (
    <div className={`card bucket ${tone}`}>
      <h3>{title}</h3>
      {goals.map((g, i) => (
        <div key={i} className="goal">
          <div className="row spread">
            <strong>{g.title}</strong>
            <span className="muted">
              {g.timelineMonths} mo · {fmt(g.monthlyContribution)}/mo
            </span>
          </div>
          <div className="muted small">Target: {fmt(g.targetAmount)}</div>
          <p>{g.rationale}</p>
        </div>
      ))}
    </div>
  )
}

function fmt(n) {
  if (n == null || isNaN(n)) return '—'
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(n)
}
