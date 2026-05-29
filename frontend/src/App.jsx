import { useEffect, useRef, useState } from 'react'
import { buildKnowledgeAnswer, loadKnowledgeIndex, searchKnowledgeIndex } from './localKnowledge.js'

const suggestedQuestions = [
  'What is SIP?',
  'How much EMI can I manage from income?',
  'What is an emergency fund?',
  'How much health insurance should I have?',
  'How does compounding work?',
]

function fallbackAnswer() {
  return 'I could not find a strong match in the local PDF knowledge base. Connect VITE_CHAT_API_URL in Amplify so unmatched questions can be routed to the backend fallback.'
}

async function getAnswer(message, localIndex) {
  const trimmed = String(message || '').trim()
  if (!trimmed) return 'Please ask a finance education question to get started.'

  const localMatch = searchKnowledgeIndex(trimmed, localIndex)
  if (localMatch) return buildKnowledgeAnswer(localMatch)

  const apiUrl = import.meta.env.VITE_CHAT_API_URL || import.meta.env.VITE_API_URL
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
  return <div className={`message ${message.role}`}><div className="bubble">{message.content}</div></div>
}

export default function App() {
  const [messages, setMessages] = useState([{ role: 'assistant', content: 'Hi, I am SmartFinly. I search the local PDF knowledge base first. If no match is found, I use the backend fallback.' }])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [localIndex, setLocalIndex] = useState(null)
  const messagesRef = useRef(null)

  useEffect(() => { loadKnowledgeIndex().then(setLocalIndex) }, [])

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
    const answer = await getAnswer(content, localIndex)
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
        <h1>Finance education chatbot</h1>
        <p className="subtitle">Local PDF knowledge base first. Backend fallback only when no PDF match is found.</p>
      </section>
      <section className="chat-shell" aria-label="SmartFinly chatbot">
        <div className="chat-header"><div><strong>SmartFinly Chat</strong><span>{localIndex?.pdf_count ? `${localIndex.pdf_count} PDFs indexed` : 'Loading PDF index'}</span></div><span className="status-pill">Online</span></div>
        <div className="messages" ref={messagesRef} aria-live="polite">
          {messages.map((message, index) => <Message key={`${message.role}-${index}`} message={message} />)}
          {isLoading ? <Message message={{ role: 'assistant', content: 'Thinking...' }} /> : null}
        </div>
        <div className="suggestions" aria-label="Suggested questions">{suggestedQuestions.map((question) => <button key={question} type="button" onClick={() => send(question)} disabled={isLoading}>{question}</button>)}</div>
        <form className="composer" onSubmit={onSubmit}><input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask a finance concept question..." aria-label="Message" disabled={isLoading} /><button type="submit" disabled={isLoading}>{isLoading ? 'Sending' : 'Send'}</button></form>
      </section>
      <footer className="disclaimer">SmartFinly is for education only.</footer>
    </main>
  )
}
