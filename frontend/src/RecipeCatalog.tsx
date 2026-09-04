import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { listFoods, type Food } from './api/foods'
import {
  createRecipe,
  deleteRecipe,
  listRecipes,
  type MealRole,
  type Nutrients,
  type Recipe,
  type RecipeInput,
  updateRecipe,
} from './api/recipes'

type IngredientDraft = { food_id: string; amount: string }
type RecipeDraft = {
  title: string
  servings: string
  meal_roles: MealRole[]
  ingredients: IngredientDraft[]
  instructions: string
}

const mealRoles: Array<{ value: MealRole; label: string }> = [
  { value: 'breakfast', label: 'Frühstück' },
  { value: 'lunch', label: 'Mittagessen' },
  { value: 'dinner', label: 'Abendessen' },
  { value: 'snack', label: 'Snack' },
]

const emptyDraft: RecipeDraft = {
  title: '',
  servings: '1',
  meal_roles: [],
  ingredients: [{ food_id: '', amount: '' }],
  instructions: '',
}

export function RecipeCatalog() {
  const [foods, setFoods] = useState<Food[]>([])
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [draft, setDraft] = useState<RecipeDraft>(emptyDraft)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    let active = true
    Promise.all([listFoods(controller.signal), listRecipes(controller.signal)])
      .then(([foodItems, recipeItems]) => {
        if (!active) return
        setFoods(foodItems)
        setRecipes(recipeItems)
      })
      .catch((reason: unknown) => { if (active) setError(errorMessage(reason)) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false; controller.abort() }
  }, [])

  async function submitRecipe(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const input = draftToInput(draft)
      const saved = editingId
        ? await updateRecipe(editingId, input)
        : await createRecipe(input)
      setRecipes((current) => sortRecipes(editingId
        ? current.map((recipe) => recipe.id === saved.id ? saved : recipe)
        : [...current, saved]))
      resetForm()
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setSaving(false)
    }
  }

  function toggleRole(role: MealRole) {
    setDraft((current) => ({
      ...current,
      meal_roles: current.meal_roles.includes(role)
        ? current.meal_roles.filter((item) => item !== role)
        : [...current.meal_roles, role],
    }))
  }

  function updateIngredient(index: number, change: Partial<IngredientDraft>) {
    setDraft((current) => ({
      ...current,
      ingredients: current.ingredients.map((item, position) =>
        position === index ? { ...item, ...change } : item,
      ),
    }))
  }

  function removeIngredient(index: number) {
    setDraft((current) => ({
      ...current,
      ingredients: current.ingredients.filter((_, position) => position !== index),
    }))
  }

  function editRecipe(recipe: Recipe) {
    setEditingId(recipe.id)
    setDraft({
      title: recipe.title,
      servings: String(recipe.servings),
      meal_roles: recipe.meal_roles,
      ingredients: recipe.ingredients.map((item) => ({
        food_id: String(item.food_id),
        amount: String(item.amount),
      })),
      instructions: recipe.instructions.join('\n'),
    })
    setError(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function removeRecipe(recipe: Recipe) {
    if (!window.confirm(`„${recipe.title}“ wirklich löschen?`)) return
    setError(null)
    try {
      await deleteRecipe(recipe.id)
      setRecipes((current) => current.filter((item) => item.id !== recipe.id))
      if (editingId === recipe.id) resetForm()
    } catch (reason) {
      setError(errorMessage(reason))
    }
  }

  function resetForm() {
    setDraft(emptyDraft)
    setEditingId(null)
  }

  return (
    <section className="catalog-layout catalog-layout--recipes">
      <form className="food-form recipe-form" onSubmit={submitRecipe}>
        <div className="section-heading"><p className="eyebrow">{editingId ? 'Bearbeiten' : 'Neu anlegen'}</p><h2>{editingId ? 'Rezept ändern' : 'Rezept hinzufügen'}</h2></div>
        {foods.length === 0 && !loading && <p className="notice field--wide">Lege zuerst mindestens ein Lebensmittel an.</p>}
        <label className="field field--wide"><span>Titel</span><input required maxLength={300} value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} placeholder="z. B. Porridge" /></label>
        <label className="field field--wide"><span>Portionen</span><input required type="number" min="1" step="1" value={draft.servings} onChange={(event) => setDraft({ ...draft, servings: event.target.value })} /></label>

        <fieldset className="role-picker"><legend>Geeignet als</legend>{mealRoles.map((role) => <label key={role.value}><input type="checkbox" checked={draft.meal_roles.includes(role.value)} onChange={() => toggleRole(role.value)} />{role.label}</label>)}</fieldset>

        <fieldset className="ingredient-editor"><legend>Zutaten</legend>{draft.ingredients.map((ingredient, index) => {
          const selectedFood = foods.find((food) => food.id === Number(ingredient.food_id))
          return <div className="ingredient-row" key={index}>
            <select required aria-label={`Lebensmittel ${index + 1}`} value={ingredient.food_id} onChange={(event) => updateIngredient(index, { food_id: event.target.value })}><option value="">Lebensmittel wählen</option>{foods.map((food) => <option value={food.id} key={food.id}>{food.name}</option>)}</select>
            <div className="number-input"><input required aria-label={`Menge ${index + 1}`} type="number" min="0.001" step="0.001" value={ingredient.amount} onChange={(event) => updateIngredient(index, { amount: event.target.value })} /><small>{selectedFood?.base_unit ?? 'g/ml'}</small></div>
            {draft.ingredients.length > 1 && <button type="button" className="button-icon" aria-label={`Zutat ${index + 1} entfernen`} onClick={() => removeIngredient(index)}>×</button>}
          </div>
        })}<button type="button" className="button-secondary" disabled={foods.length === 0} onClick={() => setDraft((current) => ({ ...current, ingredients: [...current.ingredients, { food_id: '', amount: '' }] }))}>Weitere Zutat</button></fieldset>

        <label className="field field--wide"><span>Zubereitung <small>ein Schritt pro Zeile</small></span><textarea required rows={5} value={draft.instructions} onChange={(event) => setDraft({ ...draft, instructions: event.target.value })} placeholder={'Zutaten vermengen\nKurz aufkochen\nServieren'} /></label>
        <div className="form-actions"><button type="submit" disabled={saving || foods.length === 0 || draft.meal_roles.length === 0}>{saving ? 'Wird gespeichert …' : editingId ? 'Änderungen speichern' : 'Hinzufügen'}</button>{editingId && <button type="button" className="button-secondary" onClick={resetForm}>Abbrechen</button>}</div>
      </form>

      <section className="food-catalog" aria-labelledby="recipe-catalog-title">
        <div className="catalog-heading"><div><p className="eyebrow">Persönliche Sammlung</p><h2 id="recipe-catalog-title">Rezepte</h2></div><span>{recipes.length}</span></div>
        {error && <p className="notice notice--error">{error}</p>}
        {loading ? <p className="notice">Rezepte werden geladen …</p> : recipes.length === 0 ? (
          <div className="empty-state"><div className="empty-state__icon" aria-hidden="true">R</div><div><h3>Noch keine Rezepte</h3><p>Kombiniere links deine Lebensmittel zum ersten Rezept.</p></div></div>
        ) : <div className="food-list">{recipes.map((recipe) => <RecipeCard key={recipe.id} recipe={recipe} onEdit={() => editRecipe(recipe)} onDelete={() => void removeRecipe(recipe)} />)}</div>}
      </section>
    </section>
  )
}

