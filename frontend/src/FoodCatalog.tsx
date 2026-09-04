import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  createFoodPortion,
  createFood,
  deleteFoodPortion,
  deleteFood,
  listFoods,
  type BaseUnit,
  type Food,
  type FoodCategory,
  type FoodInput,
  type FoodPortion,
  updateFoodPortion,
  updateFood,
} from './api/foods'
import { foodCategories, foodCategoryLabel } from './foodCategories'

type FoodDraft = {
  name: string
  base_unit: BaseUnit
  category: FoodCategory
  calories_kcal: string
  protein_g: string
  carbohydrates_g: string
  fat_g: string
}

const emptyDraft: FoodDraft = {
  name: '', base_unit: 'g', category: 'other', calories_kcal: '', protein_g: '',
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
      .then((items) => { if (active) setFoods(sortFoods(items)) })
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
      category: food.category,
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

  async function savePortion(food: Food, portion: FoodPortion | null, name: string, amount: number) {
    setError(null)
    try {
      const saved = portion
        ? await updateFoodPortion(food.id, portion.id, { name, amount })
        : await createFoodPortion(food.id, { name, amount })
      setFoods((current) => current.map((item) => item.id !== food.id ? item : {
        ...item,
        portions: portion
          ? item.portions.map((entry) => entry.id === saved.id ? saved : entry)
          : [...item.portions, saved],
      }))
    } catch (reason) {
      setError(errorMessage(reason))
      throw reason
    }
  }

  async function removePortion(food: Food, portion: FoodPortion) {
    if (!window.confirm(`Einheit „${portion.name}“ wirklich löschen?`)) return
    setError(null)
    try {
      await deleteFoodPortion(food.id, portion.id)
      setFoods((current) => current.map((item) => item.id !== food.id ? item : {
        ...item,
        portions: item.portions.filter((entry) => entry.id !== portion.id),
      }))
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
        <label className="field field--wide"><span>Kategorie</span><select value={draft.category} onChange={(event) => setDraft({ ...draft, category: event.target.value as FoodCategory })}>{foodCategories.map((category) => <option value={category.value} key={category.value}>{category.label}</option>)}</select></label>
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
          <FoodCategoryList foods={foods} onEdit={editFood} onDelete={removeFood} onSavePortion={savePortion} onDeletePortion={removePortion} />
        )}
      </section>
    </section>
  )
}

export function FoodCategoryList(props: {
  foods: Food[]
  onEdit: (food: Food) => void
  onDelete: (food: Food) => void
  onSavePortion: (food: Food, portion: FoodPortion | null, name: string, amount: number) => Promise<void>
  onDeletePortion: (food: Food, portion: FoodPortion) => void
}) {
  return <div className="food-category-list">{foodCategories.map((category) => {
    const categoryFoods = props.foods.filter((food) => food.category === category.value)
    if (categoryFoods.length === 0) return null
    return <details className="food-category-group" key={category.value}>
      <summary><span>{category.label}</span><span>{categoryFoods.length}</span></summary>
      <div className="food-list">{categoryFoods.map((food) => <article className="food-card" key={food.id}>
        <div className="food-card__heading"><div><h3>{food.name}</h3><p>pro 100 {food.base_unit}</p></div><div className="food-actions"><button type="button" onClick={() => props.onEdit(food)}>Bearbeiten</button><button type="button" onClick={() => void props.onDelete(food)}>Löschen</button></div></div>
        <span className="food-category">{foodCategoryLabel(food.category)}</span>
        <dl className="nutrient-list"><NutrientValue label="Kalorien" value={food.calories_kcal} unit="kcal" /><NutrientValue label="Protein" value={food.protein_g} unit="g" /><NutrientValue label="Kohlenhydrate" value={food.carbohydrates_g} unit="g" /><NutrientValue label="Fett" value={food.fat_g} unit="g" /></dl>
        <FoodPortionEditor food={food} onSave={props.onSavePortion} onDelete={props.onDeletePortion} />
      </article>)}</div>
    </details>
  })}</div>
}

function FoodPortionEditor(props: {
  food: Food
  onSave: (food: Food, portion: FoodPortion | null, name: string, amount: number) => Promise<void>
  onDelete: (food: Food, portion: FoodPortion) => void
}) {
  const [editing, setEditing] = useState<FoodPortion | null>(null)
  const [name, setName] = useState('')
  const [amount, setAmount] = useState('')
  const [saving, setSaving] = useState(false)

  function select(portion: FoodPortion) {
    setEditing(portion)
    setName(portion.name)
    setAmount(String(portion.amount))
  }

  function reset() {
    setEditing(null)
    setName('')
    setAmount('')
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    try {
      await props.onSave(props.food, editing, name, Number(amount))
      reset()
    } finally {
      setSaving(false)
    }
  }

  return <details className="portion-editor">
    <summary>Einheiten ({props.food.portions.length})</summary>
    {props.food.portions.length > 0 && <ul>{props.food.portions.map((portion) => <li key={portion.id}>
      <span>1 {portion.name} = {formatNutrient(portion.amount)} {props.food.base_unit}</span>
      <span><button type="button" onClick={() => select(portion)}>Ändern</button><button type="button" onClick={() => props.onDelete(props.food, portion)}>Löschen</button></span>
    </li>)}</ul>}
    <form onSubmit={submit}>
      <input required maxLength={50} aria-label={`Einheit für ${props.food.name}`} placeholder="z. B. Stück" value={name} onChange={(event) => setName(event.target.value)} />
      <div className="number-input"><input required type="number" min="0.001" step="0.001" aria-label={`Umrechnung für ${props.food.name}`} value={amount} onChange={(event) => setAmount(event.target.value)} /><small>{props.food.base_unit}</small></div>
      <button type="submit" disabled={saving}>{editing ? 'Speichern' : 'Hinzufügen'}</button>
      {editing && <button type="button" className="button-secondary" onClick={reset}>Abbrechen</button>}
    </form>
  </details>
}

function NutrientField(props: { label: string; unit: string; value: string; onChange: (value: string) => void }) {
  return <label className="field"><span>{props.label}</span><div className="number-input"><input required type="number" min="0" step="0.01" value={props.value} onChange={(event) => props.onChange(event.target.value)} /><small>{props.unit}</small></div></label>
}

function NutrientValue(props: { label: string; value: number; unit: string }) {
  return <div><dt>{props.label}</dt><dd>{formatNutrient(props.value)} {props.unit}</dd></div>
}

function draftToInput(draft: FoodDraft): FoodInput {
  return { name: draft.name, base_unit: draft.base_unit, category: draft.category, calories_kcal: Number(draft.calories_kcal), protein_g: Number(draft.protein_g), carbohydrates_g: Number(draft.carbohydrates_g), fat_g: Number(draft.fat_g) }
}

function sortFoods(foods: Food[]): Food[] {
  return [...foods].sort((left, right) => {
    const categoryOrder = foodCategories.findIndex((item) => item.value === left.category)
      - foodCategories.findIndex((item) => item.value === right.category)
    return categoryOrder || left.name.localeCompare(right.name, 'de', { sensitivity: 'base' })
  })
}

function formatNutrient(value: number): string {
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(value)
}

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : 'Ein unbekannter Fehler ist aufgetreten'
}
