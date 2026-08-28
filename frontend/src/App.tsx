import { useEffect, useState, type FormEvent } from 'react'
import {
  createDayPlans,
  type DayPlan,
  type DayPlansResponse,
  type RuleEvaluation,
} from './api/dayPlans'
import { getHealth } from './api/health'
import { buildShoppingList, weekDays } from './weeklyPlan'
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

const metricUnits: Record<RuleEvaluation['metric'], string> = {
  calories: 'kcal',
  protein: 'g',
  fat: 'g',
  carbs: 'g',
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
              <p>Dieser Tagesplan wird für alle sieben Tage verwendet.</p>
            </div>
          </div>
          <WeeklyPlan plan={selectedPlan} />
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

function WeeklyPlan({ plan }: { plan: DayPlan }) {
  const shoppingList = buildShoppingList(plan.meals)

  return (
    <section className="weekly-plan" aria-labelledby="weekly-plan-heading">
      <div className="weekly-heading">
        <div>
          <p className="eyebrow">Wochenplan</p>
          <h2 id="weekly-plan-heading">Deine Woche</h2>
        </div>
        <p>
          Derselbe Tagesplan gilt von Montag bis Sonntag. So bleibt die Planung
          für den ersten MVP bewusst einfach.
        </p>
      </div>

      <div className="weekly-layout">
        <div className="week-days">
          {weekDays.map((day, index) => (
            <details
              key={day}
              className="week-day"
              data-testid="week-day"
              open={index === 0}
            >
              <summary>
                <span>
                  <strong>{day}</strong>
                  <small>{plan.meals.length} Mahlzeiten</small>
                </span>
                <span>{formatNumber(plan.nutrients.calories)} kcal</span>
              </summary>
              <ul>
                {plan.meals.map((meal) => (
                  <li key={`${day}-${meal.role}-${meal.key}`}>
                    <span>
                      <small>{roleNames[meal.role] ?? meal.role}</small>
                      <strong>{meal.name}</strong>
                    </span>
                    <span>{formatNumber(meal.nutrients.calories)} kcal</span>
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </div>

        <aside className="shopping-list" aria-labelledby="shopping-list-heading">
          <p className="eyebrow">Einkauf</p>
          <h3 id="shopping-list-heading">Einkaufsliste</h3>
          <p className="shopping-list-copy">Gesamtmengen für sieben Tage.</p>
          <ul>
            {shoppingList.map((item) => (
              <li key={`${item.foodKey}-${item.unit}`}>
                <span>{item.name}</span>
                <strong>{formatNumber(item.amount)} {item.unit}</strong>
              </li>
            ))}
          </ul>
        </aside>
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

export default App
