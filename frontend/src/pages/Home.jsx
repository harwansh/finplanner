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
  currentInvestments: {
    equitySip: '', debtSip: '', epfPpfNps: '', nps: '', ppf: '',
    retirementSip: '', childEducationSip: '', fdRd: '', gold: '', otherMonthlyInvestments: ''
  },
  oneTimeFutureExpenses: '',
  existingGoals: '',
}

const investmentOptions = [
  'Mutual funds', 'Stocks', 'FD/RD', 'PPF/EPF/NPS',
  'Real estate', 'Gold', 'Not sure'
]

const assetLabels = {
  bankSavings: 'Bank savings',
  fixedDeposits: 'Fixed deposits',
  mutualFunds: 'Mutual funds',
  stocks: 'Stocks',
  epfPpfNps: 'EPF / PPF / NPS',
  gold: 'Gold',
  realEstate: 'Real estate',
  otherAssets: 'Other assets',
}

const liabilityLabels = {
  homeLoan: 'Home loan',
  personalLoan: 'Personal loan',
  educationLoan: 'Education loan',
  creditCard: 'Credit card',
  vehicleLoan: 'Vehicle loan',
  otherDebt: 'Other debt',
}

const currentInvestmentLabels = {
  equitySip: 'Equity mutual fund SIP',
  debtSip: 'Debt / hybrid SIP',
  epfPpfNps: 'EPF / PPF / NPS contribution',
  nps: 'Additional NPS',
  ppf: 'PPF contribution',
  retirementSip: 'Retirement-focused SIP',
  childEducationSip: 'Child education SIP',
  fdRd: 'FD / RD monthly investment',
  gold: 'Gold monthly investment',
  otherMonthlyInvestments: 'Other monthly investments',
}

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
  const preview = getCashflowPreview(data)

  const togglePref = (option) => {
    setData(d => {
      const cur = d.investmentPreferences
      const next = cur.includes(option) ? cur.filter(x => x !== option) : [...cur, option]
      return { ...d, investmentPreferences: next }
    })
  }

  const submit = async (e) => {
    e.preventDefault()
    const validationError = validate(data)
    if (validationError) {
      setErr(validationError)
      setResult(null)
      return
    }

    setBusy(true); setErr(''); setResult(null)
    try {
      const r = await analyze(cleanProfile(data))
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
            <Field label="Current age" required>
              <input type="number" min="18" max="100" value={data.basics.age}
                onChange={e=>set('basics','age',num(e.target.value))} required />
            </Field>
            <Field label="Desired retirement age" required>
              <input type="number" min="35" max="100" value={data.basics.desiredRetirementAge}
                onChange={e=>set('basics','desiredRetirementAge',num(e.target.value))} required />
            </Field>
            <Field label="Country" required>
              <input value={data.basics.country}
                onChange={e=>set('basics','country',e.target.value)} required />
            </Field>
            <Field label="City tier" required>
              <select value={data.basics.cityTier}
                onChange={e=>set('basics','cityTier',e.target.value)} required>
                <option>Tier 1</option><option>Tier 2</option><option>Tier 3</option>
              </select>
            </Field>
          </Row>
          <Row>
            <Field label="Marital status" required>
              <select value={data.basics.maritalStatus}
                onChange={e=>{
                  const maritalStatus = e.target.value
                  setData(d => ({
                    ...d,
                    basics: {
                      ...d.basics,
                      maritalStatus,
                      kids: maritalStatus === 'married' ? d.basics.kids : [],
                    }
                  }))
                }} required>
                <option value="single">Single</option>
                <option value="married">Married</option>
                <option value="divorced">Divorced</option>
                <option value="widowed">Widowed</option>
              </select>
            </Field>
            <Field label="Employment" required>
              <select value={data.basics.employmentType}
                onChange={e=>set('basics','employmentType',e.target.value)} required>
                <option value="salaried">Salaried</option>
                <option value="business">Business owner</option>
                <option value="freelance">Freelance / contractor</option>
              </select>
            </Field>
            <Field label="Tax regime" required>
              <select value={data.basics.taxRegime}
                onChange={e=>set('basics','taxRegime',e.target.value)} required>
                <option value="new">New</option>
                <option value="old">Old</option>
                <option value="unknown">Don't know</option>
              </select>
            </Field>
            <Field label="Own a home?" required>
              <select value={data.basics.ownsHouse ? 'yes' : 'no'}
                onChange={e=>set('basics','ownsHouse',e.target.value === 'yes')} required>
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
            <Field label="Parents financially dependent?" required>
              <select value={data.basics.parentsDependent ? 'yes' : 'no'}
                onChange={e=>{
                  const parentsDependent = e.target.value === 'yes'
                  setData(d => ({
                    ...d,
                    basics: {
                      ...d.basics,
                      parentsDependent,
                      dependentParentsCount: parentsDependent
                        ? Math.max(1, Number(d.basics.dependentParentsCount) || 1)
                        : 0,
                    }
                  }))
                }} required>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </Field>
            {data.basics.parentsDependent && (
              <Field label="Number of dependent parents" required>
                <input type="number" min="1" max="2" value={data.basics.dependentParentsCount}
                  onChange={e=>set('basics','dependentParentsCount',num(e.target.value))} required />
              </Field>
            )}
          </Row>
        </Section>

        <Section title="2. Income">
          <Row>
            <Field label="Monthly income after tax" required hint="Example: 2,00,000">
              <MoneyInput value={data.income.monthlyAfterTax}
                onChange={v=>set('income','monthlyAfterTax',v)} required />
            </Field>
            <Field label="Annual bonus / variable" hint="Enter 0 if none">
              <MoneyInput value={data.income.bonusAnnual}
                onChange={v=>set('income','bonusAnnual',v)} />
            </Field>
            <Field label="Other monthly income" hint="Rent, dividends etc.">
              <MoneyInput value={data.income.otherMonthly}
                onChange={v=>set('income','otherMonthly',v)} />
            </Field>
            <Field label="Expected income growth % / yr" required>
              <input type="number" min="0" max="100" step="0.1" value={data.income.expectedGrowthPct}
                onChange={e=>set('income','expectedGrowthPct',num(e.target.value))} required />
            </Field>
          </Row>
        </Section>

        <Section title="3. Expenses">
          <Row>
            <Field label="Fixed monthly expenses" required hint="Rent, school, utilities">
              <MoneyInput value={data.expenses.fixed}
                onChange={v=>set('expenses','fixed',v)} required />
            </Field>
            <Field label="Variable monthly expenses" required hint="Enter 0 if none">
              <MoneyInput value={data.expenses.variable}
                onChange={v=>set('expenses','variable',v)} required />
            </Field>
            <Field label="Annual lump sums" required hint="Insurance, vacations / year. Enter 0 if none">
              <MoneyInput value={data.expenses.annual}
                onChange={v=>set('expenses','annual',v)} required />
            </Field>
            <Field label="Total monthly EMIs" required hint="Enter 0 if none">
              <MoneyInput value={data.monthlyEmi}
                onChange={v=>setTop('monthlyEmi',v)} required />
            </Field>
          </Row>
          <CashflowPreview preview={preview} />
        </Section>

        <Section title="4. Assets">
          <div className="section-note">Current value in ₹. Optional fields can stay blank.</div>
          <Row>
            {Object.keys(empty.assets).map(k => (
              <Field key={k} label={assetLabels[k] || prettify(k)}>
                <MoneyInput value={data.assets[k]}
                  onChange={v=>set('assets',k,v)} />
              </Field>
            ))}
            <Field label="Emergency fund" required hint="Separate emergency fund. Enter 0 if none">
              <MoneyInput value={data.emergencyFund}
                onChange={v=>setTop('emergencyFund',v)} required />
            </Field>
          </Row>
        </Section>

        <Section title="5. Liabilities">
          <div className="section-note">Outstanding balance in ₹. Leave blank or enter 0 if not applicable.</div>
          <Row>
            {Object.keys(empty.liabilities).map(k => (
              <Field key={k} label={liabilityLabels[k] || prettify(k)}>
                <MoneyInput value={data.liabilities[k]}
                  onChange={v=>set('liabilities',k,v)} />
              </Field>
            ))}
          </Row>
        </Section>

        <Section title="6. Insurance">
          <Row>
            <Field label="Life cover" hint="Sum assured in ₹">
              <MoneyInput value={data.insurance.life}
                onChange={v=>set('insurance','life',v)} />
            </Field>
            <Field label="Health cover" hint="Family floater / individual cover">
              <MoneyInput value={data.insurance.health}
                onChange={v=>set('insurance','health',v)} />
            </Field>
            <Field label="Critical illness cover">
              <MoneyInput value={data.insurance.criticalIllness}
                onChange={v=>set('insurance','criticalIllness',v)} />
            </Field>
          </Row>
        </Section>

        <Section title="7. Current monthly investments">
          <div className="section-note">Enter SIPs/contributions already running every month. These are projected toward goals and reduce the new recommendation amount.</div>
          <Row>
            {Object.keys(empty.currentInvestments).map(k => (
              <Field key={k} label={currentInvestmentLabels[k] || prettify(k)}>
                <MoneyInput value={data.currentInvestments[k]}
                  onChange={v=>set('currentInvestments',k,v)} />
              </Field>
            ))}
          </Row>
        </Section>

        <Section title="8. Risk & investment preferences">
          <div className="muted small" style={{marginBottom:6}}>Risk appetite</div>
          <div className="radio-row">
            {['conservative','moderate','aggressive'].map(r => (
              <label key={r} className={`radio chip ${data.risk === r ? 'selected' : ''}`}>
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
              <label key={opt} className={`radio chip ${data.investmentPreferences.includes(opt) ? 'selected' : ''}`}>
                <input type="checkbox"
                  checked={data.investmentPreferences.includes(opt)}
                  onChange={()=>togglePref(opt)} /> {opt}
              </label>
            ))}
          </div>
        </Section>

        <Section title="9. Future plans">
          <Field label="Expected one-time future expenses" hint="Example: kid's MBA in 2038, car in 5 years, wedding in 2029">
            <textarea value={data.oneTimeFutureExpenses}
              onChange={e=>setTop('oneTimeFutureExpenses', e.target.value)} />
          </Field>
          <Field label="Existing financial goals" hint="Only goals entered here will be treated as user-entered goals">
            <textarea value={data.existingGoals}
              onChange={e=>setTop('existingGoals', e.target.value)} />
          </Field>
        </Section>

        {err && <div className="err error-block">{err}</div>}

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
          {summary.monthlySurplus <= 0 && (
            <div className="err" style={{marginBottom: 12}}>
              Your plan is not currently feasible. Monthly expenses exceed average monthly income by {fmt(Math.abs(summary.monthlySurplus))}. Fix cash flow before starting new long-term SIPs.
            </div>
          )}
          {summary.warnings?.length > 0 && (
            <ul className="muted small">
              {summary.warnings.map((warning, i) => <li key={i}>{warning}</li>)}
            </ul>
          )}
          <div className="kpi-grid">
            <Kpi label="Net worth" value={fmt(summary.netWorth)} big />
            <Kpi label="Total assets" value={fmt(summary.totalAssets)} />
            <Kpi label="Total liabilities" value={fmt(summary.totalLiabilities)} />
            <Kpi label="Average monthly income" value={fmt(summary.monthlyIncome)} />
            <Kpi label="Monthly expenses" value={fmt(summary.monthlyExpenses)} />
            <Kpi label="Monthly surplus" value={fmt(summary.monthlySurplus)} />
            <Kpi label="Savings rate" value={`${summary.savingsRatePct}%`} />
            <Kpi label="Emergency fund" value={`${summary.emergencyFundMonths} mo`} />
            <Kpi label="Existing monthly investments" value={fmt(summary.currentMonthlyInvestments)} />
            <Kpi label="Remaining surplus" value={fmt(summary.remainingSurplusAfterExistingInvestments)} />
          </div>
          {summary.monthlyExpenseBreakdown && (
            <div className="muted small" style={{marginTop: 12}}>
              Expense breakdown: fixed {fmt(summary.monthlyExpenseBreakdown.fixed)}
              {' '}+ variable {fmt(summary.monthlyExpenseBreakdown.variable)}
              {' '}+ annual prorated {fmt(summary.monthlyExpenseBreakdown.annualProrated)}
              {' '}+ EMI {fmt(summary.monthlyExpenseBreakdown.emi)}
            </div>
          )}
          {summary.monthlyBonusProrated > 0 && (
            <div className="muted small" style={{marginTop: 6}}>
              Average monthly income includes prorated annual bonus of {fmt(summary.monthlyBonusProrated)}.
            </div>
          )}
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
            <input type="number" min="0" value={kid.age}
              onChange={e=>update(i,'age', e.target.value === '' ? '' : Number(e.target.value))} />
          </Field>
          <button type="button" onClick={()=>remove(i)} className="link remove-btn">Remove</button>
        </Row>
      ))}
      <button type="button" onClick={add} className="link add-btn">+ Add child</button>
    </div>
  )
}

