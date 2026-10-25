import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { initDb } from './db/sqlite'
import ErrorBoundary from './components/ErrorBoundary'

const root = createRoot(document.getElementById('root'))

function FatalError({ message }) {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24, background: '#0b0f17', color: '#e5e7eb', fontFamily: 'system-ui, sans-serif',
      textAlign: 'center',
    }}>
      <div>
        <h1 style={{ fontSize: 20, marginBottom: 8 }}>Could not start the database</h1>
        <p style={{ color: '#9ca3af', fontSize: 14 }}>{message}</p>
      </div>
    </div>
  )
}

// Gate the app on DB initialisation so no page queries an unopened database.
initDb()
  .then(() => {
    root.render(
      <StrictMode>
        <ErrorBoundary>
          <App />
        </ErrorBoundary>
      </StrictMode>,
    )
  })
  .catch((err) => {
    console.error('DB init failed:', err)
    root.render(<FatalError message={String(err?.message || err)} />)
  })
