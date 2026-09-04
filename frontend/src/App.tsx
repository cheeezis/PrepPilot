import { useEffect, useState, type FormEvent, type MouseEvent } from 'react'
import {
  createDayPlans,
  type DayPlan,
  type DayPlansResponse,
  type RuleEvaluation,
} from './api/dayPlans'
import { getHealth } from './api/health'
import {
  createRecipe,
  deleteRecipe,
  getRecipes,
  updateRecipe,
  type Recipe,
  type RecipeCategory,
  type RecipeInput,
} from './api/recipes'
import './App.css'

type SystemStatus = 'checking' | 'ready' | 'unavailable'
type RequestStatus = 'idle' | 'loading' | 'success' | 'error'
type RecipeStatus = 'loading' | 'success' | 'error'
type SaveStatus = 'idle' | 'loading' | 'error'
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

const categoryNames: Record<RecipeCategory, string> = {
  breakfast: 'Frühstück',
  lunch: 'Mittagessen',
  dinner: 'Abendessen',
  snack: 'Snack',
}

const mealCategories = Object.keys(categoryNames) as RecipeCategory[]

function App() {
  const [page, setPage] = useState<AppPage>(() => pageFromPath())
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('checking')
  const [requestStatus, setRequestStatus] = useState<RequestStatus>('idle')
  const [recipeStatus, setRecipeStatus] = useState<RecipeStatus>('loading')
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [editingRecipe, setEditingRecipe] = useState<Recipe | null>(null)
  const [recipeEditorVersion, setRecipeEditorVersion] = useState(0)
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle')
  const [result, setResult] = useState<DayPlansResponse | null>(null)
  const [selectedPlanIndex, setSelectedPlanIndex] = useState<number | null>(null)
  const [selectedMeals, setSelectedMeals] = useState<RecipeCategory[]>([
    'breakfast',
    'lunch',
    'dinner',
  ])

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
        meal_categories: selectedMeals,
      })
      setResult(nextResult)
      setRequestStatus('success')
    } catch {
      setRequestStatus('error')
    }
  }

  function toggleMeal(category: RecipeCategory) {
    setSelectedMeals((current) => {
      if (current.includes(category)) {
        return current.length === 1
          ? current
          : current.filter((item) => item !== category)
      }
      return mealCategories.filter((item) => (
        current.includes(item) || item === category
      ))
    })
    setResult(null)
    setSelectedPlanIndex(null)
  }

  async function handleRecipeSave(input: RecipeInput) {
    setSaveStatus('loading')
    try {
      if (editingRecipe) {
        await updateRecipe(editingRecipe.id, input)
      } else {
        await createRecipe(input)
      }
      setRecipes(await getRecipes())
      setEditingRecipe(null)
      setRecipeEditorVersion((current) => current + 1)
      setRecipeStatus('success')
      setSaveStatus('idle')
    } catch {
      setSaveStatus('error')
    }
  }

  async function handleRecipeDelete(recipe: Recipe) {
    if (!window.confirm(`„${recipe.title}“ wirklich löschen?`)) return
    try {
      await deleteRecipe(recipe.id)
      setRecipes((current) => current.filter((item) => item.id !== recipe.id))
      if (editingRecipe?.id === recipe.id) setEditingRecipe(null)
    } catch {
      setRecipeStatus('error')
    }
  }

  function handleRecipeEdit(recipe: Recipe) {
    setEditingRecipe(recipe)
    setSaveStatus('idle')
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
              Gib deine Tagesziele ein und wähle deine Mahlzeiten. PrepPilot
              kombiniert passende Rezepte und zeigt Abweichungen offen an.
            </p>
          </section>

          <form className="target-form" onSubmit={handleSubmit}>
            <NumberField name="calories" label="Kalorien" unit="kcal" value={2000} />
            <NumberField name="protein" label="Protein mindestens" unit="g" value={120} />
            <NumberField name="fat" label="Fett höchstens" unit="g" value={70} />
            <NumberField name="carbs" label="Kohlenhydrate" unit="g" value={220} />
            <fieldset className="meal-selector">
              <legend>Mahlzeiten im Tagesplan</legend>
              <div>
                {mealCategories.map((category) => (
                  <label key={category}>
                    <input
                      type="checkbox"
                      checked={selectedMeals.includes(category)}
                      onChange={() => toggleMeal(category)}
                      disabled={selectedMeals.length === 1 && selectedMeals[0] === category}
                    />
                    <span>{categoryNames[category]}</span>
                  </label>
                ))}
              </div>
              <small>Mindestens eine Mahlzeit bleibt ausgewählt.</small>
            </fieldset>
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
            <p className="eyebrow">Meine Rezepte</p>
            <h1>Plane mit Gerichten, die wirklich zu dir passen.</h1>
            <p className="intro-copy">
              Hinterlege deine eigenen Rezepte mit Portionszahl und Nährwerten.
              PrepPilot verwendet genau diese Angaben für deine Tagespläne.
            </p>
          </section>

          <RecipeEditor
            key={`${editingRecipe?.id ?? 'new'}-${recipeEditorVersion}`}
            recipe={editingRecipe}
            status={saveStatus}
            onSave={handleRecipeSave}
            onCancel={() => {
              setEditingRecipe(null)
              setSaveStatus('idle')
            }}
          />

          <RecipeInventory
            status={recipeStatus}
            recipes={recipes}
            onEdit={handleRecipeEdit}
            onDelete={handleRecipeDelete}
          />
        </>
      )}
    </main>
  )
}

