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
  const title = match.title || match.source || 'the local PDF knowledge base'
  const text = String(match.text || match.content || '').trim()
  const sentences = text.split(/(?<=[.!?])\s+/).filter(Boolean).slice(0, 4)
  const answer = sentences.length ? sentences.join(' ') : text.slice(0, 700)
  return `From ${title}: ${answer}`
}
