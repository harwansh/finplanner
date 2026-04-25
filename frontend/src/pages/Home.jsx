
import { useMemo, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { analyze } from '../api/client'

const FY_LABEL = 'FY 2026-27'

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
  liabilities: {
    homeLoan: '', personalLoan: '', educationLoan: '',
    creditCard: '', vehicleLoan: '', otherDebt: ''
  },
  insurance: { life: '', health: '', criticalIllness: '' },
  tax: {
    deduction80C: '',
    nps80CCD1B: '',
    health80D: '',
    homeLoanInterest24B: '',
    homeLoan80EEA: '',
    educationLoan80E: '',
    donation80G: '',
    interest80TTA_TTB: '',
    hraExemption: '',
    ltaExemption: '',
    professionalTax: '',
    otherAnnualIncome: ''
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
  ['marriage', 'Marriage'],
  ['home', 'Home'],
  ['medical', 'Medical'],
  ['travel', 'Travel'],
  ['vehicle', 'Vehicle'],
  ['wealth', 'Wealth creation'],
  ['other', 'Other'],
]

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

const categoryReturnMap = Object.fromEntries(investmentCategories.map(([key, , ret]) => [key, ret]))
const goalInflationMap = {
  retirement: 6,
  education: 10,
  childEducation: 10,
  marriage: 7,
  home: 6,
  medical: 10,
  travel: 6,
  vehicle: 6,
  wealth: 6,
  other: 6,
}

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
  const displayGoals = useMemo(() => getDisplayGoals(data), [data])
  const taxPreview = useMemo(() => computeTaxPreview(data), [data])
  const insurancePreview = useMemo(
    () => computeInsurancePreview(data, preview.monthlyExpenses, displayGoals),
    [data, preview.monthlyExpenses, displayGoals]
  )
  const currentIndex = tabs.findIndex(([key]) => key === activeTab)

  const goNext = () => {
    const tabError = validateTab(activeTab, data)
    if (tabError) {
      setErr(tabError)
      return
    }
    setErr('')
    setActiveTab(tabs[Math.min(currentIndex + 1, tabs.length - 1)][0])
  }

  const goBack = () => {
    setErr('')
    setActiveTab(tabs[Math.max(currentIndex - 1, 0)][0])
  }

  const submit = async (e) => {
    e.preventDefault()
    const validationError = validate(data)
    if (validationError) {
      setErr(validationError)
      setResult(null)
      return
    }

    setBusy(true)
    setErr('')
    setResult(null)
    try {
      const cleaned = cleanProfile(data)
      const r = await analyze(cleaned)
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
        <h2>SmartFinly Planner</h2>
        <p className="muted">
          A CFP-style financial operating system for salary, tax, cash-flow, liabilities,
          insurance, investments, goals and retirement.
        </p>
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
                    setData(d => ({
                      ...d,
                      basics: {
                        ...d.basics,
                        parentsDependent,
                        dependentParentsCount: parentsDependent ? Math.max(1, Number(d.basics.dependentParentsCount) || 1) : 0
                      }
                    }))
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
                Salary inputs are used for tax comparison for {FY_LABEL}. Employee EPF is auto-added to 80C
                and retirement investments. Employer NPS is auto-added to tax and retirement planning.
              </div>
              <Row>
                {Object.keys(data.salary).map(k => (
                  <Field key={k} label={salaryLabels[k] || prettify(k)}>
                    <MoneyInput value={data.salary[k]} onChange={v=>set('salary',k,v)} />
                  </Field>
                ))}
              </Row>
              <div className="cashflow-preview success">
                <div className="cashflow-title">Salary and tax base preview</div>
                <div className="cashflow-grid">
                  <span>Annual salary components: <strong>{fmtMoney(salaryPreview.annualComponents)}</strong></span>
                  <span>Annual gross used: <strong>{fmtMoney(salaryPreview.annualGrossUsed)}</strong></span>
                  <span>Annual HRA received: <strong>{fmtMoney(salaryPreview.hraAnnual)}</strong></span>
                  <span>Annual rent paid: <strong>{fmtMoney(salaryPreview.rentAnnual)}</strong></span>
                  <span>Employee EPF auto 80C: <strong>{fmtMoney(salaryPreview.employeeEpfAnnual)}</strong></span>
                  <span>Employer NPS auto retirement: <strong>{fmtMoney(salaryPreview.employerNpsAnnual)}</strong></span>
                </div>
              </div>
            </Section>

            <Section title="3. Cash-flow">
              <Row>
                <Field label="Monthly income after tax" required hint="Example: 2,00,000">
                  <MoneyInput value={data.income.monthlyAfterTax} onChange={v=>set('income','monthlyAfterTax',v)} required />
                </Field>
                <Field label="Annual bonus / variable">
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
                <Field label="Annual lump sums" required hint="Insurance, vacations, school fees / year">
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
              Add only your emergency fund and debts here. Put all investment/current corpus values in
              “Existing investments and SIPs” to avoid duplicate counting.
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
            <div className="section-note">
              Enter your current covers. SmartFinly will show the estimated required life cover and health cover.
            </div>
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
            <div className="section-note">
              This is the single source for investment/current corpus values: EPF, PPF, NPS, mutual funds,
              smallcase, stocks, FD/RD, gold, real estate and SIPs. Return % is auto-filled by category but editable.
            </div>
            <InvestmentEditor investments={data.investments} onChange={v=>setTop('investments', v)} />
          </Section>
        )}

        {activeTab === 'goals' && (
          <Section title="7. Goals">
            <div className="section-note">
              Add custom goals here. Child higher education at age 17 and child marriage at age 22 are auto-created
              in planning if kids are added in the profile section.
            </div>
            <GoalEditor goals={data.goals} onChange={v=>setTop('goals', v)} />
            {displayGoals.filter(g => g.auto).length > 0 && (
              <div className="auto-goal-box">
                <div className="goal-box-title">Auto-added child goals</div>
                <ul className="auto-goal-list">
                  {displayGoals.filter(g => g.auto).map(goal => (
                    <li key={goal.id}>{goal.name} · {goal.years} years · Today need {fmtMoney(goal.todayNeed)} · Future need {fmtMoney(goal.futureNeed)}</li>
                  ))}
                </ul>
              </div>
            )}
          </Section>
        )}

        {activeTab === 'tax' && (
          <Section title={`8. Tax inputs ${FY_LABEL}`}>
            <div className="section-note">
              Old vs new regime is calculated for {FY_LABEL}. Salary details from the Salary tab are used automatically
              for HRA, employer NPS, EPF and professional tax where possible.
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
              <Kpi label="FY" value={FY_LABEL} />
              <Kpi label="Annual gross salary used" value={fmtMoney(taxPreview.grossIncome)} />
              <Kpi label="Monthly cash-flow surplus" value={fmtMoney(preview.monthlySurplus)} />
              <Kpi label="Goals included" value={fmtCount(displayGoals.length)} />
            </div>
            <div className="section-note">
              Generate the plan after all tabs are complete. Output will show tax calculation, insurance calculation,
              auto-added child goals, today need vs future need, and graphical summaries.
            </div>
          </Section>
        )}

        {err && <div className="err error-block">{err}</div>}

        <div className="actions">
          {currentIndex > 0 && <button type="button" className="link" onClick={goBack}>← Back</button>}
          {currentIndex < tabs.length - 1 && <button type="button" className="primary" onClick={goNext}>Next →</button>}
          {currentIndex === tabs.length - 1 && (
            <button type="submit" disabled={busy} className="primary">
              {busy ? 'Calculating…' : 'Generate SmartFinly plan'}
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
        {result && (
          <Results
            result={result}
            inputData={data}
            cashflowPreview={preview}
            taxPreview={taxPreview}
            insurancePreview={insurancePreview}
            displayGoals={displayGoals}
          />
        )}
      </div>
    </>
  )
}

function Results({ result, inputData, cashflowPreview, taxPreview, insurancePreview, displayGoals }) {
  const { summary, plan, report, error } = result || {}
  const tax = summary?.tax || taxPreview
  const insurance = summary?.insurance || insurancePreview
  const outputGoals = buildOutputGoalsFromPlan(plan?.goals, displayGoals)

  const monthlyIncome = summary?.monthlyIncome ?? cashflowPreview.monthlyIncome
  const monthlyExpenses = summary?.monthlyExpenses ?? cashflowPreview.monthlyExpenses
  const currentMonthlyInvestments = summary?.currentMonthlyInvestments ?? getCurrentMonthlyInvestments(inputData)
  const remainingSurplus = summary?.remainingSurplusAfterExistingInvestments ?? (cashflowPreview.monthlySurplus - currentMonthlyInvestments)

  return (
    <div className="results">
      <div className="card">
        <div className="result-header">
          <div>
            <div className="result-eyebrow">Planner dashboard</div>
            <h2>SmartFinly Output</h2>
            <div className="muted">{FY_LABEL} aligned calculations with tax, insurance, goals and monthly planning</div>
          </div>
        </div>

        {summary?.warnings?.length > 0 && (
          <ul className="muted small" style={{marginTop: 10}}>
            {summary.warnings.map((warning, i) => <li key={i}>{warning}</li>)}
          </ul>
        )}

        <div className="kpi-grid">
          <Kpi label="Net worth" value={fmtMoney(summary?.netWorth)} big />
          <Kpi label="Monthly income" value={fmtMoney(monthlyIncome)} />
          <Kpi label="Monthly expenses" value={fmtMoney(monthlyExpenses)} />
          <Kpi label="Monthly surplus" value={fmtMoney(summary?.monthlySurplus ?? cashflowPreview.monthlySurplus)} />
          <Kpi label="Existing SIPs" value={fmtMoney(currentMonthlyInvestments)} />
          <Kpi label="Free surplus" value={fmtMoney(remainingSurplus)} />
          <Kpi label="Preferred regime" value={tax?.preferredRegime || '—'} />
          <Kpi label="Auto risk" value={summary?.riskProfile?.label || '—'} />
        </div>
      </div>

      <div className="visual-grid">
        <ChartCard title="Cash-flow picture" subtitle="Graphical view of money in and money out">
          <MetricRow label="Income" current={monthlyIncome} max={Math.max(monthlyIncome, monthlyExpenses, currentMonthlyInvestments, remainingSurplus, 1)} />
          <MetricRow label="Expenses" current={monthlyExpenses} max={Math.max(monthlyIncome, monthlyExpenses, currentMonthlyInvestments, remainingSurplus, 1)} danger />
          <MetricRow label="Existing SIPs" current={currentMonthlyInvestments} max={Math.max(monthlyIncome, monthlyExpenses, currentMonthlyInvestments, remainingSurplus, 1)} />
          <MetricRow label="Free surplus" current={Math.max(remainingSurplus, 0)} max={Math.max(monthlyIncome, monthlyExpenses, currentMonthlyInvestments, remainingSurplus, 1)} accent />
        </ChartCard>

        <ChartCard title={`Tax calculation • ${FY_LABEL}`} subtitle="Old vs new regime comparison">
          <div className="mini-kpi-grid">
            <MiniKpi label="Gross income" value={fmtMoney(tax?.grossIncome)} />
            <MiniKpi label="Old tax" value={fmtMoney(tax?.oldTax)} />
            <MiniKpi label="New tax" value={fmtMoney(tax?.newTax)} />
            <MiniKpi label="Savings" value={fmtMoney(tax?.savingsVsOther)} />
          </div>
          <MetricRow label="Old regime tax" current={tax?.oldTax} max={Math.max(tax?.oldTax || 0, tax?.newTax || 0, 1)} />
          <MetricRow label="New regime tax" current={tax?.newTax} max={Math.max(tax?.oldTax || 0, tax?.newTax || 0, 1)} accent />
          <div className="chart-note">
            Preferred regime: <strong>{tax?.preferredRegime || '-'}</strong> ·
            Taxable income old {fmtMoney(tax?.oldTaxable)} ·
            Taxable income new {fmtMoney(tax?.newTaxable)}
          </div>
          <TaxSlabTable title="Old regime slab-wise tax" rows={tax?.oldSlabBreakdown} rebate={tax?.oldRebate} cess={tax?.oldCess} />
          <TaxSlabTable title="New regime slab-wise tax" rows={tax?.newSlabBreakdown} rebate={tax?.newRebate} cess={tax?.newCess} />
        </ChartCard>

        <ChartCard title="Insurance calculation" subtitle="Current cover vs estimated requirement">
          <div className="mini-kpi-grid">
            <MiniKpi label="Current life cover" value={fmtMoney(insurance?.currentLifeCover)} />
            <MiniKpi label="Required life cover" value={fmtMoney(insurance?.recommendedLifeCover)} />
            <MiniKpi label="Current health cover" value={fmtMoney(insurance?.currentHealthCover)} />
            <MiniKpi label="Required health cover" value={fmtMoney(insurance?.recommendedHealthCover)} />
          </div>
          <MetricRow label="Life cover" current={insurance?.currentLifeCover} max={Math.max(insurance?.recommendedLifeCover || 0, insurance?.currentLifeCover || 0, 1)} />
          <MetricRow label="Required life" current={insurance?.recommendedLifeCover} max={Math.max(insurance?.recommendedLifeCover || 0, insurance?.currentLifeCover || 0, 1)} accent />
          <MetricRow label="Health cover" current={insurance?.currentHealthCover} max={Math.max(insurance?.recommendedHealthCover || 0, insurance?.currentHealthCover || 0, 1)} />
          <MetricRow label="Required health" current={insurance?.recommendedHealthCover} max={Math.max(insurance?.recommendedHealthCover || 0, insurance?.currentHealthCover || 0, 1)} accent />
          <div className="chart-note">{insurance?.note}</div>
        </ChartCard>

        <ChartCard title="Goal summary" subtitle="Today need vs future need">
          <div className="goal-summary-table">
            <div className="goal-summary-head">
              <span>Goal</span>
              <span>Years</span>
              <span>Today need</span>
              <span>Future need</span>
            </div>
            {outputGoals.length === 0 && <div className="goal-empty muted">No goals returned yet.</div>}
            {outputGoals.map(goal => (
              <div key={goal.id} className="goal-summary-row">
                <span>{goal.name}{goal.auto && <em className="goal-auto-tag">auto</em>}</span>
                <span>{goal.years}</span>
                <span>{fmtMoney(goal.todayNeed)}</span>
                <span>{fmtMoney(goal.futureNeed)}</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      {error && <div className="card err">{error}</div>}

      {report && (
        <div className="card markdown">
          <div className="report-header-line">
            <strong>Detailed report</strong>
            <span className="muted">{FY_LABEL}</span>
          </div>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}

function MetricRow({ label, current, max, danger = false, accent = false }) {
  const safeCurrent = Number(current) || 0
  const safeMax = Math.max(Number(max) || 1, 1)
  const pct = Math.max(0, Math.min(100, (safeCurrent / safeMax) * 100))
  return (
    <div className="metric-row">
      <div className="metric-top">
        <span>{label}</span>
        <strong>{fmtMoney(safeCurrent)}</strong>
      </div>
      <div className="metric-track">
        <div
          className={`metric-fill ${danger ? 'danger' : accent ? 'accent' : ''}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function MiniKpi({ label, value }) {
  return (
    <div className="mini-kpi">
      <div className="mini-kpi-label">{label}</div>
      <div className="mini-kpi-value">{value}</div>
    </div>
  )
}

function ChartCard({ title, subtitle, children }) {
  return (
    <div className="card chart-card">
      <div className="chart-card-head">
        <div className="chart-title">{title}</div>
        <div className="chart-subtitle">{subtitle}</div>
      </div>
      {children}
    </div>
  )
}


function TaxSlabTable({ title, rows = [], rebate = 0, cess = 0 }) {
  if (!rows || rows.length === 0) return null
  return (
    <div className="slab-table-wrap">
      <div className="slab-title">{title}</div>
      <div className="slab-table">
        <div className="slab-row slab-head">
          <span>Slab</span>
          <span>Rate</span>
          <span>Amount</span>
          <span>Tax</span>
        </div>
        {rows.map((row, index) => (
          <div className="slab-row" key={`${title}-${index}`}>
            <span>{row.range}</span>
            <span>{row.ratePct}%</span>
            <span>{fmtMoney(row.taxableAmount)}</span>
            <span>{fmtMoney(row.tax)}</span>
          </div>
        ))}
        <div className="slab-row slab-foot">
          <span>Rebate</span><span>-</span><span>-</span><span>-{fmtMoney(rebate)}</span>
        </div>
        <div className="slab-row slab-foot">
          <span>Cess</span><span>4%</span><span>-</span><span>{fmtMoney(cess)}</span>
        </div>
      </div>
    </div>
  )
}

function buildOutputGoalsFromPlan(planGoals, fallbackGoals) {
  const source = Array.isArray(planGoals) && planGoals.length ? planGoals : fallbackGoals
  return (source || []).map((goal, index) => {
    const todayNeed = toNumber(goal.presentCost ?? goal.todayNeed)
    const futureNeed = toNumber(goal.futureCost ?? goal.futureNeed)
    return {
      id: goal.name || `goal-${index}`,
      name: goal.name || `Goal ${index + 1}`,
      years: goal.years ?? extractYears(goal.timeline),
      todayNeed,
      futureNeed,
      auto: Boolean(goal.auto) || goal.type === 'Auto-added' || /education|marriage/i.test(goal.name || ''),
    }
  })
}

function extractYears(timeline) {
  const match = String(timeline || '').match(/(\d+)/)
  return match ? Number(match[1]) : '-'
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
    const copy = kids.slice()
    copy[i] = { ...copy[i], [k]: v }
    onChange(copy)
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
        <div key={i} className="card compact-card">
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
      {goals.length === 0 && <div className="muted small" style={{marginBottom: 12}}>No custom goals added yet.</div>}
      {goals.map((goal, i) => (
        <div key={i} className="card compact-card">
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
        <span>Fixed: <strong>{fmtMoney(preview.fixed)}</strong></span>
        <span>Variable: <strong>{fmtMoney(preview.variable)}</strong></span>
        <span>Annual / month: <strong>{fmtMoney(preview.annualProrated)}</strong></span>
        <span>EMI: <strong>{fmtMoney(preview.emi)}</strong></span>
      </div>
      <div className="cashflow-total">
        Expenses: <strong>{fmtMoney(preview.monthlyExpenses)}</strong> · Surplus: <strong>{fmtMoney(preview.monthlySurplus)}</strong>
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

function validateTab(tab, profile) {
  switch (tab) {
    case 'profile':
      return validateProfileTab(profile)
    case 'salary':
      return validateSalaryCashflowTab(profile)
    case 'debt':
      return validateDebtTab(profile)
    case 'insurance':
      return ''
    case 'investments':
      return ''
    case 'goals':
      return validateGoalsTab(profile)
    case 'tax':
      return ''
    case 'review':
      return validate(profile)
    default:
      return ''
  }
}

function validateProfileTab(profile) {
  if (!Number(profile.basics.age) || Number(profile.basics.age) < 18) {
    return 'Please enter a valid current age before continuing.'
  }
  if (!Number(profile.basics.desiredRetirementAge)) {
    return 'Please enter desired retirement age before continuing.'
  }
  if (Number(profile.basics.desiredRetirementAge) <= Number(profile.basics.age)) {
    return 'Desired retirement age must be greater than current age.'
  }
  if (!String(profile.basics.country || '').trim()) {
    return 'Please enter country before continuing.'
  }
  if (!profile.basics.cityTier) {
    return 'Please select city type before continuing.'
  }
  if (!profile.basics.maritalStatus) {
    return 'Please select marital status before continuing.'
  }
  if (!profile.basics.employmentType) {
    return 'Please select employment type before continuing.'
  }
  if (profile.basics.parentsDependent && Number(profile.basics.dependentParentsCount) < 1) {
    return 'Please enter at least 1 dependent parent, or select "No" for parent dependency.'
  }
  const partialKid = (profile.basics.kids || []).find(kid => Boolean(kid.name?.trim()) !== (kid.age !== ''))
  if (profile.basics.maritalStatus === 'married' && partialKid) {
    return 'Please enter both name and age for each child, or remove the incomplete child row.'
  }
  return ''
}

function validateSalaryCashflowTab(profile) {
  if (!Number(profile.income.monthlyAfterTax) || Number(profile.income.monthlyAfterTax) <= 0) {
    return 'Please enter monthly income after tax before continuing.'
  }
  if (profile.expenses.fixed === '' || profile.expenses.fixed == null) {
    return 'Please enter fixed monthly expenses. Enter 0 if not applicable.'
  }
  if (profile.expenses.variable === '' || profile.expenses.variable == null) {
    return 'Please enter variable monthly expenses. Enter 0 if not applicable.'
  }
  if (profile.expenses.annual === '' || profile.expenses.annual == null) {
    return 'Please enter annual lump-sum expenses. Enter 0 if not applicable.'
  }
  if (profile.monthlyEmi === '' || profile.monthlyEmi == null) {
    return 'Please enter total monthly EMIs. Enter 0 if not applicable.'
  }
  const preview = getCashflowPreview(profile)
  if (!Number.isFinite(Number(preview.monthlySurplus))) {
    return 'Please check income and expense values before continuing.'
  }
  return ''
}

function validateDebtTab(profile) {
  if (profile.emergencyFund === '' || profile.emergencyFund == null) {
    return 'Please enter emergency fund amount. Enter 0 if none.'
  }
  return ''
}

function validateGoalsTab(profile) {
  const badGoal = (profile.goals || []).find(goal => {
    const hasAny = goal.name?.trim() || goal.presentCost !== '' || goal.years !== ''
    if (!hasAny) return false
    return !goal.name?.trim() || !Number(goal.presentCost) || !Number(goal.years)
  })

  if (badGoal) {
    return 'Please complete each added goal with name, cost today and years to goal, or remove the incomplete goal.'
  }
  return ''
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

  const manualGoals = cleaned.goals
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

  const autoGoals = buildAutoGoals(cleaned)
  const existingNames = new Set(manualGoals.map(g => g.name.toLowerCase()))
  cleaned.goals = [
    ...manualGoals,
    ...autoGoals
      .filter(g => !existingNames.has(g.name.toLowerCase()))
      .map(g => ({
        name: g.name,
        category: g.category,
        presentCost: g.presentCost,
        years: g.years,
        inflationPct: g.inflationPct,
        expectedReturnPct: g.expectedReturnPct,
        priority: g.priority,
      }))
  ]

  return cleaned
}

function buildAutoGoals(profile) {
  const kids = (profile.basics?.kids || []).filter(kid => kid.name?.trim() || kid.age !== '')
  const autoGoals = []

  kids.forEach((kid, i) => {
    const name = kid.name?.trim() || `Child ${i + 1}`
    const age = Number(kid.age) || 0

    autoGoals.push({
      id: `${name}-education`,
      name: `${name} higher education`,
      category: 'childEducation',
      presentCost: 2500000,
      years: Math.max(1, 17 - age),
      inflationPct: 10,
      expectedReturnPct: 10,
      priority: 'High',
      auto: true,
    })

    autoGoals.push({
      id: `${name}-marriage`,
      name: `${name} marriage`,
      category: 'marriage',
      presentCost: 1500000,
      years: Math.max(1, 22 - age),
      inflationPct: 7,
      expectedReturnPct: 9,
      priority: 'Medium',
      auto: true,
    })
  })

  return autoGoals
}

function getDisplayGoals(profile) {
  const manualGoals = (profile.goals || [])
    .filter(goal => goal.name?.trim() && toNumber(goal.presentCost) > 0 && Number(goal.years) > 0)
    .map((goal, index) => ({
      id: `manual-${index}`,
      name: goal.name.trim(),
      category: goal.category,
      presentCost: toNumber(goal.presentCost),
      years: Number(goal.years),
      inflationPct: Number(goal.inflationPct) || goalInflationMap[goal.category] || 6,
      expectedReturnPct: Number(goal.expectedReturnPct) || 9,
      priority: goal.priority || 'Medium',
      auto: false,
    }))

  const autoGoals = buildAutoGoals(profile)
  const existingNames = new Set(manualGoals.map(g => g.name.toLowerCase()))
  const merged = [
    ...manualGoals,
    ...autoGoals.filter(g => !existingNames.has(g.name.toLowerCase()))
  ].map(goal => ({
    ...goal,
    todayNeed: goal.presentCost,
    futureNeed: futureValue(goal.presentCost, goal.years, goal.inflationPct),
  }))

  return merged.sort((a, b) => a.years - b.years)
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
  return {
    fixed,
    variable,
    annualProrated,
    emi,
    monthlyIncome,
    monthlyExpenses,
    monthlySurplus: monthlyIncome - monthlyExpenses
  }
}

function computeTaxPreview(profile) {
  const income = profile.income || {}
  const salary = profile.salary || {}
  const basics = profile.basics || {}
  const tax = profile.tax || {}

  const basicAnnual = toNumber(salary.monthlyBasic) * 12
  const hraReceived = toNumber(salary.monthlyHra) * 12
  const ltaReceived = toNumber(salary.monthlyLta) * 12
  const specialAllowance = toNumber(salary.monthlySpecialAllowance) * 12
  const monthlyBonus = toNumber(salary.monthlyBonus) * 12
  const employerNps = toNumber(salary.monthlyEmployerNps) * 12
  const employeeEpf = toNumber(salary.monthlyEmployeeEpf) * 12
  const salaryProfessionalTax = toNumber(salary.monthlyProfessionalTax) * 12
  const rentPaid = toNumber(salary.rentPaidMonthly) * 12
  const annualGrossOverride = toNumber(salary.annualGross)

  const salaryComponentsTotal = basicAnnual + hraReceived + ltaReceived + specialAllowance + monthlyBonus + employerNps
  const fallbackIncome = (toNumber(income.monthlyAfterTax) + toNumber(income.otherMonthly)) * 12 + toNumber(income.bonusAnnual)
  const grossIncome = (annualGrossOverride || salaryComponentsTotal || fallbackIncome) + toNumber(tax.otherAnnualIncome)

  const standardOld = 50000
  const standardNew = 75000

  const metroRatio = ['Metro', 'Tier 1'].includes(basics.cityTier) ? 0.50 : 0.40
  let autoHraExemption = 0
  if (hraReceived > 0 && basicAnnual > 0 && rentPaid > 0) {
    autoHraExemption = Math.max(
      0,
      Math.min(
        hraReceived,
        Math.max(0, rentPaid - 0.10 * basicAnnual),
        metroRatio * basicAnnual
      )
    )
  }

  const hra = toNumber(tax.hraExemption) || autoHraExemption
  const professionalTax = toNumber(tax.professionalTax) + salaryProfessionalTax
  const deduction80C = Math.min(150000, toNumber(tax.deduction80C) + employeeEpf)
  const deduction80CCD1B = Math.min(50000, toNumber(tax.nps80CCD1B))
  const deduction80D = toNumber(tax.health80D)
  const deduction80G = toNumber(tax.donation80G)
  const deduction80E = toNumber(tax.educationLoan80E)
  const deduction80TTA_TTB = toNumber(tax.interest80TTA_TTB)
  const deduction80EEA = Math.min(150000, toNumber(tax.homeLoan80EEA))
  const section24B = Math.min(200000, toNumber(tax.homeLoanInterest24B))
  const lta = toNumber(tax.ltaExemption) || ltaReceived

  const employerNpsOld = basicAnnual > 0 ? Math.min(employerNps, basicAnnual * 0.10) : employerNps
  const employerNpsNew = basicAnnual > 0 ? Math.min(employerNps, basicAnnual * 0.14) : employerNps

  const oldDeductions = standardOld + hra + lta + professionalTax + deduction80C + deduction80CCD1B + employerNpsOld + deduction80D + deduction80G + deduction80E + deduction80TTA_TTB + deduction80EEA + section24B
  const newDeductions = standardNew + employerNpsNew

  const oldTaxable = Math.max(0, grossIncome - oldDeductions)
  const newTaxable = Math.max(0, grossIncome - newDeductions)

  const oldRows = slabRows(oldTaxable, [[250000, 0], [500000, 0.05], [1000000, 0.20], [Infinity, 0.30]])
  const newRows = slabRows(newTaxable, [[400000, 0], [800000, 0.05], [1200000, 0.10], [1600000, 0.15], [2000000, 0.20], [2400000, 0.25], [Infinity, 0.30]])
  const oldBeforeRebate = oldRows.reduce((sum, row) => sum + row.tax, 0)
  const newBeforeRebate = newRows.reduce((sum, row) => sum + row.tax, 0)
  const oldRebate = oldTaxable <= 500000 ? oldBeforeRebate : 0
  const newRebate = newTaxable <= 1200000 ? newBeforeRebate : 0
  let oldTax = Math.max(0, oldBeforeRebate - oldRebate)
  let newTax = Math.max(0, newBeforeRebate - newRebate)

  if (oldTaxable <= 500000) oldTax = 0
  if (newTaxable <= 1200000) newTax = 0

  oldTax = oldTax * 1.04
  newTax = newTax * 1.04

  return {
    fyLabel: FY_LABEL,
    grossIncome,
    salaryComponentsTotal,
    oldDeductions,
    newDeductions,
    oldTaxable,
    newTaxable,
    oldTax,
    newTax,
    oldSlabBreakdown: oldRows,
    newSlabBreakdown: newRows,
    oldRebate,
    newRebate,
    oldCess: oldTax * 0.04 / 1.04,
    newCess: newTax * 0.04 / 1.04,
    preferredRegime: oldTax < newTax ? 'Old' : 'New',
    savingsVsOther: Math.abs(oldTax - newTax),
  }
}


function slabRows(taxable, slabs) {
  const rows = []
  let previous = 0
  for (const [limit, rate] of slabs) {
    if (taxable <= previous) break
    const taxableAmount = Math.max(0, Math.min(taxable, limit) - previous)
    rows.push({
      range: `${fmtMoney(previous)} to ${limit === Infinity ? 'Above' : fmtMoney(limit)}`,
      ratePct: rate * 100,
      taxableAmount,
      tax: taxableAmount * rate,
    })
    previous = limit
  }
  return rows
}

function slabTaxOld(taxable) {
  let tax = 0
  if (taxable > 250000) tax += Math.min(taxable, 500000) - 250000 > 0 ? (Math.min(taxable, 500000) - 250000) * 0.05 : 0
  if (taxable > 500000) tax += (Math.min(taxable, 1000000) - 500000) * 0.20
  if (taxable > 1000000) tax += (taxable - 1000000) * 0.30
  return Math.max(0, tax)
}

function slabTaxNewFY2627(taxable) {
  const slabs = [
    [400000, 0.00],
    [800000, 0.05],
    [1200000, 0.10],
    [1600000, 0.15],
    [2000000, 0.20],
    [2400000, 0.25],
    [Infinity, 0.30],
  ]
  let previous = 0
  let tax = 0
  for (const [limit, rate] of slabs) {
    if (taxable <= previous) break
    const taxableInSlab = Math.min(taxable, limit) - previous
    tax += taxableInSlab * rate
    previous = limit
  }
  return tax
}

function computeInsurancePreview(profile, monthlyExpenses, goals) {
  const basics = profile.basics || {}
  const liabilities = profile.liabilities || {}
  const insurance = profile.insurance || {}
  const kidsCount = (basics.kids || []).filter(k => k.name?.trim() || k.age !== '').length
  const spouseCount = basics.maritalStatus === 'married' ? 1 : 0
  const parents = basics.parentsDependent ? Math.max(1, Number(basics.dependentParentsCount) || 1) : 0
  const dependents = spouseCount + kidsCount + parents
  const liabilitiesTotal = Object.values(liabilities).reduce((sum, v) => sum + toNumber(v), 0)
  const annualExpenses = (Number(monthlyExpenses) || 0) * 12
  const dependentGoalTodayNeed = (goals || [])
    .filter(goal => ['childEducation', 'marriage', 'education', 'medical', 'home'].includes(goal.category))
    .reduce((sum, goal) => sum + toNumber(goal.todayNeed), 0)

  const currentLifeCover = toNumber(insurance.life)
  const currentHealthCover = toNumber(insurance.health)

  let recommendedLifeCover = 0
  let note = ''

  if (dependents > 0) {
    recommendedLifeCover = liabilitiesTotal + annualExpenses * 15 + dependentGoalTodayNeed
    note = 'Because you have dependents, term cover should ideally protect liabilities, 15 years of family expenses and major family goals.'
  } else {
    recommendedLifeCover = Math.max(liabilitiesTotal + annualExpenses * 5, liabilitiesTotal)
    note = 'If you have no financial dependents, life insurance is generally good to have rather than critical, but liabilities and some income replacement can still be protected.'
  }

  const recommendedHealthCover =
    1000000 +
    (spouseCount > 0 ? 500000 : 0) +
    (kidsCount * 500000) +
    (parents * 500000)

  return {
    currentLifeCover,
    recommendedLifeCover,
    lifeGap: Math.max(0, recommendedLifeCover - currentLifeCover),
    currentHealthCover,
    recommendedHealthCover,
    healthGap: Math.max(0, recommendedHealthCover - currentHealthCover),
    note,
  }
}

function getCurrentMonthlyInvestments(profile) {
  const direct = (profile.investments || []).reduce((sum, inv) => sum + toNumber(inv.monthlyAmount), 0)
  const autoEpf = toNumber(profile.salary?.monthlyEmployeeEpf)
  const autoNps = toNumber(profile.salary?.monthlyEmployerNps)
  return direct + autoEpf + autoNps
}

function futureValue(present, years, inflationPct) {
  return present * Math.pow(1 + (Number(inflationPct) || 0) / 100, Number(years) || 0)
}

function parseIndianNumber(value) {
  const raw = String(value || '').replace(/,/g, '').trim()
  if (!raw) return ''

  // Keep only digits and the first decimal point.
  const cleaned = raw
    .replace(/[^0-9.]/g, '')
    .replace(/(\\..*)\\./g, '$1')

  if (!cleaned || cleaned === '.') return ''
  const n = Number(cleaned)
  return Number.isFinite(n) ? n : ''
}

function formatIndianNumber(value) {
  if (value === '' || value == null) return ''
  const n = Number(value)
  if (!Number.isFinite(n)) return ''

  const hasDecimals = String(value).includes('.') && !Number.isInteger(n)
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: hasDecimals ? 2 : 0,
    maximumFractionDigits: 2,
  }).format(n)
}

function toNumber(value) {
  return value === '' || value == null ? 0 : Number(value)
}

function prettify(k) {
  return k.replace(/([A-Z])/g, ' $1').replace(/^./, c => c.toUpperCase())
}

function fmtMoney(n) {
  if (n == null || isNaN(n)) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(Number(n))
}

function fmtCount(n) {
  if (n == null || isNaN(n)) return '—'
  return new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(Number(n))
}
