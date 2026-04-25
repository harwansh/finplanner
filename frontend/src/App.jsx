import Home from './pages/Home.jsx'

export default function App() {
  return (
    <div className="shell">
      <header>
        <span className="brand">FinPlanner</span>
        <span className="muted">AI-powered personal finance planning</span>
      </header>
      <main><Home /></main>
    </div>
  )
}
