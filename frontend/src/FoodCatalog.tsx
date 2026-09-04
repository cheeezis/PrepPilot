import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  createFood,
  deleteFood,
  listFoods,
  type BaseUnit,
  type Food,
  type FoodInput,
  updateFood,
} from './api/foods'

type FoodDraft = {
  name: string
  base_unit: BaseUnit
  calories_kcal: string
  protein_g: string
  carbohydrates_g: string
  fat_g: string
}

const emptyDraft: FoodDraft = {
  name: '', base_unit: 'g', calories_kcal: '', protein_g: '',
  carbohydrates_g: '', fat_g: '',
}

export function FoodCatalog() {
  const [foods, setFoods] = useState<Food[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [draft, setDraft] = useState<FoodDraft>(emptyDraft)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    let active = true
    listFoods(controller.signal)
      .then((items) => { if (active) setFoods(items) })
      .catch((reason: unknown) => { if (active) setError(errorMessage(reason)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false; controller.abort() }
  }, [])

  async function submitFood(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const input = draftToInput(draft)
      const saved = editingId ? await updateFood(editingId, input) : await createFood(input)
      setFoods((current) => sortFoods(editingId
        ? current.map((food) => food.id === saved.id ? saved : food)
        : [...current, saved]))
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
    <section className="catalog-layout">
      <form className="food-form" onSubmit={submitFood}>
        <div className="section-heading">
          <p className="eyebrow">{editingId ? 'Bearbeiten' : 'Neu anlegen'}</p>
          <h2>{editingId ? 'Lebensmittel ändern' : 'Lebensmittel hinzufügen'}</h2>
        </div>

        <label className="field field--wide"><span>Name</span><input required maxLength={200} value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} placeholder="z. B. Haferflocken" /></label>
        <label className="field field--unit"><span>Bezugsgröße</span><select value={draft.base_unit} onChange={(event) => setDraft({ ...draft, base_unit: event.target.value as BaseUnit })}><option value="g">pro 100 g</option><option value="ml">pro 100 ml</option></select></label>
        <NutrientField label="Kalorien" unit="kcal" value={draft.calories_kcal} onChange={(value) => setDraft({ ...draft, calories_kcal: value })} />
        <NutrientField label="Protein" unit="g" value={draft.protein_g} onChange={(value) => setDraft({ ...draft, protein_g: value })} />
        <NutrientField label="Kohlenhydrate" unit="g" value={draft.carbohydrates_g} onChange={(value) => setDraft({ ...draft, carbohydrates_g: value })} />
        <NutrientField label="Fett" unit="g" value={draft.fat_g} onChange={(value) => setDraft({ ...draft, fat_g: value })} />
        <div className="form-actions"><button type="submit" disabled={saving}>{saving ? 'Wird gespeichert …' : editingId ? 'Änderungen speichern' : 'Hinzufügen'}</button>{editingId && <button type="button" className="button-secondary" onClick={resetForm}>Abbrechen</button>}</div>
      </form>

      <section className="food-catalog" aria-labelledby="food-catalog-title">
        <div className="catalog-heading"><div><p className="eyebrow">Persönlicher Bestand</p><h2 id="food-catalog-title">Lebensmittel</h2></div><span>{foods.length}</span></div>
        {error && <p className="notice notice--error">{error}</p>}
        {loading ? <p className="notice">Lebensmittel werden geladen …</p> : foods.length === 0 ? (
          <div className="empty-state"><div className="empty-state__icon" aria-hidden="true">100</div><div><h3>Noch keine Lebensmittel</h3><p>Lege links das erste Lebensmittel mit seinen Nährwerten an.</p></div></div>
        ) : (
          <div className="food-list">{foods.map((food) => <article className="food-card" key={food.id}>
            <div className="food-card__heading"><div><h3>{food.name}</h3><p>pro 100 {food.base_unit}</p></div><div className="food-actions"><button type="button" onClick={() => editFood(food)}>Bearbeiten</button><button type="button" onClick={() => void removeFood(food)}>Löschen</button></div></div>
            <dl className="nutrient-list"><NutrientValue label="Kalorien" value={food.calories_kcal} unit="kcal" /><NutrientValue label="Protein" value={food.protein_g} unit="g" /><NutrientValue label="Kohlenhydrate" value={food.carbohydrates_g} unit="g" /><NutrientValue label="Fett" value={food.fat_g} unit="g" /></dl>
          </article>)}</div>
        )}
      </section>
    </section>
  )
}

function NutrientField(props: { label: string; unit: string; value: string; onChange: (value: string) => void }) {
  return <label className="field"><span>{props.label}</span><div className="number-input"><input required type="number" min="0" step="0.01" value={props.value} onChange={(event) => props.onChange(event.target.value)} /><small>{props.unit}</small></div></label>
}

function NutrientValue(props: { label: string; value: number; unit: string }) {
  return <div><dt>{props.label}</dt><dd>{formatNutrient(props.value)} {props.unit}</dd></div>
}

function draftToInput(draft: FoodDraft): FoodInput {
  return { name: draft.name, base_unit: draft.base_unit, calories_kcal: Number(draft.calories_kcal), protein_g: Number(draft.protein_g), carbohydrates_g: Number(draft.carbohydrates_g), fat_g: Number(draft.fat_g) }
}

function sortFoods(foods: Food[]): Food[] {
  return [...foods].sort((left, right) => left.name.localeCompare(right.name, 'de', { sensitivity: 'base' }))
}

function formatNutrient(value: number): string {
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(value)
}

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : 'Ein unbekannter Fehler ist aufgetreten'
}
