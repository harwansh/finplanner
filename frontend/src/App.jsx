import Chat from './pages/Chat.jsx'

function LearnLanding() {
  return (
    <main className="learn-chat-page">
      <nav className="learn-chat-topbar" aria-label="SmartFinly navigation">
        <a className="learn-chat-brand" href="/">SmartFinly</a>
        <div className="learn-chat-nav">
          <a href="/learn">Learn</a>
          <a href="/learn-chat">Finance Chat</a>
        </div>
      </nav>
      <section className="learn-chat-hero">
        <p className="eyebrow">SmartFinly Learn</p>
        <h1>Your finance learning assistant</h1>
        <p>Explore finance concepts and ask questions grounded in study material.</p>
        <p style={{ marginTop: 18 }}><a className="learn-chat-brand" href="/learn-chat">Open Finance Education Chat →</a></p>
      </section>
    </main>
  )
}

export default function App() {
  const path = window.location.pathname
  if (path === '/learn-chat') return <Chat />
  return <LearnLanding />
}
