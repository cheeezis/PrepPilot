import { useEffect, useState } from 'react'
import { getHealth } from './api/health'
import './App.css'

type SystemStatus = 'checking' | 'ready' | 'unavailable'

function App() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('checking')

  useEffect(() => {
    const controller = new AbortController()

    getHealth(controller.signal)
      .then(() => setSystemStatus('ready'))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return
        }

        setSystemStatus('unavailable')
      })

    return () => controller.abort()
  }, [])

  const statusText = {
    checking: 'Verbindung wird geprüft',
    ready: 'System ist bereit',
    unavailable: 'System ist nicht erreichbar',
  }[systemStatus]

  return (
    <main>
      <header>
        <span className="brand-mark" aria-hidden="true">
          P
        </span>
        <span className="brand-name">PrepPilot</span>
      </header>

      <section className="system-check" aria-live="polite">
        <p className="eyebrow">Technischer Systemcheck</p>
        <h1>{statusText}</h1>
        <div className={`status-line status-line--${systemStatus}`}>
          <span className="status-indicator" aria-hidden="true" />
          <span>Frontend, API und Datenbank</span>
        </div>
      </section>
    </main>
  )
}

export default App
