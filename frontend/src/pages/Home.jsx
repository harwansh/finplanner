import { useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { analyze } from '../api/client'

const empty = {
  basics: {
    age: '',
    desiredRetirementAge: 60,
    country: 'India',
    cityTier: 'Metro',
    maritalStatus: 'single',
    employmentType: 'salaried',
    kids: [],
    parentsDependent: false,
    dependentParentsCount: 0,
    ownsHouse: false,
    taxRegime: 'new',
  },
  salary: {
    monthlyBasic: '',
    monthlyHra: '',
    monthlySpecialAllowance: '',
    monthlyLta: '',
    monthlyBonus: '',
    monthlyEmployerNps: '',
    monthlyEmployeeEpf: '',
    monthlyProfessionalTax: '',
    rentPaidMonthly: '',
    annualGross: '',
  },
  income: { monthlyAfterTax: '', bonusAnnual: '', otherMonthly: '', expectedGrowthPct: 8 },
  expenses: { fixed: '', variable: '', annual: '' },
  monthlyEmi: '',
  emergencyFund: '',
  assets: {
    bankSavings: '', fixedDeposits: '', mutualFunds: '', stocks: '',
    epfCorpus: '', ppfCorpus: '', npsCorpus: '', gold: '', realEstate: '', otherAssets: ''
  },
  liabilities: {
    homeLoan: '', personalLoan: '', educationLoan: '',
    creditCard: '', vehicleLoan: '', otherDebt: ''
  },
  insurance: { life: '', health: '', criticalIllness: '' },
  tax: {
    deduction80C: '', nps80CCD1B: '', health80D: '', homeLoanInterest24B: '',
    homeLoan80EEA: '', educationLoan80E: '', donation80G: '',
    interest80TTA_TTB: '', hraExemption: '', ltaExemption: '',
    professionalTax: '', otherAnnualIncome: ''
  },
  investments: [],
  goals: [],
}

const liabilityLabels = {
  homeLoan: 'Home loan',
  personalLoan: 'Personal loan',
  educationLoan: 'Education loan',
  creditCard: 'Credit card',
  vehicleLoan: 'Vehicle loan',
  otherDebt: 'Other debt',
}

const salaryLabels = {
  monthlyBasic: 'Monthly basic salary',
  monthlyHra: 'Monthly HRA received',
  monthlySpecialAllowance: 'Monthly special / flexible allowance',
  monthlyLta: 'Monthly LTA',
  monthlyBonus: 'Monthly bonus / variable average',
  monthlyEmployerNps: 'Monthly employer NPS',
  monthlyEmployeeEpf: 'Monthly employee EPF',
  monthlyProfessionalTax: 'Monthly professional tax',
  rentPaidMonthly: 'Monthly rent paid',
  annualGross: 'Annual gross salary override',
}

const taxLabels = {
  deduction80C: '80C investments excluding salary EPF auto-added',
  nps80CCD1B: 'Extra self NPS 80CCD(1B), employer NPS auto-added',
  health80D: 'Health insurance 80D',
  homeLoanInterest24B: 'Home loan interest 24(b)',
  homeLoan80EEA: 'Affordable housing 80EEA',
  educationLoan80E: 'Education loan interest 80E',
  donation80G: 'Donation 80G',
  interest80TTA_TTB: 'Savings/deposit interest 80TTA/80TTB',
  hraExemption: 'Manual HRA exemption override',
  ltaExemption: 'LTA exemption',
  professionalTax: 'Extra annual professional tax',
  otherAnnualIncome: 'Other annual taxable income',
}

const investmentCategories = [
  ['momentum', 'Aggressive - Momentum', 18],
  ['value', 'Aggressive - Value', 17],
  ['midcap', 'Aggressive - Midcap', 17],
  ['smallcap', 'Aggressive - Smallcap', 16],
  ['niftyNext50', 'Aggressive - Nifty Next 50', 16],
  ['customStockBasket', 'Aggressive - custom stock basket', 18],
  ['multicap', 'Core - Multicap', 15],
  ['flexicap', 'Core - Flexicap', 14],
  ['nifty50', 'Core - Nifty 50', 13],
  ['us500', 'Defensive growth - US 500', 15],
  ['gold', 'Defensive - Gold / SGB', 12],
  ['reitInvit', 'Defensive - REITs / InvITs', 12],
  ['equityLargeCap', 'MF - Large cap', 11],
  ['equityMidCap', 'MF - Mid cap', 12],
  ['equitySmallCap', 'MF - Small cap', 13],
  ['equityFlexiCap', 'MF - Flexi / multi cap', 11],
  ['equityIndex', 'MF - Index fund', 11],
  ['elss', 'MF - ELSS / tax saver', 11],
  ['smallcase', 'Smallcase / stock basket', 12],
  ['debtFund', 'Debt mutual fund', 7],
  ['liquidFund', 'Liquid fund', 5.5],
  ['hybridFund', 'Hybrid / balanced fund', 9],
  ['fdRd', 'FD / RD', 6.5],
  ['epf', 'EPF', 8.25],
  ['ppf', 'PPF', 7.1],
  ['nps', 'NPS', 10],
  ['retirementSip', 'Retirement SIP', 10],
  ['childEducation', 'Child education SIP', 10],
  ['realEstate', 'Real estate investment', 6],
  ['other', 'Other investment', 8],
]

const investmentGoals = [
  ['retirement', 'Retirement'],
  ['emergency', 'Emergency'],
  ['childEducation', 'Child education'],
  ['home', 'Home'],
  ['wealth', 'Wealth creation'],
  ['taxSaving', 'Tax saving'],
  ['education', 'Education'],
  ['medical', 'Medical'],
  ['other', 'Other'],
]

const goalCategories = [
  ['retirement', 'Retirement'],
  ['education', 'Education'],
  ['childEducation', 'Child education'],
  ['home', 'Home'],
  ['medical', 'Medical'],
  ['travel', 'Travel'],
  ['vehicle', 'Vehicle'],
  ['wealth', 'Wealth creation'],
  ['other', 'Other'],
]

const categoryReturnMap = Object.fromEntries(investmentCategories.map(([key,, ret]) => [key, ret]))
const goalInflationMap = { retirement: 6, education: 10, childEducation: 10, home: 6, medical: 10, travel: 6, vehicle: 6, wealth: 6, other: 6 }

const tabs = [
  ['profile', 'Profile'],
  ['salary', 'Salary & cash-flow'],
  ['debt', 'Liabilities'],
  ['insurance', 'Insurance'],
  ['investments', 'Investments'],
  ['goals', 'Goals'],
  ['tax', 'Tax'],
  ['review', 'Review'],
]

export default function Home() {
  const [data, setData] = useState(empty)
  const [activeTab, setActiveTab] = useState('profile')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const [result, setResult] = useState(null)
  const resultsRef = useRef(null)

  const set = (section, field, val) =>
    setData(d => ({ ...d, [section]: { ...d[section], [field]: val } }))
  const setTop = (field, val) => setData(d => ({ ...d, [field]: val }))
  const num = v => v === '' || v == null ? '' : Number(v)
  const preview = useMemo(() => getCashflowPreview(data), [data])
  const salaryPreview = useMemo(() => getSalaryPreview(data), [data])
  const currentIndex = tabs.findIndex(([key]) => key === activeTab)

  const goNext = () => setActiveTab(tabs[Math.min(currentIndex + 1, tabs.length - 1)][0])
  const goBack = () => setActiveTab(tabs[Math.max(currentIndex - 1, 0)][0])

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
      <div className="card hero-card">
        <h2>FinOS Planner</h2>
        <p className="muted">A CFP-style financial operating system for salary, tax, cash-flow, liabilities, insurance, investments, goals and retirement.</p>
      </div>

      <form onSubmit={submit}>
        <div className="tabs-card">
          <div className="tabs">
            {tabs.map(([key, label], index) => (
              <button
                type="button"
                key={key}
                className={`tab ${activeTab === key ? 'active' : ''} ${index < currentIndex ? 'done' : ''}`}
                onClick={() => setActiveTab(key)}
              >
                <span>{index + 1}</span>{label}
              </button>
            ))}
          </div>
        </div>

        {activeTab === 'profile' && (
          <Section title="1. Profile">
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
              <Field label="City type" required>
                <select value={data.basics.cityTier}
                  onChange={e=>set('basics','cityTier',e.target.value)} required>
                  <option>Metro</option><option>Tier 1</option><option>Tier 2</option><option>Tier 3</option><option>Tier 4</option><option>Rural / Village</option>
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
                      basics: { ...d.basics, maritalStatus, kids: maritalStatus === 'married' ? d.basics.kids : [] }
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
              <Field label="Own a home?" required>
                <select value={data.basics.ownsHouse ? 'yes' : 'no'}
                  onChange={e=>set('basics','ownsHouse',e.target.value === 'yes')} required>
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </Field>
              <Field label="Parents financially dependent?" required>
                <select value={data.basics.parentsDependent ? 'yes' : 'no'}
                  onChange={e=>{
                    const parentsDependent = e.target.value === 'yes'
                    setData(d => ({ ...d, basics: { ...d.basics, parentsDependent, dependentParentsCount: parentsDependent ? Math.max(1, Number(d.basics.dependentParentsCount) || 1) : 0 }}))
                  }} required>
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </Field>
            </Row>

            {data.basics.parentsDependent && (
              <Row>
                <Field label="Number of dependent parents" required>
                  <input type="number" min="1" max="2" value={data.basics.dependentParentsCount}
                    onChange={e=>set('basics','dependentParentsCount',num(e.target.value))} required />
                </Field>
              </Row>
            )}

            {data.basics.maritalStatus === 'married' && (
              <KidsEditor kids={data.basics.kids} onChange={(kids)=>set('basics','kids',kids)} />
            )}
          </Section>
        )}

        {activeTab === 'salary' && (
          <>
            <Section title="2. Salary structure">
              <div className="section-note">
                Based on your tax workbook: Basic, HRA, LTA, employer NPS, employee EPF, professional tax and rent help calculate old vs new regime more accurately. Employee EPF is auto-added to 80C and retirement investments. Employer NPS is auto-added to tax deductions and retirement investments. Use annual gross override only if your payslip gives one final annual number.
              </div>
              <Row>
                {Object.keys(data.salary).map(k => (
                  <Field key={k} label={salaryLabels[k] || prettify(k)}>
                    <MoneyInput value={data.salary[k]} onChange={v=>set('salary',k,v)} />
                  </Field>
                ))}
              </Row>
              <div className="cashflow-preview success">
                <div className="cashflow-title">Salary tax preview</div>
                <div className="cashflow-grid">
                  <span>Annual salary components: <strong>{fmt(salaryPreview.annualComponents)}</strong></span>
                  <span>Annual gross used: <strong>{fmt(salaryPreview.annualGrossUsed)}</strong></span>
                  <span>Annual HRA received: <strong>{fmt(salaryPreview.hraAnnual)}</strong></span>
                  <span>Annual rent paid: <strong>{fmt(salaryPreview.rentAnnual)}</strong></span>
                  <span>Employee EPF auto 80C: <strong>{fmt(salaryPreview.employeeEpfAnnual)}</strong></span>
                  <span>Employer NPS auto retirement: <strong>{fmt(salaryPreview.employerNpsAnnual)}</strong></span>
                </div>
              </div>
            </Section>

            <Section title="3. Cash-flow">
              <Row>
                <Field label="Monthly income after tax" required hint="Used for cash-flow/surplus. Example: 2,00,000">
                  <MoneyInput value={data.income.monthlyAfterTax} onChange={v=>set('income','monthlyAfterTax',v)} required />
                </Field>
                <Field label="Annual bonus / variable" hint="Cash-flow bonus if not already in monthly net income">
                  <MoneyInput value={data.income.bonusAnnual} onChange={v=>set('income','bonusAnnual',v)} />
                </Field>
                <Field label="Other monthly income">
                  <MoneyInput value={data.income.otherMonthly} onChange={v=>set('income','otherMonthly',v)} />
                </Field>
                <Field label="Expected income growth % / yr">
                  <input type="number" min="0" max="100" step="0.1" value={data.income.expectedGrowthPct}
                    onChange={e=>set('income','expectedGrowthPct',num(e.target.value))} />
                </Field>
              </Row>
              <Row>
                <Field label="Fixed monthly expenses" required>
                  <MoneyInput value={data.expenses.fixed} onChange={v=>set('expenses','fixed',v)} required />
                </Field>
                <Field label="Variable monthly expenses" required>
                  <MoneyInput value={data.expenses.variable} onChange={v=>set('expenses','variable',v)} required />
                </Field>
                <Field label="Annual lump sums" required hint="Insurance, vacations, fees / year">
                  <MoneyInput value={data.expenses.annual} onChange={v=>set('expenses','annual',v)} required />
                </Field>
                <Field label="Total monthly EMIs" required>
                  <MoneyInput value={data.monthlyEmi} onChange={v=>setTop('monthlyEmi',v)} required />
                </Field>
              </Row>
              <CashflowPreview preview={preview} />
            </Section>
          </>
        )}

        {activeTab === 'debt' && (
          <Section title="4. Liabilities and emergency">
            <div className="section-note">
              Add only your emergency fund and debts here. Put all investment/current corpus values in “Existing investments and SIPs” to avoid duplicate counting.
            </div>
            <Row>
              <Field label="Emergency fund" required hint="Liquid amount kept for emergencies">
                <MoneyInput value={data.emergencyFund} onChange={v=>setTop('emergencyFund',v)} required />
              </Field>
              {Object.keys(empty.liabilities).map(k => (
                <Field key={k} label={liabilityLabels[k] || prettify(k)}>
                  <MoneyInput value={data.liabilities[k]} onChange={v=>set('liabilities',k,v)} />
                </Field>
              ))}
            </Row>
          </Section>
        )}

        {activeTab === 'insurance' && (
          <Section title="5. Insurance">
            <div className="section-note">Enter current cover. FinOS calculates required life and health cover from dependents, liabilities, expenses and goals.</div>
            <Row>
              <Field label="Life cover">
                <MoneyInput value={data.insurance.life} onChange={v=>set('insurance','life',v)} />
              </Field>
              <Field label="Health cover">
                <MoneyInput value={data.insurance.health} onChange={v=>set('insurance','health',v)} />
              </Field>
              <Field label="Critical illness cover">
                <MoneyInput value={data.insurance.criticalIllness} onChange={v=>set('insurance','criticalIllness',v)} />
              </Field>
            </Row>
          </Section>
        )}

        {activeTab === 'investments' && (
          <Section title="6. Existing investments and SIPs">
            <div className="section-note">This is the single source for investment/current corpus values: EPF, PPF, NPS, mutual funds, smallcase, stocks, FD/RD, gold, real estate and SIPs. Return % is auto-filled by category but editable.</div>
            <InvestmentEditor investments={data.investments} onChange={v=>setTop('investments', v)} />
          </Section>
        )}

        {activeTab === 'goals' && (
          <Section title="7. Goals">
            <div className="section-note">Structured goals replace free-text future plans. Add only goals you actually want.</div>
            <GoalEditor goals={data.goals} onChange={v=>setTop('goals', v)} />
          </Section>
        )}

        {activeTab === 'tax' && (
          <Section title="8. Tax inputs FY 2026-27">
            <div className="section-note">
              Optional deductions/exemptions for old vs new regime. Salary details from the Salary tab are used automatically for HRA, employer NPS, EPF and professional tax where possible.
            </div>
            <Row>
              {Object.keys(empty.tax).map(k => (
                <Field key={k} label={taxLabels[k] || prettify(k)}>
                  <MoneyInput value={data.tax[k]} onChange={v=>set('tax',k,v)} />
                </Field>
              ))}
            </Row>
          </Section>
        )}

        {activeTab === 'review' && (
          <Section title="9. Review and generate">
            <div className="review-grid">
              <Kpi label="Annual gross salary used" value={fmt(salaryPreview.annualGrossUsed)} />
              <Kpi label="Monthly cash-flow surplus" value={fmt(preview.monthlySurplus)} />
              <Kpi label="Existing SIPs added" value={data.investments.length} />
              <Kpi label="Custom goals added" value={data.goals.length} />
            </div>
            <div className="section-note">
              Generate the plan after all tabs are complete. Recommendations remain capped to available surplus after existing SIPs.
            </div>
          </Section>
        )}

        {err && <div className="err error-block">{err}</div>}

        <div className="actions">
          {currentIndex > 0 && <button type="button" className="link" onClick={goBack}>← Back</button>}
          {currentIndex < tabs.length - 1 && <button type="button" className="primary" onClick={goNext}>Next →</button>}
          {currentIndex === tabs.length - 1 && (
            <button type="submit" disabled={busy} className="primary">
              {busy ? 'Calculating…' : 'Generate FinOS plan'}
            </button>
          )}
          <span className="muted small">Nothing is saved. Refresh to start over.</span>
        </div>
      </form>

      <div ref={resultsRef}>
        {busy && (
          <div className="card center">
            <div className="spinner" />
            <p>Crunching CFP-style numbers…</p>
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
          <h2>FinOS Dashboard</h2>
          {summary.monthlySurplus <= 0 && (
            <div className="err" style={{marginBottom: 12}}>
              Not feasible yet. Expenses consume or exceed income. Fix cash flow before starting new SIPs.
            </div>
          )}
          {summary.warnings?.length > 0 && (
            <ul className="muted small">
              {summary.warnings.map((warning, i) => <li key={i}>{warning}</li>)}
            </ul>
          )}
          <div className="kpi-grid">
            <Kpi label="Net worth" value={fmt(summary.netWorth)} big />
            <Kpi label="Monthly income" value={fmt(summary.monthlyIncome)} />
            <Kpi label="Monthly expenses" value={fmt(summary.monthlyExpenses)} />
            <Kpi label="Monthly surplus" value={fmt(summary.monthlySurplus)} />
            <Kpi label="Existing SIPs" value={fmt(summary.currentMonthlyInvestments)} />
            <Kpi label="Remaining surplus" value={fmt(summary.remainingSurplusAfterExistingInvestments)} />
            <Kpi label="Auto risk" value={summary.riskProfile?.label || '—'} />
            <Kpi label="Tax regime" value={summary.tax?.preferredRegime || '—'} />
          </div>
          {summary.riskProfile && (
            <div className="cashflow-preview success" style={{marginTop: 14}}>
              <div className="cashflow-title">Auto-calculated risk profile</div>
              {summary.riskProfile.label}: {summary.riskProfile.equity}% equity / {summary.riskProfile.debt}% debt / {summary.riskProfile.gold}% gold. {summary.riskProfile.reason}
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
      <div className="muted small">Children</div>
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

function InvestmentEditor({ investments, onChange }) {
  const add = () => {
    onChange([...investments, {
      name: '',
      category: 'flexicap',
      currentValue: '',
      monthlyAmount: '',
      expectedReturnPct: categoryReturnMap.flexicap,
      goal: 'wealth',
    }])
  }

  const update = (i, patch) => {
    const copy = investments.slice()
    const next = { ...copy[i], ...patch }
    if (patch.category) {
      next.expectedReturnPct = categoryReturnMap[patch.category] ?? next.expectedReturnPct
      if (['epf','ppf','nps','retirementSip'].includes(patch.category)) next.goal = 'retirement'
      if (patch.category === 'childEducation') next.goal = 'childEducation'
      if (patch.category === 'elss') next.goal = 'taxSaving'
    }
    copy[i] = next
    onChange(copy)
  }

  const remove = (i) => onChange(investments.filter((_, idx) => idx !== i))

  return (
    <div className="kids">
      {investments.length === 0 && <div className="muted small" style={{marginBottom: 12}}>No SIPs added yet.</div>}
      {investments.map((inv, i) => (
        <div key={i} className="card" style={{padding: 14, marginBottom: 12}}>
          <Row>
            <Field label="Investment name">
              <input value={inv.name} placeholder="Axis small cap SIP, EPF, NPS..."
                onChange={e=>update(i, { name: e.target.value })} />
            </Field>
            <Field label="Category">
              <select value={inv.category} onChange={e=>update(i, { category: e.target.value })}>
                {investmentCategories.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
              </select>
            </Field>
            <Field label="Mapped goal">
              <select value={inv.goal} onChange={e=>update(i, { goal: e.target.value })}>
                {investmentGoals.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
              </select>
            </Field>
          </Row>
          <Row>
            <Field label="Current value">
              <MoneyInput value={inv.currentValue} onChange={v=>update(i, { currentValue: v })} />
            </Field>
            <Field label="Monthly SIP / contribution">
              <MoneyInput value={inv.monthlyAmount} onChange={v=>update(i, { monthlyAmount: v })} />
            </Field>
            <Field label="Expected return %">
              <input type="number" step="0.1" min="0" max="30" value={inv.expectedReturnPct}
                onChange={e=>update(i, { expectedReturnPct: e.target.value === '' ? '' : Number(e.target.value) })} />
            </Field>
            <button type="button" onClick={()=>remove(i)} className="link remove-btn">Remove SIP</button>
          </Row>
        </div>
      ))}
      <button type="button" onClick={add} className="primary">+ Add more SIP / investment</button>
    </div>
  )
}

function GoalEditor({ goals, onChange }) {
  const add = () => onChange([...goals, { name: '', category: 'wealth', presentCost: '', years: '', inflationPct: 6, expectedReturnPct: 9, priority: 'Medium' }])
  const update = (i, patch) => {
    const copy = goals.slice()
    const next = { ...copy[i], ...patch }
    if (patch.category) {
      next.inflationPct = goalInflationMap[patch.category] ?? next.inflationPct
      if (['retirement'].includes(patch.category)) next.priority = 'Critical'
      if (['education','childEducation','medical'].includes(patch.category)) next.priority = 'High'
    }
    copy[i] = next
    onChange(copy)
  }
  const remove = i => onChange(goals.filter((_, idx) => idx !== i))

  return (
    <div className="kids">
      {goals.length === 0 && <div className="muted small" style={{marginBottom: 12}}>No custom goals added. Required retirement, emergency and insurance goals are generated automatically.</div>}
      {goals.map((goal, i) => (
        <div key={i} className="card" style={{padding: 14, marginBottom: 12}}>
          <Row>
            <Field label="Goal name">
              <input value={goal.name} placeholder="Home down payment, MBA, car..."
                onChange={e=>update(i, { name: e.target.value })} />
            </Field>
            <Field label="Category">
              <select value={goal.category} onChange={e=>update(i, { category: e.target.value })}>
                {goalCategories.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
              </select>
            </Field>
            <Field label="Priority">
              <select value={goal.priority} onChange={e=>update(i, { priority: e.target.value })}>
                <option>Critical</option><option>High</option><option>Medium</option><option>Low</option>
              </select>
            </Field>
          </Row>
          <Row>
            <Field label="Cost today">
              <MoneyInput value={goal.presentCost} onChange={v=>update(i, { presentCost: v })} />
            </Field>
            <Field label="Years to goal">
              <input type="number" min="1" max="60" value={goal.years}
                onChange={e=>update(i, { years: e.target.value === '' ? '' : Number(e.target.value) })} />
            </Field>
            <Field label="Inflation %">
              <input type="number" step="0.1" min="0" max="30" value={goal.inflationPct}
                onChange={e=>update(i, { inflationPct: e.target.value === '' ? '' : Number(e.target.value) })} />
            </Field>
            <Field label="Expected return %">
              <input type="number" step="0.1" min="0" max="30" value={goal.expectedReturnPct}
                onChange={e=>update(i, { expectedReturnPct: e.target.value === '' ? '' : Number(e.target.value) })} />
            </Field>
            <button type="button" onClick={()=>remove(i)} className="link remove-btn">Remove goal</button>
          </Row>
        </div>
      ))}
      <button type="button" onClick={add} className="primary">+ Add financial goal</button>
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
  cleaned.basics.kids = cleaned.basics.maritalStatus === 'married'
    ? cleaned.basics.kids
        .filter(kid => kid.name?.trim() || kid.age !== '')
        .map((kid, i) => ({ name: kid.name?.trim() || `Child ${i + 1}`, age: Number(kid.age) || 0 }))
    : []

  cleaned.basics.dependentParentsCount = cleaned.basics.parentsDependent
    ? Math.max(1, Number(cleaned.basics.dependentParentsCount) || 1)
    : 0

  cleaned.salary = Object.fromEntries(Object.entries(cleaned.salary || {}).map(([k, v]) => [k, toNumber(v)]))

  cleaned.investments = cleaned.investments
    .filter(inv => toNumber(inv.currentValue) > 0 || toNumber(inv.monthlyAmount) > 0)
    .map((inv, i) => ({
      name: inv.name?.trim() || `Investment ${i + 1}`,
      category: inv.category,
      currentValue: toNumber(inv.currentValue),
      monthlyAmount: toNumber(inv.monthlyAmount),
      expectedReturnPct: Number(inv.expectedReturnPct) || categoryReturnMap[inv.category] || 8,
      goal: inv.goal || 'wealth',
    }))

  if (toNumber(cleaned.salary?.monthlyEmployeeEpf) > 0) {
    cleaned.investments.push({
      name: 'Auto EPF from salary',
      category: 'epf',
      currentValue: 0,
      monthlyAmount: toNumber(cleaned.salary.monthlyEmployeeEpf),
      expectedReturnPct: categoryReturnMap.epf || 8.25,
      goal: 'retirement',
      source: 'salary',
    })
  }

  if (toNumber(cleaned.salary?.monthlyEmployerNps) > 0) {
    cleaned.investments.push({
      name: 'Auto employer NPS from salary',
      category: 'nps',
      currentValue: 0,
      monthlyAmount: toNumber(cleaned.salary.monthlyEmployerNps),
      expectedReturnPct: categoryReturnMap.nps || 10,
      goal: 'retirement',
      source: 'salary',
    })
  }

  cleaned.goals = cleaned.goals
    .filter(goal => goal.name?.trim() && toNumber(goal.presentCost) > 0 && Number(goal.years) > 0)
    .map(goal => ({
      name: goal.name.trim(),
      category: goal.category,
      presentCost: toNumber(goal.presentCost),
      years: Number(goal.years),
      inflationPct: Number(goal.inflationPct) || goalInflationMap[goal.category] || 6,
      expectedReturnPct: Number(goal.expectedReturnPct) || 9,
      priority: goal.priority || 'Medium',
    }))

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

function getSalaryPreview(profile) {
  const s = profile.salary || {}
  const annualComponents =
    (toNumber(s.monthlyBasic) + toNumber(s.monthlyHra) + toNumber(s.monthlySpecialAllowance) +
      toNumber(s.monthlyLta) + toNumber(s.monthlyBonus) + toNumber(s.monthlyEmployerNps)) * 12
  return {
    annualComponents,
    annualGrossUsed: toNumber(s.annualGross) || annualComponents,
    hraAnnual: toNumber(s.monthlyHra) * 12,
    rentAnnual: toNumber(s.rentPaidMonthly) * 12,
    employeeEpfAnnual: toNumber(s.monthlyEmployeeEpf) * 12,
    employerNpsAnnual: toNumber(s.monthlyEmployerNps) * 12,
  }
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
  return { fixed, variable, annualProrated, emi, monthlyExpenses, monthlySurplus: monthlyIncome - monthlyExpenses }
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