function RecipeEditor({
  recipe,
  status,
  onSave,
  onCancel,
}: {
  recipe: Recipe | null
  status: SaveStatus
  onSave: (input: RecipeInput) => Promise<void>
  onCancel: () => void
}) {
  const [categories, setCategories] = useState<RecipeCategory[]>(
    recipe?.categories ?? ['dinner'],
  )

  function toggleCategory(category: RecipeCategory) {
    setCategories((current) => {
      if (current.includes(category)) {
        return current.length === 1
          ? current
          : current.filter((item) => item !== category)
      }
      return mealCategories.filter((item) => (
        current.includes(item) || item === category
      ))
    })
  }

  async function handleRecipeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    await onSave({
      title: String(form.get('title')),
      categories,
      servings: Number(form.get('servings')),
      calories_per_serving: Number(form.get('calories_per_serving')),
      protein_per_serving: Number(form.get('protein_per_serving')),
      carbs_per_serving: Number(form.get('carbs_per_serving')),
      fat_per_serving: Number(form.get('fat_per_serving')),
      sugar_per_serving: optionalNumber(form.get('sugar_per_serving')),
      saturated_fat_per_serving: optionalNumber(form.get('saturated_fat_per_serving')),
      fiber_per_serving: optionalNumber(form.get('fiber_per_serving')),
      salt_per_serving: optionalNumber(form.get('salt_per_serving')),
      ingredients: splitLines(form.get('ingredients')),
      instructions: splitLines(form.get('instructions')),
      preparation_minutes: optionalNumber(form.get('preparation_minutes')),
      cooking_minutes: optionalNumber(form.get('cooking_minutes')),
      source_url: optionalText(form.get('source_url')),
    })
  }

  return (
    <section className="recipe-editor" aria-labelledby="recipe-editor-heading">
      <div>
        <p className="eyebrow">{recipe ? 'Rezept bearbeiten' : 'Neues Rezept'}</p>
        <h2 id="recipe-editor-heading">
          {recipe ? recipe.title : 'Eigenes Rezept hinzufügen'}
        </h2>
        <p>Alle Nährwerte beziehen sich auf eine Portion.</p>
      </div>
      <form onSubmit={handleRecipeSubmit}>
        <label className="field recipe-title-field">
          <span>Rezeptname</span>
          <input name="title" defaultValue={recipe?.title ?? ''} required />
        </label>
        <RecipeNumberField name="servings" label="Rezept ergibt" unit="Portionen" value={recipe?.servings ?? 4} />
        <fieldset className="recipe-category-selector">
          <legend>Geeignet für</legend>
          <div>
            {mealCategories.map((category) => (
              <label key={category}>
                <input
                  type="checkbox"
                  checked={categories.includes(category)}
                  onChange={() => toggleCategory(category)}
                  disabled={categories.length === 1 && categories[0] === category}
                />
                <span>{categoryNames[category]}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <div className="recipe-form-section">
          <h3>Nährwerte pro Portion</h3>
          <div className="recipe-number-grid">
            <RecipeNumberField name="calories_per_serving" label="Kalorien" unit="kcal" value={recipe?.nutrients.calories ?? 500} />
            <RecipeNumberField name="protein_per_serving" label="Protein" unit="g" value={recipe?.nutrients.protein ?? 30} allowZero />
            <RecipeNumberField name="carbs_per_serving" label="Kohlenhydrate" unit="g" value={recipe?.nutrients.carbs ?? 50} allowZero />
            <RecipeNumberField name="fat_per_serving" label="Fett" unit="g" value={recipe?.nutrients.fat ?? 15} allowZero />
            <RecipeNumberField name="sugar_per_serving" label="Zucker, optional" unit="g" value={recipe?.nutrients.sugar ?? ''} optional />
            <RecipeNumberField name="saturated_fat_per_serving" label="Gesättigte Fettsäuren, optional" unit="g" value={recipe?.nutrients.saturated_fat ?? ''} optional />
            <RecipeNumberField name="fiber_per_serving" label="Ballaststoffe, optional" unit="g" value={recipe?.nutrients.fiber ?? ''} optional />
            <RecipeNumberField name="salt_per_serving" label="Salz, optional" unit="g" value={recipe?.nutrients.salt ?? ''} optional />
          </div>
        </div>
        <div className="recipe-text-grid">
          <label className="field">
            <span>Zutaten – eine Zutat pro Zeile</span>
            <textarea name="ingredients" rows={7} defaultValue={recipe?.ingredients.join('\n') ?? ''} required />
          </label>
          <label className="field">
            <span>Zubereitung – ein Schritt pro Zeile</span>
            <textarea name="instructions" rows={7} defaultValue={recipe?.instructions.join('\n') ?? ''} required />
          </label>
        </div>
        <div className="recipe-number-grid recipe-number-grid--optional">
          <RecipeNumberField name="preparation_minutes" label="Vorbereitung, optional" unit="Min." value={recipe?.preparation_minutes ?? ''} optional />
          <RecipeNumberField name="cooking_minutes" label="Kochzeit, optional" unit="Min." value={recipe?.cooking_minutes ?? ''} optional />
          <label className="field recipe-source-field">
            <span>Quellenlink, optional</span>
            <input name="source_url" type="url" defaultValue={recipe?.source_url ?? ''} placeholder="https://…" />
          </label>
        </div>
        {status === 'error' && (
          <p className="notice notice--error">Das Rezept konnte nicht gespeichert werden.</p>
        )}
        <div className="recipe-form-actions">
          <button type="submit" disabled={status === 'loading'}>
            {status === 'loading'
              ? 'Rezept wird gespeichert …'
              : recipe
                ? 'Änderungen speichern'
                : 'Rezept speichern'}
          </button>
          {recipe && (
            <button type="button" className="secondary-button" onClick={onCancel}>
              Bearbeiten abbrechen
            </button>
          )}
        </div>
      </form>
    </section>
  )
}

function RecipeNumberField({
  name,
  label,
  unit,
  value,
  optional = false,
  allowZero = false,
}: {
  name: string
  label: string
  unit: string
  value: number | ''
  optional?: boolean
  allowZero?: boolean
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <span className="number-input">
        <input
          name={name}
          type="number"
          min={allowZero || optional ? '0' : '0.01'}
          step="0.01"
          defaultValue={value}
          required={!optional}
        />
        <small>{unit}</small>
      </span>
    </label>
  )
}

function RecipeInventory({
  status,
  recipes,
  onEdit,
  onDelete,
}: {
  status: RecipeStatus
  recipes: Recipe[]
  onEdit: (recipe: Recipe) => void
  onDelete: (recipe: Recipe) => void
}) {
  const [categoryFilter, setCategoryFilter] = useState<'all' | RecipeCategory>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const normalizedSearch = searchTerm.trim().toLocaleLowerCase('de')
  const visibleRecipes = recipes.filter((recipe) => (
    (categoryFilter === 'all' || recipe.categories.includes(categoryFilter))
    && (normalizedSearch === '' || recipe.title.toLocaleLowerCase('de').includes(normalizedSearch))
  ))

  return (
    <section className="recipe-inventory" aria-labelledby="recipes-heading">
      <div className="inventory-heading">
        <div>
          <p className="eyebrow">Persönlicher Bestand</p>
          <h2 id="recipes-heading">Meine gespeicherten Rezepte</h2>
        </div>
        {status === 'success' && (
          <strong className="inventory-count">
            {recipes.length} {recipes.length === 1 ? 'Rezept' : 'Rezepte'}
          </strong>
        )}
      </div>

      {status === 'success' && recipes.length > 0 && (
        <div className="recipe-filters">
          <label className="recipe-search">
            <span>Rezepte durchsuchen</span>
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="z. B. Curry"
            />
          </label>
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
              <span>{recipes.filter((recipe) => recipe.categories.includes(category)).length}</span>
            </button>
          ))}
          </div>
        </div>
      )}

      {status === 'loading' && <p>Rezeptbestand wird geladen …</p>}
      {status === 'error' && (
        <p className="notice notice--error">
          Der Rezeptbestand konnte nicht geladen werden.
        </p>
      )}
      {status === 'success' && recipes.length === 0 && (
        <p>Noch keine eigenen Rezepte gespeichert. Lege oben dein erstes an.</p>
      )}
      {recipes.length > 0 && (
        <div className="recipe-list">
          {visibleRecipes.map((recipe) => (
            <details className="recipe-card" key={recipe.id}>
              <summary>
                <div className="recipe-card-title">
                  <strong>{recipe.title}</strong>
                  <small>
                    {recipe.categories.map((category) => categoryNames[category]).join(' · ')}
                  </small>
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
                {recipe.source_url ? (
                  <a href={recipe.source_url} target="_blank" rel="noreferrer">
                    Optionale Rezeptquelle öffnen
                  </a>
                ) : <small>Eigenes Rezept ohne externe Quelle</small>}
                <span className="recipe-actions">
                  <button type="button" onClick={() => onEdit(recipe)}>Bearbeiten</button>
                  <button type="button" onClick={() => onDelete(recipe)}>Löschen</button>
                </span>
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
              <p>Dieser Vorschlag kombiniert deine gespeicherten Rezepte.</p>
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
            {recipe.source_url && (
              <a href={recipe.source_url} target="_blank" rel="noreferrer">
                Rezeptquelle öffnen
              </a>
            )}
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

function splitLines(value: FormDataEntryValue | null) {
  return String(value ?? '')
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function optionalNumber(value: FormDataEntryValue | null) {
  const text = String(value ?? '').trim()
  return text === '' ? null : Number(text)
}

function optionalText(value: FormDataEntryValue | null) {
  const text = String(value ?? '').trim()
  return text === '' ? null : text
}

export default App
