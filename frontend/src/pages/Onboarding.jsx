import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getProfile, saveProfile } from '../api/client'

const empty = {
  basics: {
    age: '', country: '', city: '', maritalStatus: 'single',
    employmentType: 'salaried', dependentsCount: 0, kids: []
  },
  income: { monthlyAfterTax: '', bonusAnnual: '', otherMonthly: '', expectedGrowthPct: '' },
  expenses: { fixed: '', variable: '', annual: '' },
  assets: { savings: '', stocks: '', mutualFunds: '', crypto: '', gold: '', realEstate: '', retirement: '' },
  liabilities: { homeLoan: '', personalLoan: '', creditCard: '', otherDebt: '', avgInterestPct: '' },
  risk: 'moderate',
  insurance: { life: '', health: '', disability: '' },
  preferences: { ethical: '', religious: '', preferredAssets: '', timePerWeekHours: '' },
  behavior: { spendingHabit: 'disciplined', savingsConsistent: true, pastMistakes: '', knowledgeLevel: 'intermediate' }
}

const steps = [
  'Basics', 'Income', 'Expenses', 'Assets', 'Liabilities',
  'Risk', 'Insurance', 'Preferences', 'Behavior', 'Review'
]

export default function Onboarding() {
  const [data, setData] = useState(empty)
  const [step, setStep] = useState(0)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    getProfile().then(p => { if (p) setData({ ...empty, ...p }) }).catch(()=>{})
  }, [])

  const set = (section, field, val) =>
    setData(d => ({ ...d, [section]: { ...d[section], [field]: val } }))

  const submit = async () => {
    setBusy(true); setErr('')
    try {
      await saveProfile(data)
      navigate('/dashboard')
    } catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  const num = (v) => v === '' || v == null ? '' : Number(v)

  return (
    <div className="card">
      <div className="stepper">
        {steps.map((s,i) => (
          <span key={s} className={i===step ? 'active' : i<step ? 'done' : ''}>{i+1}. {s}</span>
        ))}
      </div>

      {step === 0 && (
        <section>
          <h3>Basic profile</h3>
          <Row>
            <Field label="Age"><input type="number" value={data.basics.age}
              onChange={e=>set('basics','age',num(e.target.value))} /></Field>
            <Field label="Country"><input value={data.basics.country}
              onChange={e=>set('basics','country',e.target.value)} placeholder="India" /></Field>
            <Field label="City"><input value={data.basics.city}
              onChange={e=>set('basics','city',e.target.value)} placeholder="Bengaluru" /></Field>
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
            <Field label="Employment type">
              <select value={data.basics.employmentType}
                onChange={e=>set('basics','employmentType',e.target.value)}>
                <option value="salaried">Salaried</option>
                <option value="business">Business owner</option>
                <option value="freelance">Freelance / contractor</option>
              </select>
            </Field>
            <Field label="# Dependents (incl. kids)">
              <input type="number" min="0" value={data.basics.dependentsCount}
                onChange={e=>set('basics','dependentsCount',num(e.target.value))} />
            </Field>
          </Row>
          {data.basics.maritalStatus === 'married' && (
            <KidsEditor kids={data.basics.kids}
              onChange={(kids)=>set('basics','kids',kids)} />
          )}
        </section>
      )}

      {step === 1 && (
        <section>
          <h3>Income</h3>
          <Row>
            <Field label="Monthly income (after tax)">
              <input type="number" value={data.income.monthlyAfterTax}
                onChange={e=>set('income','monthlyAfterTax',num(e.target.value))} />
            </Field>
            <Field label="Annual bonus / variable">
              <input type="number" value={data.income.bonusAnnual}
                onChange={e=>set('income','bonusAnnual',num(e.target.value))} />
            </Field>
          </Row>
          <Row>
            <Field label="Other monthly income (rent, freelance, dividends)">
              <input type="number" value={data.income.otherMonthly}
                onChange={e=>set('income','otherMonthly',num(e.target.value))} />
            </Field>
            <Field label="Expected income growth % / yr">
              <input type="number" value={data.income.expectedGrowthPct}
                onChange={e=>set('income','expectedGrowthPct',num(e.target.value))} />
            </Field>
          </Row>
        </section>
      )}

      {step === 2 && (
        <section>
          <h3>Expenses (per month)</h3>
          <Row>
            <Field label="Fixed (rent, EMI, school fees)"><input type="number" value={data.expenses.fixed}
              onChange={e=>set('expenses','fixed',num(e.target.value))} /></Field>
            <Field label="Variable (food, travel, shopping)"><input type="number" value={data.expenses.variable}
              onChange={e=>set('expenses','variable',num(e.target.value))} /></Field>
            <Field label="Annual lump sums (insurance, vacations) / yr"><input type="number" value={data.expenses.annual}
              onChange={e=>set('expenses','annual',num(e.target.value))} /></Field>
          </Row>
        </section>
      )}

      {step === 3 && (
        <section>
          <h3>Assets (current value)</h3>
          {Object.keys(empty.assets).map(k => (
            <Row key={k}>
              <Field label={prettify(k)}>
                <input type="number" value={data.assets[k]}
                  onChange={e=>set('assets',k,num(e.target.value))} />
              </Field>
            </Row>
          ))}
        </section>
      )}

      {step === 4 && (
        <section>
          <h3>Liabilities (outstanding balance)</h3>
          {['homeLoan','personalLoan','creditCard','otherDebt'].map(k => (
            <Row key={k}>
              <Field label={prettify(k)}>
                <input type="number" value={data.liabilities[k]}
                  onChange={e=>set('liabilities',k,num(e.target.value))} />
              </Field>
            </Row>
          ))}
          <Field label="Average interest rate % across debt">
            <input type="number" value={data.liabilities.avgInterestPct}
              onChange={e=>set('liabilities','avgInterestPct',num(e.target.value))} />
          </Field>
        </section>
      )}

      {step === 5 && (
        <section>
          <h3>Risk tolerance</h3>
          {['conservative','moderate','aggressive'].map(r => (
            <label key={r} className="radio">
              <input type="radio" checked={data.risk===r}
                onChange={()=>setData(d=>({...d, risk:r}))} /> {r}
            </label>
          ))}
        </section>
      )}

      {step === 6 && (
        <section>
          <h3>Insurance coverage (sum assured)</h3>
          <Row>
            <Field label="Life cover"><input type="number" value={data.insurance.life}
              onChange={e=>set('insurance','life',num(e.target.value))} /></Field>
            <Field label="Health cover"><input type="number" value={data.insurance.health}
              onChange={e=>set('insurance','health',num(e.target.value))} /></Field>
            <Field label="Disability cover"><input type="number" value={data.insurance.disability}
              onChange={e=>set('insurance','disability',num(e.target.value))} /></Field>
          </Row>
        </section>
      )}

      {step === 7 && (
        <section>
          <h3>Preferences & constraints</h3>
          <Field label="Ethical preferences (e.g. no tobacco / arms)">
            <input value={data.preferences.ethical} onChange={e=>set('preferences','ethical',e.target.value)} />
          </Field>
          <Field label="Religious constraints (e.g. shariah, no interest)">
            <input value={data.preferences.religious} onChange={e=>set('preferences','religious',e.target.value)} />
          </Field>
          <Field label="Preferred asset classes">
            <input value={data.preferences.preferredAssets}
              onChange={e=>set('preferences','preferredAssets',e.target.value)}
              placeholder="index funds, real estate" />
          </Field>
          <Field label="Hours per week to manage investments">
            <input type="number" value={data.preferences.timePerWeekHours}
              onChange={e=>set('preferences','timePerWeekHours',num(e.target.value))} />
          </Field>
        </section>
      )}

      {step === 8 && (
        <section>
          <h3>Behavior</h3>
          <Field label="Spending habit">
            <select value={data.behavior.spendingHabit}
              onChange={e=>set('behavior','spendingHabit',e.target.value)}>
              <option>disciplined</option>
              <option>moderate</option>
              <option>impulsive</option>
            </select>
          </Field>
          <label className="radio">
            <input type="checkbox" checked={data.behavior.savingsConsistent}
              onChange={e=>set('behavior','savingsConsistent',e.target.checked)} />
            I save consistently each month
          </label>
          <Field label="Past investment mistakes / lessons">
            <textarea value={data.behavior.pastMistakes}
              onChange={e=>set('behavior','pastMistakes',e.target.value)} />
          </Field>
          <Field label="Financial knowledge level">
            <select value={data.behavior.knowledgeLevel}
              onChange={e=>set('behavior','knowledgeLevel',e.target.value)}>
              <option>beginner</option>
              <option>intermediate</option>
              <option>advanced</option>
            </select>
          </Field>
        </section>
      )}

      {step === 9 && (
        <section>
          <h3>Review</h3>
          <pre className="json">{JSON.stringify(data, null, 2)}</pre>
        </section>
      )}

      {err && <div className="err">{err}</div>}

      <div className="actions">
        {step > 0 && <button onClick={()=>setStep(s=>s-1)}>Back</button>}
        {step < steps.length - 1 && <button onClick={()=>setStep(s=>s+1)}>Next</button>}
        {step === steps.length - 1 && (
          <button disabled={busy} onClick={submit}>
            {busy ? 'Saving…' : 'Save & analyze'}
          </button>
        )}
      </div>
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
    <div>
      <div className="muted">Kids (optional)</div>
      {kids.map((kid, i) => (
        <Row key={i}>
          <Field label="Name"><input value={kid.name} onChange={e=>update(i,'name',e.target.value)} /></Field>
          <Field label="Age"><input type="number" value={kid.age}
            onChange={e=>update(i,'age', e.target.value === '' ? '' : Number(e.target.value))} /></Field>
          <button type="button" onClick={()=>remove(i)} className="link">Remove</button>
        </Row>
      ))}
      <button type="button" onClick={add} className="link">+ Add kid</button>
    </div>
  )
}

const Row = ({ children }) => <div className="row">{children}</div>
const Field = ({ label, children }) => (
  <label className="field">
    <span>{label}</span>
    {children}
  </label>
)
function prettify(k) {
  return k.replace(/([A-Z])/g, ' $1').replace(/^./, c => c.toUpperCase())
}
