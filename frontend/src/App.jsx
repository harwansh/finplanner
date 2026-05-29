import { useEffect, useRef, useState } from 'react'
import { loadKnowledgeIndex } from './localKnowledge.js'

const suggestedQuestions = [
  'Explain SIP in simple words',
  'How should I think about EMI affordability?',
  'What is an emergency fund?',
  'How much health insurance should I consider?',
  'Explain compounding with an example',
]

function fallbackAnswer() {
  return 'I am ready to answer, but the AI backend is not connected on this deployment yet. Please connect VITE_CHAT_API_URL in Amplify so I can read the PDF knowledge base and generate a proper answer.'
}

async function getAnswer(message) {
  const trimmed = String(message || '').trim()
  if (!trimmed) return 'Ask me any finance education question to get started.'

  const apiUrl = import.meta.env.VITE_CHAT_API_URL
  if (!apiUrl) return fallbackAnswer()

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ message: trimmed }),
    })
    if (!response.ok) return fallbackAnswer()
    const data = await response.json()
    return data.answer || fallbackAnswer()
  } catch {
    return fallbackAnswer()
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
      content: 'Hi, I am SmartFinly. Ask me a finance question. I use your PDF knowledge base first, then AI fallback when the PDFs do not have enough context.',
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [pdfCount, setPdfCount] = useState(null)
  const messagesRef = useRef(null)

  useEffect(() => {
    loadKnowledgeIndex().then((index) => setPdfCount(index?.pdf_count || null))
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
    const answer = await getAnswer(content)
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
        <p className="subtitle">Ask questions in plain English. SmartFinly reads your finance PDFs, explains the answer clearly, and uses AI fallback only when the PDFs do not cover the topic.</p>
      </section>

      <section className="chat-shell" aria-label="SmartFinly chatbot">
        <div className="chat-header">
          <div>
            <strong>SmartFinly Chat</strong>
            <span>{pdfCount ? `${pdfCount} knowledge PDFs available` : 'PDF-grounded AI assistant'}</span>
          </div>
          <span className="status-pill">Private beta</span>
        </div>

        <div className="messages" ref={messagesRef} aria-live="polite">
          {messages.map((message, index) => <Message key={`${message.role}-${index}`} message={message} />)}
          {isLoading ? <Message message={{ role: 'assistant', content: 'Reading the knowledge base and preparing an answer...' }} /> : null}
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
