import Home from './pages/Home.jsx'
import Chat from './pages/Chat.jsx'

function Header({ activePath }) {
  return (
    <header className="sf-header">
      <div className="sf-brand-lockup">
        <a className="brand" href="/learn">SmartFinly</a>
        <span className="sf-brand-badge">Education only</span>
      </div>
      <nav className="sf-nav" aria-label="SmartFinly navigation">
        <a href="/learn" className={activePath !== '/learn-chat' ? 'active' : ''}>Planner</a>
        <a href="/learn-chat" className={activePath === '/learn-chat' ? 'active' : ''}>Finance Chat</a>
      </nav>
    </header>
  )
}

export default function App() {
  const path = window.location.pathname
  const isChat = path === '/learn-chat'

  return (
    <>
      <Header activePath={path} />
      {isChat ? <Chat /> : <Home />}
    </>
  )
}