function MoneyInput({ value, onChange, required = false, placeholder = '0' }) {
  const displayValue = value === '' || value == null ? '' : formatIndianNumber(value)

  return (
    <div className="money-input">
      <span className="currency-prefix">₹</span>
      <input
        type="text"
        inputMode="numeric"
        autoComplete="off"
        value={displayValue}
        placeholder={placeholder}
        required={required}
        onChange={e => onChange(parseIndianNumber(e.target.value))}
        onBlur={e => onChange(parseIndianNumber(e.target.value))}
      />
    </div>
  )
}

function CashflowPreview({ preview }) {
  const isNegative = preview.monthlySurplus < 0
  return (
    <div className={`cashflow-preview ${isNegative ? 'danger' : 'success'}`}>
      <div className="cashflow-title">Monthly cash-flow preview</div>
      <div className="cashflow-grid">
        <span>Fixed: <strong>{fmt(preview.fixed)}</strong></span>
        <span>Variable: <strong>{fmt(preview.variable)}</strong></span>
        <span>Annual / month: <strong>{fmt(preview.annualProrated)}</strong></span>
        <span>EMI: <strong>{fmt(preview.emi)}</strong></span>
      </div>
      <div className="cashflow-total">
        Expenses: <strong>{fmt(preview.monthlyExpenses)}</strong> · Surplus: <strong>{fmt(preview.monthlySurplus)}</strong>
      </div>
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
const Field = ({ label, children, required = false, hint }) => (
  <label className="field">
    <span>{label}{required && <em className="required">*</em>}</span>
    {children}
    {hint && <small>{hint}</small>}
  </label>
)

function cleanProfile(profile) {
  const cleaned = structuredClone(profile)
  const kids = cleaned.basics.maritalStatus === 'married'
    ? cleaned.basics.kids
        .filter(kid => kid.name?.trim() || kid.age !== '')
        .map((kid, i) => ({
          name: kid.name?.trim() || `Child ${i + 1}`,
          age: Number(kid.age) || 0,
        }))
    : []

  cleaned.basics.kids = kids
  cleaned.basics.dependentParentsCount = cleaned.basics.parentsDependent
    ? Math.max(1, Number(cleaned.basics.dependentParentsCount) || 1)
    : 0

  return cleaned
}

function validate(profile) {
  if (Number(profile.basics.desiredRetirementAge) <= Number(profile.basics.age)) {
    return 'Desired retirement age must be greater than current age.'
  }
  if (profile.basics.parentsDependent && Number(profile.basics.dependentParentsCount) < 1) {
    return 'Please enter at least 1 dependent parent, or select "No" for parent dependency.'
  }

  const partialKid = profile.basics.kids.find(kid => Boolean(kid.name?.trim()) !== (kid.age !== ''))
  if (profile.basics.maritalStatus === 'married' && partialKid) {
    return 'Please enter both name and age for each child, or remove the incomplete child row.'
  }

  return ''
}

function getCashflowPreview(profile) {
  const recurringIncome = toNumber(profile.income.monthlyAfterTax) + toNumber(profile.income.otherMonthly)
  const proratedBonus = toNumber(profile.income.bonusAnnual) / 12
  const monthlyIncome = recurringIncome + proratedBonus
  const fixed = toNumber(profile.expenses.fixed)
  const variable = toNumber(profile.expenses.variable)
  const annualProrated = toNumber(profile.expenses.annual) / 12
  const emi = toNumber(profile.monthlyEmi)
  const monthlyExpenses = fixed + variable + annualProrated + emi

  return {
    fixed,
    variable,
    annualProrated,
    emi,
    monthlyExpenses,
    monthlySurplus: monthlyIncome - monthlyExpenses,
  }
}

function parseIndianNumber(value) {
  const digits = String(value || '').replace(/[^0-9]/g, '')
  if (!digits) return ''
  return Number(digits)
}

function formatIndianNumber(value) {
  const n = Number(value)
  if (!Number.isFinite(n)) return ''
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(n)
}

function toNumber(value) {
  return value === '' || value == null ? 0 : Number(value)
}

function prettify(k) {
  return k.replace(/([A-Z])/g, ' $1').replace(/^./, c => c.toUpperCase())
}
function fmt(n) {
  if (n == null || isNaN(n)) return '—'
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(n)
}
