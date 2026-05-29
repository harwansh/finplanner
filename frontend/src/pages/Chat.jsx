import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { chat } from '../api/client.js'
import '../chat.css'

const STARTER_MESSAGES = [
  'Explain SIP in simple words',
  'How does 80C help a salaried person?',
  'What should I know about NPS?',
  'How much emergency fund should I keep?',
]

function SourceBadge({ source }) {
  return <span className="chat-source-badge">{source === 'knowledge_base' ? 'From study material' : 'AI explanation'}</span>
}

function References({ references = [] }) {
  if (!references.length) return null
  return (
    <details className="chat-references">
      <summary>References</summary>
      <ul>
        {references.map((ref, index) => (
          <li key={`${ref.file}-${ref.page}-${index}`}>{ref.file} — page {ref.page}</li>
        ))}
      </ul>
    </details>
  )
}

function Message({ item }) {
  const isBot = item.role === 'assistant'
  return (
    <div className={`learn-chat-message ${item.role}`}>
      <div className="learn-chat-avatar" aria-hidden="true">{isBot ? 'S' : 'Y'}</div>
      <div className="learn-chat-bubble">
        {isBot ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.content}</ReactMarkdown> : item.content}
        {isBot && item.source ? <SourceBadge source={item.source} /> : null}
        {isBot ? <References references={item.references} /> : null}
      </div>
    </div>
  )
}

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi, I am SmartFinly. Ask me a finance learning question about SIPs, tax, insurance, retirement, estate planning, or investment basics.',
      source: 'ai',
      references: [],
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isLoading])

  async function send(text = input) {
    const message = text.trim()
    if (!message || isLoading) return
    setInput('')
    setIsLoading(true)
    setMessages((current) => [...current, { role: 'user', content: message }])
    try {
      const result = await chat(message)
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: result.answer || 'I could not prepare an answer right now.',
          source: result.source || 'ai',
          references: result.references || [],
        },
      ])
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: error.message || 'SmartFinly could not answer right now. Please try again.',
          source: 'ai',
          references: [],
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  function onSubmit(event) {
    event.preventDefault()
    send()
  }

  return (
    <main className="learn-chat-page">
      <section className="learn-chat-hero">
        <p className="eyebrow">SmartFinly Learn</p>
        <h1>Ask finance questions, learn from study material</h1>
        <p>Education-only explanations grounded in CFP study PDFs, with AI fallback when the material does not cover the question.</p>
      </section>

      <section className="learn-chat-shell" aria-label="SmartFinly finance education chatbot">
        <div className="learn-chat-header">
          <div>
            <strong>Finance Education Chat</strong>
            <span>Study-material grounded answers</span>
          </div>
          <span className="chat-status">Online</span>
        </div>

        <div className="learn-chat-messages" aria-live="polite">
          {messages.map((item, index) => <Message key={`${item.role}-${index}`} item={item} />)}
          {isLoading ? (
            <div className="learn-chat-message assistant">
              <div className="learn-chat-avatar" aria-hidden="true">S</div>
              <div className="learn-chat-bubble typing"><span /> <span /> <span /></div>
            </div>
          ) : null}
          <div ref={scrollRef} />
        </div>

        <div className="learn-chat-starters" aria-label="Suggested questions">
          {STARTER_MESSAGES.map((starter) => (
            <button key={starter} type="button" onClick={() => send(starter)} disabled={isLoading}>{starter}</button>
          ))}
        </div>

        <form className="learn-chat-composer" onSubmit={onSubmit}>
          <label className="sr-only" htmlFor="learn-chat-input">Ask a finance question</label>
          <input
            id="learn-chat-input"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask about SIP, 80C, HRA, EPF, insurance, retirement..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>Send</button>
        </form>
      </section>

      <p className="learn-chat-disclaimer">Education only. SmartFinly is not a SEBI-registered adviser and does not provide personalized buy/sell or product-selection advice.</p>
    </main>
  )
}
