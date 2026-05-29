const STOPWORDS = new Set(['about','after','again','also','and','are','can','could','does','for','from','have','how','into','not','that','the','their','then','there','this','what','when','where','which','with','would','your','you','must','should'])

export function tokenize(text) {
  return String(text || '').toLowerCase().match(/[a-z][a-z0-9-]{1,}/g)?.filter((token) => !STOPWORDS.has(token)) || []
}

export async function loadKnowledgeIndex() {
  try {
    const response = await fetch('/knowledge-index.json', { cache: 'no-store' })
    if (!response.ok) return null
    return await response.json()
  } catch {
    return null
  }
}

export function searchKnowledgeIndex(message, index) {
  const chunks = index?.chunks || []
  const queryTokens = tokenize(message)
  if (!chunks.length || !queryTokens.length) return null

  const querySet = new Set(queryTokens)
  const scored = chunks.map((chunk) => {
    const text = `${chunk.title || ''} ${chunk.source || ''} ${chunk.text || chunk.content || ''}`
    const tokenSet = new Set(tokenize(text))
    let overlap = 0
    querySet.forEach((token) => {
      if (tokenSet.has(token)) overlap += 1
    })
    const score = overlap / Math.sqrt(Math.max(querySet.size, 1) * Math.max(tokenSet.size, 1))
    return { ...chunk, score }
  }).sort((a, b) => b.score - a.score)

  return scored[0]?.score >= 0.045 ? scored[0] : null
}

export function buildKnowledgeAnswer(match) {
  const text = String(match?.text || match?.content || '').trim().replace(/Page \d+:/g, '').replace(/\s+/g, ' ')
  const sentences = text.split(/(?<=[.!?])\s+/).filter(Boolean).slice(0, 3)
  const answer = sentences.length ? sentences.join(' ') : text.slice(0, 500)
  return `Here is the simple explanation: ${answer}`
}

export function buildCommonFallback(message) {
  const query = String(message || '').toLowerCase()

  if (query.includes('sip') || query.includes('systematic investment')) {
    return 'A SIP is a way to invest a fixed amount regularly, usually every month. It helps build discipline and reduces the pressure of timing the market. The main things to understand are your goal, time horizon, risk level, and whether you can continue the amount comfortably. This is education only, not a recommendation to invest in any specific product.'
  }

  if (query.includes('emi') || query.includes('loan') || query.includes('afford')) {
    return 'Think about EMI affordability from your take-home income, not gross salary. First subtract rent, food, utilities, school fees, insurance, existing EMIs, and emergency-fund savings. As a learning rule, many households try to keep total EMIs around 30% to 40% of take-home income or lower, but the safe level depends on job stability, dependents, city costs, and emergency savings.'
  }

  if (query.includes('emergency')) {
    return 'An emergency fund is money kept aside for unexpected events like job loss, medical costs, urgent travel, or repairs. A common learning framework is to keep several months of essential expenses in liquid and relatively safe places before taking higher financial risk.'
  }

  if (query.includes('health') || query.includes('insurance')) {
    return 'Health insurance is protection against large medical expenses. The right cover depends on city, age, family size, employer cover, existing illnesses, dependents, and hospital costs. Do not rely only on employer insurance if your family depends on you, because that cover may end when the job changes.'
  }

  if (query.includes('compound')) {
    return 'Compounding means earning returns on earlier returns. Time is the biggest driver: the longer money stays invested and reinvested, the more compounding can help. It is powerful, but it does not guarantee returns because market risk, costs, and withdrawals can affect the outcome.'
  }

  return 'I can explain this in education-only terms, but I could not find enough reliable context for a strong answer right now. Try asking about SIP, EMI, emergency fund, insurance, tax planning, retirement, or compounding.'
}
