import { useEffect, useState, type FormEvent, type MouseEvent } from 'react'
import {
  createDayPlans,
  type DayPlan,
  type DayPlansResponse,
  type RuleEvaluation,
} from './api/dayPlans'
import { getHealth } from './api/health'
import { importNhsRecipes, type ImportRun } from './api/imports'
import { getRecipes, type Recipe, type RecipeCategory } from './api/recipes'
import './App.css'

type SystemStatus = 'checking' | 'ready' | 'unavailable'
type RequestStatus = 'idle' | 'loading' | 'success' | 'error'
type ImportStatus = 'idle' | 'loading' | 'success' | 'error'
type RecipeStatus = 'loading' | 'success' | 'error'
type AppPage = 'planner' | 'recipes'

const metricNames: Record<RuleEvaluation['metric'], string> = {
  calories: 'Kalorien',
  protein: 'Protein',
  fat: 'Fett',
  carbs: 'Kohlenhydrate',
}

const metricUnits: Record<RuleEvaluation['metric'], string> = {
  calories: 'kcal',
  protein: 'g',
  fat: 'g',
  carbs: 'g',
}

const importFieldNames: Record<string, string> = {
  title: 'Titel',
  servings: 'Portionszahl',
  calories: 'Kalorien',
  protein: 'Protein',
  carbs: 'Kohlenhydrate',
  fat: 'Fett',
  sugar: 'Zucker',
  saturated_fat: 'Gesättigte Fettsäuren',
  fiber: 'Ballaststoffe',
  salt: 'Salz',
  ingredients: 'Zutaten',
  instructions: 'Zubereitung',
}

const categoryNames: Record<RecipeCategory, string> = {
  breakfast: 'Frühstück',
  lunch: 'Mittagessen',
  dinner: 'Abendessen',
}

