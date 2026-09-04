import { useEffect, useState } from 'react'
import './App.css'
import { getHealth } from './api/health'

type SystemState = 'checking' | 'ready' | 'unavailable'

export default function App() {
  const [systemState, setSystemState] = useState<SystemState>('checking')

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    getHealth(controller.signal)
      .then(() => {
        if (active) setSystemState('ready')
      })
      .catch(() => {
        if (active) setSystemState('unavailable')
      })

    return () => {
      active = false
      controller.abort()
    }
  }, [])

  return (
    <main>
      <header>
        <a className="brand" href="/" aria-label="PrepPilot Startseite">
          PrepPilot
        </a>
        <span className={`system-state system-state--${systemState}`}>
          <span aria-hidden="true" />
          {systemState === 'checking' && 'System wird geprüft'}
          {systemState === 'ready' && 'System bereit'}
          {systemState === 'unavailable' && 'System nicht erreichbar'}
        </span>
      </header>

      <section className="intro" aria-labelledby="page-title">
        <p className="eyebrow">V5 · Meal-Prep-Woche</p>
        <h1 id="page-title">Plane eine Woche, die wirklich aufgeht.</h1>
        <p>
          PrepPilot wird neu aufgebaut: persönliche Lebensmittel, eigene
          Rezepte und vollständig verteilte Meal-Prep-Portionen für sieben Tage.
        </p>
      </section>

      <section className="empty-state" aria-labelledby="empty-title">
        <div className="empty-state__icon" aria-hidden="true">7</div>
        <div>
          <p className="eyebrow">Sauberer Start</p>
          <h2 id="empty-title">Noch keine Lebensmittel oder Rezepte</h2>
          <p>
            Die technische Grundlage steht. Als Nächstes entsteht der
            persönliche Lebensmittelkatalog.
          </p>
        </div>
      </section>
    </main>
  )
}
