import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'
import {
  createFood,
  deleteFood,
  listFoods,
  type BaseUnit,
  type Food,
  type FoodInput,
  updateFood,
} from './api/foods'
import { getHealth } from './api/health'

type SystemState = 'checking' | 'ready' | 'unavailable'
type FoodDraft = {
  name: string
  base_unit: BaseUnit
  calories_kcal: string
  protein_g: string
  carbohydrates_g: string
  fat_g: string
}

const emptyDraft: FoodDraft = {
  name: '',
  base_unit: 'g',
  calories_kcal: '',
  protein_g: '',
  carbohydrates_g: '',
  fat_g: '',
}

export default function App() {
  const [systemState, setSystemState] = useState<SystemState>('checking')
  const [foods, setFoods] = useState<Food[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [draft, setDraft] = useState<FoodDraft>(emptyDraft)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)

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

    listFoods(controller.signal)
      .then((items) => {
        if (active) setFoods(items)
      })
      .catch((reason: unknown) => {
        if (active) setError(errorMessage(reason))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
      controller.abort()
    }
  }, [])

  async function submitFood(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const input = draftToInput(draft)
      const saved = editingId
        ? await updateFood(editingId, input)
        : await createFood(input)
      setFoods((current) =>
        sortFoods(
          editingId
            ? current.map((food) => (food.id === saved.id ? saved : food))
            : [...current, saved],
        ),
      )
      resetForm()
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setSaving(false)
    }
  }

  function editFood(food: Food) {
    setEditingId(food.id)
    setDraft({
      name: food.name,
      base_unit: food.base_unit,
      calories_kcal: String(food.calories_kcal),
      protein_g: String(food.protein_g),
      carbohydrates_g: String(food.carbohydrates_g),
      fat_g: String(food.fat_g),
    })
    setError(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function removeFood(food: Food) {
    if (!window.confirm(`„${food.name}“ wirklich löschen?`)) return
    setError(null)
    try {
      await deleteFood(food.id)
      setFoods((current) => current.filter((item) => item.id !== food.id))
      if (editingId === food.id) resetForm()
    } catch (reason) {
      setError(errorMessage(reason))
    }
  }

  function resetForm() {
    setDraft(emptyDraft)
    setEditingId(null)
  }

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
        <p className="eyebrow">V5 · Lebensmittelkatalog</p>
        <h1 id="page-title">Deine Lebensmittel. Eine verlässliche Basis.</h1>
        <p>
          Hinterlege die Nährwerte einmal pro 100 g oder 100 ml. Rezepte und
          Wochenpläne bauen anschließend auf denselben Daten auf.
        </p>
      </section>

      <section className="catalog-layout">
        <form className="food-form" onSubmit={submitFood}>
          <div className="section-heading">
            <p className="eyebrow">{editingId ? 'Bearbeiten' : 'Neu anlegen'}</p>
            <h2>{editingId ? 'Lebensmittel ändern' : 'Lebensmittel hinzufügen'}</h2>
          </div>

          <label className="field field--wide">
            <span>Name</span>
            <input
              required
              maxLength={200}
              value={draft.name}
              onChange={(event) => setDraft({ ...draft, name: event.target.value })}
              placeholder="z. B. Haferflocken"
            />
          </label>

          <label className="field field--unit">
            <span>Bezugsgröße</span>
            <select
              value={draft.base_unit}
              onChange={(event) =>
                setDraft({ ...draft, base_unit: event.target.value as BaseUnit })
              }
            >
              <option value="g">pro 100 g</option>
              <option value="ml">pro 100 ml</option>
            </select>
          </label>

          <NutrientField
            label="Kalorien"
            unit="kcal"
            value={draft.calories_kcal}
            onChange={(value) => setDraft({ ...draft, calories_kcal: value })}
          />
          <NutrientField
            label="Protein"
            unit="g"
            value={draft.protein_g}
            onChange={(value) => setDraft({ ...draft, protein_g: value })}
          />
          <NutrientField
            label="Kohlenhydrate"
            unit="g"
            value={draft.carbohydrates_g}
            onChange={(value) => setDraft({ ...draft, carbohydrates_g: value })}
          />
          <NutrientField
            label="Fett"
            unit="g"
            value={draft.fat_g}
            onChange={(value) => setDraft({ ...draft, fat_g: value })}
          />

          <div className="form-actions">
            <button type="submit" disabled={saving}>
              {saving ? 'Wird gespeichert …' : editingId ? 'Änderungen speichern' : 'Hinzufügen'}
            </button>
            {editingId && (
              <button type="button" className="button-secondary" onClick={resetForm}>
                Abbrechen
              </button>
            )}
          </div>
        </form>

        <section className="food-catalog" aria-labelledby="catalog-title">
          <div className="catalog-heading">
            <div>
              <p className="eyebrow">Persönlicher Bestand</p>
              <h2 id="catalog-title">Lebensmittel</h2>
            </div>
            <span>{foods.length}</span>
          </div>

          {error && <p className="notice notice--error">{error}</p>}
          {loading ? (
            <p className="notice">Lebensmittel werden geladen …</p>
          ) : foods.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state__icon" aria-hidden="true">100</div>
              <div>
                <h3>Noch keine Lebensmittel</h3>
                <p>Lege links das erste Lebensmittel mit seinen Nährwerten an.</p>
              </div>
            </div>
          ) : (
            <div className="food-list">
              {foods.map((food) => (
                <article className="food-card" key={food.id}>
                  <div className="food-card__heading">
                    <div>
                      <h3>{food.name}</h3>
                      <p>pro 100 {food.base_unit}</p>
                    </div>
                    <div className="food-actions">
                      <button type="button" onClick={() => editFood(food)}>Bearbeiten</button>
                      <button type="button" onClick={() => void removeFood(food)}>Löschen</button>
                    </div>
                  </div>
                  <dl className="nutrient-list">
                    <NutrientValue label="Kalorien" value={food.calories_kcal} unit="kcal" />
                    <NutrientValue label="Protein" value={food.protein_g} unit="g" />
                    <NutrientValue label="Kohlenhydrate" value={food.carbohydrates_g} unit="g" />
                    <NutrientValue label="Fett" value={food.fat_g} unit="g" />
                  </dl>
                </article>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  )
}

function NutrientField(props: {
  label: string
  unit: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <label className="field">
      <span>{props.label}</span>
      <div className="number-input">
        <input
          required
          type="number"
          min="0"
          step="0.01"
          value={props.value}
          onChange={(event) => props.onChange(event.target.value)}
        />
        <small>{props.unit}</small>
      </div>
    </label>
  )
}

function NutrientValue(props: { label: string; value: number; unit: string }) {
  return (
    <div>
      <dt>{props.label}</dt>
      <dd>{formatNutrient(props.value)} {props.unit}</dd>
    </div>
  )
}

function draftToInput(draft: FoodDraft): FoodInput {
  return {
    name: draft.name,
    base_unit: draft.base_unit,
    calories_kcal: Number(draft.calories_kcal),
    protein_g: Number(draft.protein_g),
    carbohydrates_g: Number(draft.carbohydrates_g),
    fat_g: Number(draft.fat_g),
  }
}

function sortFoods(foods: Food[]): Food[] {
  return [...foods].sort((left, right) =>
    left.name.localeCompare(right.name, 'de', { sensitivity: 'base' }),
  )
}

function formatNutrient(value: number): string {
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(value)
}

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : 'Ein unbekannter Fehler ist aufgetreten'
}