function App() {
  const [page, setPage] = useState<AppPage>(() => pageFromPath())
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('checking')
  const [requestStatus, setRequestStatus] = useState<RequestStatus>('idle')
  const [importStatus, setImportStatus] = useState<ImportStatus>('idle')
  const [importResult, setImportResult] = useState<ImportRun | null>(null)
  const [recipeStatus, setRecipeStatus] = useState<RecipeStatus>('loading')
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [result, setResult] = useState<DayPlansResponse | null>(null)
  const [selectedPlanIndex, setSelectedPlanIndex] = useState<number | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getHealth(controller.signal)
      .then(() => setSystemStatus('ready'))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setSystemStatus('unavailable')
      })
    getRecipes(controller.signal)
      .then((storedRecipes) => {
        setRecipes(storedRecipes)
        setRecipeStatus('success')
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setRecipeStatus('error')
      })
    return () => controller.abort()
  }, [])

  useEffect(() => {
    const handleHistoryChange = () => setPage(pageFromPath())
    window.addEventListener('popstate', handleHistoryChange)
    return () => window.removeEventListener('popstate', handleHistoryChange)
  }, [])

  function navigate(event: MouseEvent<HTMLAnchorElement>, nextPage: AppPage) {
    event.preventDefault()
    const path = nextPage === 'planner' ? '/' : '/recipes'
    window.history.pushState({}, '', path)
    setPage(nextPage)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setRequestStatus('loading')
    setResult(null)
    setSelectedPlanIndex(null)

    try {
      const nextResult = await createDayPlans({
        calories: Number(form.get('calories')),
        protein_minimum: Number(form.get('protein')),
        fat_maximum: Number(form.get('fat')),
        carbs: Number(form.get('carbs')),
      })
      setResult(nextResult)
      setRequestStatus('success')
    } catch {
      setRequestStatus('error')
    }
  }

  async function handleImport() {
    setImportStatus('loading')
    setImportResult(null)
    try {
      const nextResult = await importNhsRecipes()
      setImportResult(nextResult)
      setImportStatus('success')
      if (nextResult.created + nextResult.updated + nextResult.unchanged > 0) {
        setSystemStatus('ready')
      }
      try {
        setRecipes(await getRecipes())
        setRecipeStatus('success')
      } catch {
        setRecipeStatus('error')
      }
    } catch {
      setImportStatus('error')
    }
  }

  return (
    <main>
      <header>
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">P</span>
          <span className="brand-name">PrepPilot</span>
        </div>
        <nav className="app-navigation" aria-label="Hauptnavigation">
          <a
            href="/"
            aria-current={page === 'planner' ? 'page' : undefined}
            onClick={(event) => navigate(event, 'planner')}
          >
            Planer
          </a>
          <a
            href="/recipes"
            aria-current={page === 'recipes' ? 'page' : undefined}
            onClick={(event) => navigate(event, 'recipes')}
          >
            Rezepte
          </a>
        </nav>
        <span className={`system-status system-status--${systemStatus}`}>
          <span className="status-indicator" aria-hidden="true" />
          {systemStatus === 'ready'
            ? 'System bereit'
            : systemStatus === 'unavailable'
              ? 'System nicht erreichbar'
              : 'Verbindung wird geprüft'}
        </span>
      </header>

      {page === 'planner' ? (
        <>
          <section className="intro">
            <p className="eyebrow">Tagesplaner</p>
            <h1>Ein Tagesplan, der zu deinen Zielen passt.</h1>
            <p className="intro-copy">
              Gib deine Tagesziele ein. PrepPilot kombiniert daraus ein
              Frühstück, ein Mittagessen und ein Abendessen und zeigt
              Abweichungen offen an.
            </p>
          </section>

          <form className="target-form" onSubmit={handleSubmit}>
            <NumberField name="calories" label="Kalorien" unit="kcal" value={2000} />
            <NumberField name="protein" label="Protein mindestens" unit="g" value={120} />
            <NumberField name="fat" label="Fett höchstens" unit="g" value={70} />
            <NumberField name="carbs" label="Kohlenhydrate" unit="g" value={220} />
            <button type="submit" disabled={requestStatus === 'loading'}>
              {requestStatus === 'loading'
                ? 'Pläne werden berechnet …'
                : 'Tagespläne erstellen'}
            </button>
          </form>

          {requestStatus === 'error' && (
            <p className="notice notice--error">
              Die Tagespläne konnten nicht erstellt werden.
            </p>
          )}

          {result && (
            <PlanResults
              result={result}
              selectedPlanIndex={selectedPlanIndex}
              onSelect={setSelectedPlanIndex}
            />
          )}
        </>
      ) : (
        <>
          <section className="intro">
            <p className="eyebrow">Rezeptbestand</p>
            <h1>Die Grundlage deiner Tagespläne.</h1>
            <p className="intro-copy">
              Hier siehst du alle gespeicherten Quellenrezepte und ihre
              Nährwerte pro Portion.
            </p>
          </section>

          <section className="import-control" aria-labelledby="import-heading">
            <div>
              <p className="eyebrow">NHS-Import</p>
              <h2 id="import-heading">Geprüfte NHS-Rezepte laden</h2>
              <p>Der Lauf verarbeitet ausschließlich die 33 fest freigegebenen Seiten.</p>
            </div>
            <button type="button" onClick={handleImport} disabled={importStatus === 'loading'}>
              {importStatus === 'loading' ? 'Rezepte werden importiert …' : '33 NHS-Rezepte importieren'}
            </button>
            {importResult && (
              <div className="import-result" role="status">
                <p className="notice">
                  {importResult.created} neu · {importResult.updated} aktualisiert ·{' '}
                  {importResult.unchanged} unverändert · {importResult.rejected} abgelehnt
                </p>
                {importResult.rejected > 0 && (
                  <div className="import-rejections">
                    <strong>Nicht importiert</strong>
                    <ul>
                      {importResult.items
                        .filter((item) => item.status === 'rejected')
                        .map((item) => (
                          <li key={item.source_url}>
                            <a href={item.source_url} target="_blank" rel="noreferrer">
                              {recipeNameFromUrl(item.source_url)}
                            </a>
                            <span>{describeImportReason(item.reason)}</span>
                          </li>
                        ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            {importStatus === 'error' && (
              <p className="notice notice--error">Der Rezeptimport ist fehlgeschlagen.</p>
            )}
          </section>

          <RecipeInventory status={recipeStatus} recipes={recipes} />
        </>
      )}
    </main>
  )
}

function RecipeInventory({
  status,
  recipes,
}: {
  status: RecipeStatus
  recipes: Recipe[]
}) {
  const [categoryFilter, setCategoryFilter] = useState<'all' | RecipeCategory>('all')
  const visibleRecipes = categoryFilter === 'all'
    ? recipes
    : recipes.filter((recipe) => recipe.category === categoryFilter)

  return (
    <section className="recipe-inventory" aria-labelledby="recipes-heading">
      <div className="inventory-heading">
        <div>
          <p className="eyebrow">PostgreSQL-Bestand</p>
          <h2 id="recipes-heading">Gespeicherte Rezepte</h2>
        </div>
        {status === 'success' && (
          <strong className="inventory-count">{recipes.length} Rezepte</strong>
        )}
      </div>

      {status === 'success' && recipes.length > 0 && (
        <div className="category-filters" role="group" aria-label="Rezepte filtern">
          <button
            type="button"
            aria-pressed={categoryFilter === 'all'}
            onClick={() => setCategoryFilter('all')}
          >
            Alle <span>{recipes.length}</span>
          </button>
          {(Object.keys(categoryNames) as RecipeCategory[]).map((category) => (
            <button
              type="button"
              key={category}
              aria-pressed={categoryFilter === category}
              onClick={() => setCategoryFilter(category)}
            >
              {categoryNames[category]}{' '}
              <span>{recipes.filter((recipe) => recipe.category === category).length}</span>
            </button>
          ))}
        </div>
      )}

      {status === 'loading' && <p>Rezeptbestand wird geladen …</p>}
      {status === 'error' && (
        <p className="notice notice--error">
          Der Rezeptbestand ist noch nicht verfügbar. Starte oben den Import.
        </p>
      )}
      {status === 'success' && recipes.length === 0 && (
        <p>Noch keine Rezepte gespeichert.</p>
      )}
      {recipes.length > 0 && (
        <div className="recipe-list">
          {visibleRecipes.map((recipe) => (
            <details className="recipe-card" key={recipe.id}>
              <summary>
                <div className="recipe-card-title">
                  <strong>{recipe.title}</strong>
                  <small>{categoryNames[recipe.category]}</small>
                </div>
                <span>
                  {formatNumber(recipe.nutrients.calories)} kcal pro Portion ·{' '}
                  ergibt {recipe.servings} Portionen
                </span>
              </summary>
              <p className="nutrition-basis">Nährwerte pro Portion</p>
              <div className="recipe-macros">
                <span><strong>{formatNumber(recipe.nutrients.protein)} g</strong> Protein</span>
                <span><strong>{formatNumber(recipe.nutrients.carbs)} g</strong> Kohlenhydrate</span>
                <span><strong>{formatNumber(recipe.nutrients.fat)} g</strong> Fett</span>
                <span><strong>{formatOptionalGrams(recipe.nutrients.sugar)}</strong> Zucker</span>
                <span><strong>{formatOptionalGrams(recipe.nutrients.saturated_fat)}</strong> gesättigte Fettsäuren</span>
                <span><strong>{formatOptionalGrams(recipe.nutrients.fiber)}</strong> Ballaststoffe</span>
                <span><strong>{formatOptionalGrams(recipe.nutrients.salt)}</strong> Salz</span>
              </div>
              <div className="recipe-details">
                <div>
                  <h3>Zutaten für {recipe.servings} Portionen</h3>
                  <ul>
                    {recipe.ingredients.map((ingredient, index) => (
                      <li key={`${index}:${ingredient}`}>{ingredient}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3>Zubereitung</h3>
                  <ol>
                    {recipe.instructions.map((instruction, index) => (
                      <li key={`${index}:${instruction}`}>{instruction}</li>
                    ))}
                  </ol>
                </div>
              </div>
              <p className="recipe-source">
                <a href={recipe.source_url} target="_blank" rel="noreferrer">
                  Originalrezept beim NHS
                </a>
                <small>{recipe.attribution_text} · {recipe.license_name}</small>
              </p>
            </details>
          ))}
        </div>
      )}
    </section>
  )
}

function NumberField({
  name,
  label,
  unit,
  value,
}: {
  name: string
  label: string
  unit: string
  value: number
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <span className="number-input">
        <input
          name={name}
          type="number"
          min="1"
          step="1"
          defaultValue={value}
          required
        />
        <small>{unit}</small>
      </span>
    </label>
  )
}

function PlanResults({
  result,
  selectedPlanIndex,
  onSelect,
}: {
  result: DayPlansResponse
  selectedPlanIndex: number | null
  onSelect: (index: number) => void
}) {
  if (result.outcome === 'no_usable_plan') {
    return (
      <section className="results">
        <p className="notice">
          Für diese Ziele liegt aktuell kein brauchbarer Plan innerhalb der
          festgelegten Grenzen. Passe eines deiner Nährwertziele an.
        </p>
      </section>
    )
  }

  const selectedPlan = selectedPlanIndex === null
    ? null
    : result.plans[selectedPlanIndex] ?? null
  const selectedPlanNumber = selectedPlanIndex === null
    ? null
    : selectedPlanIndex + 1

  return (
    <section className="results">
      <div className="results-heading">
        <div>
          <p className="eyebrow">Vorschläge</p>
          <h2>{result.plans.length} Tagespläne</h2>
        </div>
        {result.outcome === 'approximations_only' && (
          <p className="notice">
            Kein Plan trifft alle harten Ziele. Die besten Annäherungen:
          </p>
        )}
      </div>
      {selectedPlan && selectedPlanNumber !== null && (
        <>
          <div className="selection-summary" role="status">
            <span className="selection-check" aria-hidden="true">✓</span>
            <div>
              <strong>Vorschlag {selectedPlanNumber} ausgewählt</strong>
              <p>Dieser Vorschlag kombiniert vollständige Quellenrezepte.</p>
            </div>
          </div>
        </>
      )}
      <div className="plan-list">
        {result.plans.map((plan, index) => (
          <PlanCard
            key={`${index}-${plan.score}`}
            plan={plan}
            index={index}
            selected={selectedPlanIndex === index}
            onSelect={() => onSelect(index)}
          />
        ))}
      </div>
    </section>
  )
}

function PlanCard({
  plan,
  index,
  selected,
  onSelect,
}: {
  plan: DayPlan
  index: number
  selected: boolean
  onSelect: () => void
}) {
  return (
    <article className={`plan-card${selected ? ' plan-card--selected' : ''}`}>
      <div className="plan-title-row">
        <div>
          <p className="plan-number">Vorschlag {index + 1}</p>
          <h3>{plan.status === 'valid' ? 'Plan verwendbar' : 'Annäherung'}</h3>
        </div>
        <span className={`plan-badge plan-badge--${plan.status}`}>
          {plan.status === 'valid' ? 'Gültig' : 'Mit Abweichung'}
        </span>
      </div>

      <div className="nutrient-grid">
        {plan.evaluations.map((evaluation) => (
          <NutrientEvaluation
            key={evaluation.metric}
            evaluation={evaluation}
          />
        ))}
      </div>

      <button
        type="button"
        className={`select-plan-button${selected ? ' select-plan-button--selected' : ''}`}
        aria-pressed={selected}
        onClick={onSelect}
      >
        {selected ? 'Ausgewählt' : 'Diesen Plan auswählen'}
      </button>

      <div className="meal-list">
        {plan.recipes.map((recipe) => (
          <details key={recipe.id} className="meal">
            <summary>
              <span>
                <small>
                  {categoryNames[recipe.category]} · {recipe.portions}{' '}
                  {recipe.portions === 1 ? 'Portion eingeplant' : 'Portionen eingeplant'}
                </small>
                <strong>{recipe.title}</strong>
              </span>
              <span>{formatNumber(recipe.nutrients.calories)} kcal im Plan</span>
            </summary>
            <p className="ingredient-note">
              Die Zutatenmengen gehören zum vollständigen Rezept für{' '}
              {recipe.recipe_servings} Portionen. PrepPilot rechnet sie noch nicht
              auf die eingeplante Portionszahl um.
            </p>
            <ul>
              {recipe.ingredients.map((ingredient, index) => (
                <li key={`${index}:${ingredient}`}><span>{ingredient}</span></li>
              ))}
            </ul>
            <a href={recipe.source_url} target="_blank" rel="noreferrer">
              Originalrezept beim NHS
            </a>
            <small>{recipe.attribution_text} · {recipe.license_name}</small>
          </details>
        ))}
      </div>
    </article>
  )
}

function NutrientEvaluation({
  evaluation,
}: {
  evaluation: RuleEvaluation
}) {
  const unit = metricUnits[evaluation.metric]
  const deviation = describeDeviation(evaluation)

  return (
    <div
      className={`nutrient${evaluation.satisfied ? '' : ' nutrient--missed'}`}
    >
      <div className="nutrient-heading">
        <span>{metricNames[evaluation.metric]}</span>
        <small className={evaluation.satisfied ? 'goal-status' : 'goal-status goal-status--missed'}>
          {evaluation.satisfied
            ? 'Im Ziel'
            : evaluation.kind === 'soft'
              ? 'Weiche Abweichung'
              : 'Außerhalb'}
        </small>
      </div>
      <strong>
        {formatNumber(evaluation.actual)} <small>{unit}</small>
      </strong>
      <small className="nutrient-target">
        {describeTarget(evaluation)}
      </small>
      {deviation && <small className="nutrient-deviation">{deviation}</small>}
    </div>
  )
}

function describeTarget(evaluation: RuleEvaluation) {
  const unit = metricUnits[evaluation.metric]

  if (
    evaluation.target !== null
    && evaluation.minimum !== null
    && evaluation.maximum !== null
  ) {
    return `Ziel ${formatNumber(evaluation.target)} ${unit} · Bereich ${formatNumber(evaluation.minimum)}–${formatNumber(evaluation.maximum)} ${unit}`
  }
  if (evaluation.minimum !== null && evaluation.maximum !== null) {
    return `Bereich ${formatNumber(evaluation.minimum)}–${formatNumber(evaluation.maximum)} ${unit}`
  }
  if (evaluation.minimum !== null) {
    return `Mindestens ${formatNumber(evaluation.minimum)} ${unit}`
  }
  if (evaluation.maximum !== null) {
    return `Höchstens ${formatNumber(evaluation.maximum)} ${unit}`
  }
  return `Ziel ${formatNumber(evaluation.target ?? 0)} ${unit}`
}

function describeDeviation(evaluation: RuleEvaluation) {
  if (evaluation.satisfied) return null

  const unit = metricUnits[evaluation.metric]
  if (
    evaluation.minimum !== null
    && evaluation.actual < evaluation.minimum
  ) {
    const boundary = evaluation.maximum === null
      ? 'unter dem Mindestwert'
      : 'unter dem Zielbereich'
    return `${formatNumber(evaluation.minimum - evaluation.actual)} ${unit} ${boundary}`
  }
  if (
    evaluation.maximum !== null
    && evaluation.actual > evaluation.maximum
  ) {
    const boundary = evaluation.minimum === null
      ? 'über dem Höchstwert'
      : 'über dem Zielbereich'
    return `${formatNumber(evaluation.actual - evaluation.maximum)} ${unit} ${boundary}`
  }
  if (evaluation.target !== null) {
    return `${formatNumber(Math.abs(evaluation.actual - evaluation.target))} ${unit} vom Ziel entfernt`
  }
  return null
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('de-DE', {
    maximumFractionDigits: 1,
  }).format(value)
}

function formatOptionalGrams(value: number | null) {
  return value === null ? 'keine Angabe' : `${formatNumber(value)} g`
}

function pageFromPath(): AppPage {
  return window.location.pathname === '/recipes' ? 'recipes' : 'planner'
}

function recipeNameFromUrl(sourceUrl: string) {
  try {
    const segments = new URL(sourceUrl).pathname.split('/').filter(Boolean)
    const slug = segments.at(-1)
    return slug ? slug.replaceAll('-', ' ') : sourceUrl
  } catch {
    return sourceUrl
  }
}

function describeImportReason(reason: string | null) {
  if (!reason) return 'Unbekannter Importfehler'
  if (reason === 'recipe JSON-LD missing') {
    return 'Strukturierte Rezeptdaten fehlen auf der Quellseite.'
  }
  const missingField = reason.match(/^(\w+) missing$/)?.[1]
  if (missingField && importFieldNames[missingField]) {
    return `Pflichtfeld „${importFieldNames[missingField]}“ fehlt auf der Quellseite.`
  }
  return reason
}

export default App
