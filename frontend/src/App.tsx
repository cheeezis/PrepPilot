import { useEffect, useState } from 'react'
import './App.css'
import { FoodCatalog } from './FoodCatalog'
import { RecipeCatalog } from './RecipeCatalog'
import { WeeklyPlans } from './WeeklyPlans'
import { getHealth } from './api/health'

type SystemState = 'checking' | 'ready' | 'unavailable'
type CatalogView = 'foods' | 'recipes' | 'plans'

export default function App() {
  const [systemState, setSystemState] = useState<SystemState>('checking')
  const [view, setView] = useState<CatalogView>('foods')

  useEffect(() => {
    const controller = new AbortController()
    let active = true
    getHealth(controller.signal)
      .then(() => { if (active) setSystemState('ready') })
      .catch(() => { if (active) setSystemState('unavailable') })
    return () => { active = false; controller.abort() }
  }, [])

  return (
    <main>
      <header>
        <a className="brand" href="/" aria-label="PrepPilot Startseite">PrepPilot</a>
        <span className={`system-state system-state--${systemState}`}>
          <span aria-hidden="true" />
          {systemState === 'checking' && 'System wird geprüft'}
          {systemState === 'ready' && 'System bereit'}
          {systemState === 'unavailable' && 'System nicht erreichbar'}
        </span>
      </header>

      <section className="intro" aria-labelledby="page-title">
        <p className="eyebrow">V5 · Wochenplanung</p>
        <h1 id="page-title">Deine Ernährung. Deine Woche.</h1>
        <p>
          Pflege deine Lebensmittel und Rezepte. PrepPilot plant daraus eine
          vollständige Woche nach deinen Nährwertzielen.
        </p>
      </section>

      <nav className="catalog-tabs" aria-label="Katalog auswählen">
        <button type="button" aria-pressed={view === 'foods'} onClick={() => setView('foods')}>Lebensmittel</button>
        <button type="button" aria-pressed={view === 'recipes'} onClick={() => setView('recipes')}>Rezepte</button>
        <button type="button" aria-pressed={view === 'plans'} onClick={() => setView('plans')}>Wochenpläne</button>
      </nav>

      {view === 'foods' && <FoodCatalog />}
      {view === 'recipes' && <RecipeCatalog />}
      {view === 'plans' && <WeeklyPlans />}
    </main>
  )
}
