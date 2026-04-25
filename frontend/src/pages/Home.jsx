import { useState, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { analyze } from '../api/client'

const empty = {
  basics: {
    age: '',
    desiredRetirementAge: 60,
    country: 'India',
    cityTier: 'Tier 1',
    maritalStatus: 'single',
    employmentType: 'salaried',
    kids: [],
    parentsDependent: false,
    dependentParentsCount: 0,
    ownsHouse: false,
    taxRegime: 'new',
  },
  income: { monthlyAfterTax: '', bonusAnnual: '', otherMonthly: '', expectedGrowthPct: 8 },
  expenses: { fixed: '', variable: '', annual: '' },
  monthlyEmi: '',
  emergencyFund: '',
  assets: {
    bankSavings: '', fixedDeposits: '', mutualFunds: '', stocks: '',
    epfPpfNps: '', gold: '', realEstate: '', otherAssets: ''
  },
  liabilities: {
    homeLoan: '', personalLoan: '', educationLoan: '',
    creditCard: '', vehicleLoan: '', otherDebt: ''
  },
  insurance: { life: '', health: '', criticalIllness: '' },
  risk: 'moderate',
  investmentPreferences: [],
  oneTimeFutureExpenses: '',
  existingGoals: '',
}

const investmentOptions = [
  'Mutual funds', 'Stocks', 'FD/RD', 'PPF/EPF/NPS',
  'Real estate', 'Gold', 'Not sure'
]

export default function Home() {
  const [data, setData] = useState(empty)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [result, setResult] = useState(null)
  const resultsRef = useRef(null)

  const set = (section, field, val) =>
    setData(d => ({ ...d, [section]: { ...d[section], [field]: val } }))
  const setTop = (field, val) => setData(d => ({ ...d, [field]: val }))
  const num = v => v === '' || v == null ? '' : Number(v)

  const togglePref = (option) => {
    setData(d => {
      const cur = d.investmentPreferences
      const next = cur.includes(option)
        ? cur.filter(x => x !== option)
        : [...cur, option]
      return { ...d, investmentPreferences: next }
    })
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setErr(''); setResult(null)
    try {
      const r = await analyze(data)
      setResult(r)
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    } catch (e) {
      setErr(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <form onSubmit={submit}>
        <Section title="1. About you">
          <Row>
            <Field label="Current age">
              <input type="number" value={data.basics.age}
                onChange={e=>set('basics','age',num(e.target.value))} required />
            </Field>
            <Field label="Desired retirement age">
              <input type="number" value={data.basics.desiredRetirementAge}
                onChange={e=>set('basics','desiredRetirementAge',num(e.target.value))} />
            </Field>
            <Field label="Country">
              <input value={data.basics.country}
                onChange={e=>set('basics','country',e.target.value)} />
            </Field>
            <Field label="City tier">
              <select value={data.basics.cityTier}
                onChange={e=>set('basics','cityTier',e.target.value)}>
                <option>Tier 1</option><option>Tier 2</option><option>Tier 3</option>
              </select>
            </Field>
          </Row>
          <Row>
            <Field label="Marital status">
              <select value={data.basics.maritalStatus}
                onChange={e=>set('basics','maritalStatus',e.target.value)}>
                <option value="single">Single</option>
                <option value="married">Married</option>
                <option value="divorced">Divorced</option>
                <option value="widowed">Widowed</option>
              </select>
            </Field>
            <Field label="Employment">
              <select value={data.basics.employmentType}
                onChange={e=>set('basics','employmentType',e.target.value)}>
                <option value="salaried">Salaried</option>
                <option value="business">Business owner</option>
                <option value="freelance">Freelance / contractor</option>
              </select>
            </Field>
            <Field label="Tax regime">
              <select value={data.basics.taxRegime}
                onChange={e=>set('basics','taxRegime',e.target.value)}>
                <option value="new">New</option>
                <option value="old">Old</option>
                <option value="unknown">Don't know</option>
              </select>
            </Field>
            <Field label="Own a home?">
              <select value={data.basics.ownsHouse ? 'yes' : 'no'}
                onChange={e=>set('basics','ownsHouse',e.target.value === 'yes')}>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </Field>
          </Row>

          {data.basics.maritalStatus === 'married' && (
            <KidsEditor kids={data.basics.kids}
              onChange={(kids)=>set('basics','kids',kids)} />
          )}

          <Row>
            <Field label="Parents financially dependent?">
              <select value={data.basics.parentsDependent ? 'yes' : 'no'}
                onChange={e=>set('basics','parentsDependent', e.target.value === 'yes')}>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </Field>
            {data.basics.parentsDependent && (
              <Field label="Number of dependent parents">
                <input type="number" min="0" max="2" value={data.basics.dependentParentsCount}
                  onChange={e=>set('basics','dependentParentsCount',num(e.target.value))} />
              </Field>
            )}
          </Row>
        </Section>

        <Section title="2. Income (₹ per month unless noted)">
          <Row>
            <Field label="Monthly income (after tax)">
              <input type="number" value={data.income.monthlyAfterTax}
                onChange={e=>set('income','monthlyAfterTax',num(e.target.value))} required />
            </Field>
            <Field label="Annual bonus / variable">
              <input type="number" value={data.income.bonusAnnual}
                onChange={e=>set('income','bonusAnnual',num(e.target.value))} />
            </Field>
            <Field label="Other monthly (rent, dividends)">
              <input type="number" value={data.income.otherMonthly}
                onChange={e=>set('income','otherMonthly',num(e.target.value))} />
            </Field>
            <Field label="Expected income growth % / yr">
              <input type="number" value={data.income.expectedGrowthPct}
                onChange={e=>set('income','expectedGrowthPct',num(e.target.value))} />
            </Field>
          </Row>
        </Section>

        <Section title="3. Expenses (₹ per month unless noted)">
          <Row>
            <Field label="Fixed (rent, school)">
              <input type="number" value={data.expenses.fixed}
                onChange={e=>set('expenses','fixed',num(e.target.value))} />
            </Field>
            <Field label="Variable (food, travel)">
              <input type="number" value={data.expenses.variable}
                onChange={e=>set('expenses','variable',num(e.target.value))} />
            </Field>
            <Field label="Annual lump sums (insurance, vacations) / yr">
              <input type="number" value={data.expenses.annual}
                onChange={e=>set('expenses','annual',num(e.target.value))} />
            </Field>
            <Field label="Total monthly EMIs">
              <input type="number" value={data.monthlyEmi}
                onChange={e=>setTop('monthlyEmi',num(e.target.value))} />
            </Field>
          </Row>
        </Section>

        <Section title="4. Assets (current value, ₹)">
          <Row>
            {Object.keys(empty.assets).map(k => (
              <Field key={k} label={prettify(k)}>
                <input type="number" value={data.assets[k]}
                  onChange={e=>set('assets',k,num(e.target.value))} />
              </Field>
            ))}
            <Field label="Emergency fund (separate)">
              <input type="number" value={data.emergencyFund}
                onChange={e=>setTop('emergencyFund',num(e.target.value))} />
            </Field>
          </Row>
        </Section>

        <Section title="5. Liabilities (outstanding balance, ₹)">
          <Row>
            {Object.keys(empty.liabilities).map(k => (
              <Field key={k} label={prettify(k)}>
                <input type="number" value={data.liabilities[k]}
                  onChange={e=>set('liabilities',k,num(e.target.value))} />
              </Field>
            ))}
          </Row>
        </Section>

        <Section title="6. Insurance (sum assured, ₹)">
          <Row>
            <Field label="Life cover">
              <input type="number" value={data.insurance.life}
                onChange={e=>set('insurance','life',num(e.target.value))} />
            </Field>
            <Field label="Health cover">
              <input type="number" value={data.insurance.health}
                onChange={e=>set('insurance','health',num(e.target.value))} />
            </Field>
            <Field label="Critical illness cover">
              <input type="number" value={data.insurance.criticalIllness}
                onChange={e=>set('insurance','criticalIllness',num(e.target.value))} />
            </Field>
          </Row>
        </Section>

        <Section title="7. Risk & investment preferences">
          <div className="muted small" style={{marginBottom:6}}>Risk appetite</div>
          <div className="radio-row">
            {['conservative','moderate','aggressive'].map(r => (
              <label key={r} className="radio">
                <input type="radio" checked={data.risk===r}
                  onChange={()=>setData(d=>({...d, risk:r}))} /> {r}
              </label>
            ))}
          </div>

          <div className="muted small" style={{marginTop:14, marginBottom:6}}>
            Investment preferences (pick any)
          </div>
          <div className="checkbox-row">
            {investmentOptions.map(opt => (
              <label key={opt} className="radio">
                <input type="checkbox"
                  checked={data.investmentPreferences.includes(opt)}
                  onChange={()=>togglePref(opt)} /> {opt}
              </label>
            ))}
          </div>
        </Section>

        <Section title="8. Future plans (optional, in your own words)">
          <Field label="Expected one-time future expenses (e.g., 'kid's MBA in 2030')">
            <textarea value={data.oneTimeFutureExpenses}
              onChange={e=>setTop('oneTimeFutureExpenses', e.target.value)} />
          </Field>
          <Field label="Existing financial goals (e.g., 'buy a house in 5 years')">
            <textarea value={data.existingGoals}
              onChange={e=>setTop('existingGoals', e.target.value)} />
          </Field>
        </Section>

        {err && <div className="err">{err}</div>}

        <div className="actions">
          <button type="submit" disabled={busy} className="primary">
            {busy ? 'Calculating…' : '🔮  Generate my financial plan'}
          </button>
          <span className="muted small">Nothing is saved. Refresh to start over.</span>
        </div>
      </form>

      <div ref={resultsRef}>
        {busy && (
          <div className="card center">
            <div className="spinner" />
            <p>Crunching your numbers… personalized plan takes 15–30 seconds.</p>
          </div>
        )}
        {result && <Results result={result} />}
      </div>
    </>
  )
}

function Results({ result }) {
  const { summary, report, error } = result
  return (
    <div className="results">
      {summary && (
        <div className="card">
          <h2>📊 Your numbers</h2>
          <div className="kpi-grid">
            <Kpi label="Net worth" value={fmt(summary.netWorth)} big />
            <Kpi label="Total assets" value={fmt(summary.totalAssets)} />
            <Kpi label="Total liabilities" value={fmt(summary.totalLiabilities)} />
            <Kpi label="Monthly income" value={fmt(summary.monthlyIncome)} />
            <Kpi label="Monthly expenses" value={fmt(summary.monthlyExpenses)} />
            <Kpi label="Monthly surplus" value={fmt(summary.monthlySurplus)} />
            <Kpi label="Savings rate" value={`${summary.savingsRatePct}%`} />
            <Kpi label="Emergency fund" value={`${summary.emergencyFundMonths} mo`} />
          </div>
        </div>
      )}

      {error && <div className="card err">{error}</div>}

      {report && (
        <div className="card markdown">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
        </div>
      )}
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

function KidsEditor({ kids, onChange }) {
  const add = () => onChange([...kids, { name: '', age: '' }])
  const update = (i, k, v) => {
    const copy = kids.slice(); copy[i] = { ...copy[i], [k]: v }; onChange(copy)
  }
  const remove = (i) => onChange(kids.filter((_,j)=>j!==i))
  return (
    <div className="kids">
      <div className="muted small">Children (optional)</div>
      {kids.map((kid, i) => (
        <Row key={i}>
          <Field label="Name">
            <input value={kid.name} onChange={e=>update(i,'name',e.target.value)} />
          </Field>
          <Field label="Age">
            <input type="number" value={kid.age}
              onChange={e=>update(i,'age', e.target.value === '' ? '' : Number(e.target.value))} />
          </Field>
          <button type="button" onClick={()=>remove(i)} className="link">Remove</button>
        </Row>
      ))}
      <button type="button" onClick={add} className="link">+ Add child</button>
    </div>
  )
}

const Section = ({ title, children }) => (
  <section className="card section">
    <h3>{title}</h3>
    {children}
  </section>
)
const Row = ({ children }) => <div className="row">{children}</div>
const Field = ({ label, children }) => (
  <label className="field"><span>{label}</span>{children}</label>
)
function prettify(k) {
  return k.replace(/([A-Z])/g, ' $1').replace(/^./, c => c.toUpperCase())
}
function fmt(n) {
  if (n == null || isNaN(n)) return '—'
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(n)
}
