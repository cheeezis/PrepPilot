import type { NutrientValues } from './dayPlans'

export type RecipeCategory = 'breakfast' | 'lunch' | 'dinner' | 'snack'

export type Recipe = {
  id: number
  title: string
  categories: RecipeCategory[]
  servings: number
  source_url: string | null
  preparation_minutes: number | null
  cooking_minutes: number | null
  nutrients: NutrientValues
  ingredients: string[]
  instructions: string[]
}

export type RecipeInput = {
  title: string
  categories: RecipeCategory[]
  servings: number
  calories_per_serving: number
  protein_per_serving: number
  carbs_per_serving: number
  fat_per_serving: number
  sugar_per_serving: number | null
  saturated_fat_per_serving: number | null
  fiber_per_serving: number | null
  salt_per_serving: number | null
  ingredients: string[]
  instructions: string[]
  preparation_minutes: number | null
  cooking_minutes: number | null
  source_url: string | null
}

export async function getRecipes(signal?: AbortSignal): Promise<Recipe[]> {
  const response = await fetch('/api/recipes', { signal })
  if (!response.ok) throw new Error('Rezeptbestand konnte nicht geladen werden.')
  return (await response.json()) as Recipe[]
}

export async function createRecipe(input: RecipeInput): Promise<Recipe> {
  return saveRecipe('/api/recipes', 'POST', input)
}

export async function updateRecipe(
  recipeId: number,
  input: RecipeInput,
): Promise<Recipe> {
  return saveRecipe(`/api/recipes/${recipeId}`, 'PUT', input)
}

export async function deleteRecipe(recipeId: number): Promise<void> {
  const response = await fetch(`/api/recipes/${recipeId}`, { method: 'DELETE' })
  if (!response.ok) throw new Error('Rezept konnte nicht gelöscht werden.')
}

async function saveRecipe(
  url: string,
  method: 'POST' | 'PUT',
  input: RecipeInput,
): Promise<Recipe> {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!response.ok) throw new Error('Rezept konnte nicht gespeichert werden.')
  return (await response.json()) as Recipe
}
