import { useState } from 'react'

const BLOCKED_PATTERNS = [
  /should\s+i\s+(buy|sell|invest)/i,
  /\b(best|top)\s+(stock|fund|mutual fund|sip|share)/i,
  /price\s+prediction/i,
  /guaranteed\s+return/i,
  /multibagger/i,
  /which\s+(stock|fund|share)/i,
]

const TOPICS = [
  {
    keywords: ['sip', 'systematic investment plan'],
    answer: 'A SIP is a way to invest a fixed amount at regular intervals. It can build discipline and reduce the stress of timing the market. The key ideas are consistency, suitable time horizon, and risk awareness.',
  },
  {
    keywords: ['emergency fund', 'emergency'],
    answer: 'An emergency fund is money kept aside for unexpected needs such as job loss, medical costs, urgent travel, or repairs. Many education frameworks discuss keeping several months of essential expenses in safe and liquid instruments.',
  },
  {
    keywords: ['compounding', 'compound'],
    answer: 'Compounding means earning returns on earlier returns. Time, consistency, and reinvestment are the main drivers. Small regular contributions can grow meaningfully over long periods, but returns are not guaranteed.',
  },
  {
    keywords: ['diversification', 'diversify'],
    answer: 'Diversification means spreading money across assets, sectors, or instruments so one bad outcome does not dominate the entire plan. It reduces concentration risk but does not remove all risk.',
  },
  {
    keywords: ['emi', 'loan', 'debt burden', 'debt-to-income', 'income'],
    answer: 'A safe EMI level depends on net monthly income, existing EMIs, rent, essentials, dependents, emergency fund, insurance, and job stability. As an educational rule of thumb, many households try to keep total EMIs well below take-home income, often around 30% to 40% or lower, with a separate emergency buffer. For example, if take-home income is ₹60,000, total EMIs of ₹18,000 to ₹24,000 may already be a heavy commitment depending on rent and family obligations.',
  },
  {
    keywords: ['risk tolerance', 'risk capacity', 'risk'],
    answer: 'Risk capacity depends on income stability, dependents, debt, emergency fund, goal horizon, and ability to handle losses. It is different from risk preference, which is how comfortable someone feels with volatility.',
  },
]

const suggestedQuestions = [
  'What is SIP?',
  'How much EMI can I manage from income?',
  'What is an emergency fund?',
  'What is diversification?',
  'How does compounding work?',
]

function isAdviceRequest(message) {
  return BLOCKED_PATTERNS.some((pattern) => pattern.test(message))
}

function buildLocalResponse(message) {
  const trimmed = String(message || '').trim()

  if (!trimmed) {
    return {
      blocked: false,
      source: 'validation',
      answer: 'Please ask a finance education question to get started.',
    }
  }

  if (isAdviceRequest(trimmed)) {
    return {
      blocked: true,
      source: 'guardrail',
      answer: 'I cannot recommend buying, selling, timing, or choosing a specific stock, fund, or product. I can explain the concept, risks, and evaluation framework in education-only terms. For personal advice, consult a SEBI-registered investment adviser.',
    }
  }

  const lower = trimmed.toLowerCase()
  const topic = TOPICS.find((item) => item.keywords.some((keyword) => lower.includes(keyword)))

  if (topic) {
    return {
      blocked: false,
      source: 'demo_knowledge_base',
      answer: `${topic.answer} This is education-only information, not investment advice.`,
    }
  }

  return {
    blocked: false,
    source: 'safe_education_fallback',
    answer: 'I can help explain finance concepts in simple language. Ask about SIPs, emergency funds, EMIs, debt burden, compounding, diversification, insurance, taxation, or risk capacity. I will keep the response educational and avoid product recommendations.',
  }
}

async function askSmartFinly(message) {
  const apiUrl = import.meta.env.VITE_CHAT_API_URL || import.meta.env.VITE_API_URL

  if (!apiUrl) return buildLocalResponse(message)

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ message }),
    })

    if (!response.ok) throw new Error('Chat API request failed')
    return await response.json()
  } catch {
    return buildLocalResponse(message)
  }
}

function Message({ message }) {
  return (
    <div className={`message ${message.role}`}>
      <div className="bubble">{message.content}</div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi, I am SmartFinly. Ask me finance education questions. I do not provide buy, sell, timing, or product recommendations.',
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  async function send(text) {
    const content = String(text || input).trim()
    if (!content || isLoading) return

    setInput('')
    setIsLoading(true)
    setMessages((current) => [...current, { role: 'user', content }])

    const response = await askSmartFinly(content)
    setMessages((current) => [...current, { role: 'assistant', content: response.answer }])
    setIsLoading(false)
  }

  function onSubmit(event) {
    event.preventDefault()
    send(input)
  }

  return (
    <main className="chatbot-page">
      <section className="hero" aria-label="SmartFinly chatbot overview">
        <p className="eyebrow">SmartFinly</p>
        <h1>Finance education chatbot</h1>
        <p className="subtitle">
          Learn concepts like SIPs, emergency funds, diversification, compounding, taxation, insurance,
          and risk capacity in simple language. Education only. No product recommendations.
        </p>
      </section>

      <section className="chat-shell" aria-label="SmartFinly chatbot">
        <div className="chat-header">
          <div>
            <strong>SmartFinly Chat</strong>
            <span>Education-only finance assistant</span>
          </div>
          <span className="status-pill">Online</span>
        </div>

        <div className="messages" aria-live="polite">
          {messages.map((message, index) => <Message key={`${message.role}-${index}`} message={message} />)}
          {isLoading ? <Message message={{ role: 'assistant', content: 'Thinking...' }} /> : null}
        </div>

        <div className="suggestions" aria-label="Suggested questions">
          {suggestedQuestions.map((question) => (
            <button key={question} type="button" onClick={() => send(question)} disabled={isLoading}>
              {question}
            </button>
          ))}
        </div>

        <form className="composer" onSubmit={onSubmit}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask a finance concept question..."
            aria-label="Message"
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading}>{isLoading ? 'Sending' : 'Send'}</button>
        </form>
      </section>

      <footer className="disclaimer">
        SmartFinly is for education only. It is not a SEBI-registered investment adviser and does not provide
        investment, tax, legal, insurance, buy/sell, or product-selection advice.
      </footer>
    </main>
  )
}