function RecipeCard({ recipe, onEdit, onDelete }: { recipe: Recipe; onEdit: () => void; onDelete: () => void }) {
  return <article className="food-card recipe-card">
    <div className="food-card__heading"><div><h3>{recipe.title}</h3><p>{recipe.servings} {recipe.servings === 1 ? 'Portion' : 'Portionen'} · {recipe.is_meal_prep ? 'Meal Prep' : 'Einzelportion'}</p></div><div className="food-actions"><button type="button" onClick={onEdit}>Bearbeiten</button><button type="button" onClick={onDelete}>Löschen</button></div></div>
    <div className="role-tags">{recipe.meal_roles.map((role) => <span key={role}>{roleLabel(role)}</span>)}</div>
    <p className="recipe-ingredients">{recipe.ingredients.map((item) => `${formatNumber(item.amount)} ${item.unit} ${item.food_name}`).join(' · ')}</p>
    <dl className="nutrient-list"><NutrientValue label="Kalorien" value={recipe.nutrition_per_serving.calories_kcal} unit="kcal" /><NutrientValue label="Protein" value={recipe.nutrition_per_serving.protein_g} unit="g" /><NutrientValue label="Kohlenhydrate" value={recipe.nutrition_per_serving.carbohydrates_g} unit="g" /><NutrientValue label="Fett" value={recipe.nutrition_per_serving.fat_g} unit="g" /></dl>
    <details><summary>Zubereitung und Gesamtwerte</summary><ol>{recipe.instructions.map((step, index) => <li key={index}>{step}</li>)}</ol><p>{nutritionSummary(recipe.nutrition_total)} gesamt</p></details>
  </article>
}

function NutrientValue({ label, value, unit }: { label: string; value: number; unit: string }) {
  return <div><dt>{label}</dt><dd>{formatNumber(value)} {unit}</dd></div>
}

function draftToInput(draft: RecipeDraft): RecipeInput {
  return {
    title: draft.title,
    servings: Number(draft.servings),
    meal_roles: draft.meal_roles,
    ingredients: draft.ingredients.map((item) => ({ food_id: Number(item.food_id), amount: Number(item.amount) })),
    instructions: draft.instructions.split('\n').map((step) => step.trim()).filter(Boolean),
  }
}

function roleLabel(role: MealRole): string {
  return mealRoles.find((item) => item.value === role)?.label ?? role
}

function sortRecipes(recipes: Recipe[]): Recipe[] {
  return [...recipes].sort((left, right) => left.title.localeCompare(right.title, 'de', { sensitivity: 'base' }))
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(value)
}

function nutritionSummary(nutrients: Nutrients): string {
  return `${formatNumber(nutrients.calories_kcal)} kcal · ${formatNumber(nutrients.protein_g)} g Protein · ${formatNumber(nutrients.carbohydrates_g)} g Kohlenhydrate · ${formatNumber(nutrients.fat_g)} g Fett`
}

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : 'Ein unbekannter Fehler ist aufgetreten'
}
