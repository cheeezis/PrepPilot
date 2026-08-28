import { useEffect, useState, type FormEvent } from 'react'
import {
  createDayPlans,
  type DayPlan,
  type DayPlansResponse,
  type RuleEvaluation,
} from './api/dayPlans'
import { getHealth } from './api/health'
import './App.css'

type SystemStatus = 'checking' | 'ready' | 'unavailable'
type RequestStatus = 'idle' | 'loading' | 'success' | 'error'

const roleNames: Record<string, string> = {
  first_meal: 'Erste Mahlzeit',
  quick_lunch: 'Schnelles Mittagessen',
  protein_snack: 'Protein-Snack',
  main_meal: 'Hauptgericht',
  late_snack: 'Später Snack',
}

const metricNames: Record<RuleEvaluation['metric'], string> = {
  calories: 'Kalorien',
  protein: 'Protein',
  fat: 'Fett',
  carbs: 'Kohlenhydrate',
}

function App() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('checking')
  const [requestStatus, setRequestStatus] = useState<RequestStatus>('idle')
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
    return () => controller.abort()
  }, [])

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
        meal_count: Number(form.get('mealCount')),
      })
      setResult(nextResult)
      setRequestStatus('success')
    } catch {
      setRequestStatus('error')
    }
  }

  return (
    <main>
      <header>
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">P</span>
          <span className="brand-name">PrepPilot</span>
        </div>
        <span className={`system-status system-status--${systemStatus}`}>
          <span className="status-indicator" aria-hidden="true" />
          {systemStatus === 'ready'
            ? 'System bereit'
            : systemStatus === 'unavailable'
              ? 'System nicht erreichbar'
              : 'Verbindung wird geprüft'}
        </span>
      </header>

      <section className="intro">
        <p className="eyebrow">Tagesplaner</p>
        <h1>Ein Tagesplan, der zu deinen Zielen passt.</h1>
        <p className="intro-copy">
          Gib deine Tagesziele ein. PrepPilot kombiniert daraus passende
          Mahlzeiten und zeigt Abweichungen offen an.
        </p>
      </section>

      <form className="target-form" onSubmit={handleSubmit}>
        <NumberField name="calories" label="Kalorien" unit="kcal" value={2500} />
        <NumberField name="protein" label="Protein mindestens" unit="g" value={220} />
        <NumberField name="fat" label="Fett höchstens" unit="g" value={71} />
        <NumberField name="carbs" label="Kohlenhydrate" unit="g" value={233} />
        <label className="field">
          <span>Mahlzeiten</span>
          <select name="mealCount" defaultValue="5">
            {[3, 4, 5, 6].map((count) => (
              <option key={count} value={count}>{count}</option>
            ))}
          </select>
        </label>
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
    </main>
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
          festgelegten Grenzen. Passe ein Ziel oder die Mahlzeitenanzahl an.
        </p>
      </section>
    )
  }

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
      {selectedPlanIndex !== null && result.plans[selectedPlanIndex] && (
        <div className="selection-summary" role="status">
          <span className="selection-check" aria-hidden="true">✓</span>
          <div>
            <strong>Vorschlag {selectedPlanIndex + 1} ausgewählt</strong>
            <p>Dieser Tagesplan ist für den nächsten Schritt vorgemerkt.</p>
          </div>
        </div>
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
          <h3>{plan.status === 'valid' ? 'Ziele erfüllt' : 'Annäherung'}</h3>
        </div>
        <span className={`plan-badge plan-badge--${plan.status}`}>
          {plan.status === 'valid' ? 'Gültig' : 'Mit Abweichung'}
        </span>
      </div>

      <div className="nutrient-grid">
        <Nutrient label="Kalorien" value={plan.nutrients.calories} unit="kcal" />
        <Nutrient label="Protein" value={plan.nutrients.protein} unit="g" />
        <Nutrient label="Kohlenhydrate" value={plan.nutrients.carbs} unit="g" />
        <Nutrient label="Fett" value={plan.nutrients.fat} unit="g" />
      </div>

      <div className="rule-list">
        {plan.evaluations.map((evaluation) => (
          <span
            key={evaluation.metric}
            className={
              evaluation.satisfied ? 'rule rule--met' : 'rule rule--missed'
            }
          >
            {metricNames[evaluation.metric]}:{' '}
            {evaluation.satisfied ? 'im Ziel' : 'abweichend'}
          </span>
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
        {plan.meals.map((meal) => (
          <details key={`${meal.role}-${meal.key}`} className="meal">
            <summary>
              <span>
                <small>{roleNames[meal.role] ?? meal.role}</small>
                <strong>{meal.name}</strong>
              </span>
              <span>{formatNumber(meal.nutrients.calories)} kcal</span>
            </summary>
            <ul>
              {meal.ingredients.map((ingredient) => (
                <li key={ingredient.food_key}>
                  <span>{ingredient.name}</span>
                  <span>
                    {formatNumber(ingredient.amount)} {ingredient.unit}
                  </span>
                </li>
              ))}
            </ul>
          </details>
        ))}
      </div>
    </article>
  )
}

function Nutrient({
  label,
  value,
  unit,
}: {
  label: string
  value: number
  unit: string
}) {
  return (
    <div className="nutrient">
      <span>{label}</span>
      <strong>
        {formatNumber(value)} <small>{unit}</small>
      </strong>
    </div>
  )
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('de-DE', {
    maximumFractionDigits: 1,
  }).format(value)
}

export default App
