import { useEffect, useRef, useState } from 'react'
import { buildCommonFallback, buildKnowledgeAnswer, loadKnowledgeIndex, searchKnowledgeIndex } from './localKnowledge.js'

const suggestedQuestions = [
  'Explain SIP in simple words',
  'How should I think about EMI affordability?',
  'What is an emergency fund?',
  'How much health insurance should I consider?',
  'Explain compounding with an example',
]

function localAnswer(message, knowledgeIndex) {
  const match = searchKnowledgeIndex(message, knowledgeIndex)
  if (match) return buildKnowledgeAnswer(match)
  return buildCommonFallback(message)
}

async function getAnswer(message, knowledgeIndex) {
  const trimmed = String(message || '').trim()
  if (!trimmed) return 'Ask me any finance education question to get started.'

  const apiUrl = import.meta.env.VITE_CHAT_API_URL || import.meta.env.VITE_API_URL
  if (!apiUrl) return localAnswer(trimmed, knowledgeIndex)

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ message: trimmed, question: trimmed }),
    })
    if (!response.ok) return localAnswer(trimmed, knowledgeIndex)
    const data = await response.json()
    const answer = data.answer || data.report || data.message
    return answer || localAnswer(trimmed, knowledgeIndex)
  } catch {
    return localAnswer(trimmed, knowledgeIndex)
  }
}

function Message({ message }) {
  return (
    <div className={`message ${message.role}`}>
      <div className="avatar">{message.role === 'assistant' ? 'S' : 'Y'}</div>
      <div className="bubble">{message.content}</div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi, I am SmartFinly. Ask me a finance question and I will explain it in simple, practical language.',
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [knowledgeIndex, setKnowledgeIndex] = useState(null)
  const messagesRef = useRef(null)

  useEffect(() => {
    loadKnowledgeIndex().then(setKnowledgeIndex)
  }, [])

  useEffect(() => {
    const container = messagesRef.current
    if (container) container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
  }, [messages, isLoading])

  async function send(text) {
    const content = String(text || input).trim()
    if (!content || isLoading) return
    setInput('')
    setIsLoading(true)
    setMessages((current) => [...current, { role: 'user', content }])
    const answer = await getAnswer(content, knowledgeIndex)
    setMessages((current) => [...current, { role: 'assistant', content: answer }])
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
        <h1>Your finance learning assistant</h1>
        <p className="subtitle">Ask questions in plain English and get clear, practical explanations for personal-finance concepts.</p>
      </section>

      <section className="chat-shell" aria-label="SmartFinly chatbot">
        <div className="chat-header">
          <div>
            <strong>SmartFinly Chat</strong>
            <span>Finance education assistant</span>
          </div>
          <span className="status-pill">Online</span>
        </div>

        <div className="messages" ref={messagesRef} aria-live="polite">
          {messages.map((message, index) => <Message key={`${message.role}-${index}`} message={message} />)}
          {isLoading ? <Message message={{ role: 'assistant', content: 'Preparing a clear answer...' }} /> : null}
        </div>

        <div className="suggestions" aria-label="Suggested questions">
          {suggestedQuestions.map((question) => <button key={question} type="button" onClick={() => send(question)} disabled={isLoading}>{question}</button>)}
        </div>

        <form className="composer" onSubmit={onSubmit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask about SIP, tax, insurance, EMI, retirement..." aria-label="Message" disabled={isLoading} />
          <button type="submit" disabled={isLoading}>{isLoading ? 'Sending' : 'Ask'}</button>
        </form>
      </section>

      <footer className="disclaimer">Education only. Not investment, tax, legal, insurance, buy/sell, or product-selection advice.</footer>
    </main>
  )
}
