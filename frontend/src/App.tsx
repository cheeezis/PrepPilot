import { useEffect, useState } from 'react'
import './App.css'
import { FoodCatalog } from './FoodCatalog'
import { RecipeCatalog } from './RecipeCatalog'
import { getHealth } from './api/health'

type SystemState = 'checking' | 'ready' | 'unavailable'
type CatalogView = 'foods' | 'recipes'

export default function App() {
  const [systemState, setSystemState] = useState<SystemState>('checking')
  const [view, setView] = useState<CatalogView>('foods')

  useEffect(() => {
    const controller = new AbortController()
    getHealth(controller.signal)
      .then(() => setSystemState('ready'))
      .catch(() => setSystemState('unavailable'))
    return () => controller.abort()
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
        <p className="eyebrow">V5 · Rezeptbasis</p>
        <h1 id="page-title">Deine Lebensmittel. Deine Rezepte.</h1>
        <p>
          Hinterlege Nährwerte einmal und kombiniere sie zu Rezepten. PrepPilot
          berechnet daraus automatisch die Nährwerte pro Portion.
        </p>
      </section>

      <nav className="catalog-tabs" aria-label="Katalog auswählen">
        <button type="button" aria-pressed={view === 'foods'} onClick={() => setView('foods')}>Lebensmittel</button>
        <button type="button" aria-pressed={view === 'recipes'} onClick={() => setView('recipes')}>Rezepte</button>
      </nav>

      {view === 'foods' ? <FoodCatalog /> : <RecipeCatalog />}
    </main>
  )
}
