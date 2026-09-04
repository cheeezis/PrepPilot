import type { BaseUnit } from './foods'

export type MealRole = 'breakfast' | 'lunch' | 'dinner' | 'snack'

export type Nutrients = {
  calories_kcal: number
  protein_g: number
  carbohydrates_g: number
  fat_g: number
}

export type RecipeIngredient = {
  food_id: number
  food_name: string
  amount: number
  unit: BaseUnit
  position: number
}

export type Recipe = {
  id: number
  title: string
  servings: number
  is_meal_prep: boolean
  meal_roles: MealRole[]
  ingredients: RecipeIngredient[]
  instructions: string[]
  nutrition_total: Nutrients
  nutrition_per_serving: Nutrients
  created_at: string
  updated_at: string
}

export type RecipeInput = {
  title: string
  servings: number
  meal_roles: MealRole[]
  ingredients: Array<{ food_id: number; amount: number }>
  instructions: string[]
}

export function listRecipes(signal?: AbortSignal): Promise<Recipe[]> {
  return request<Recipe[]>('/api/recipes', { signal })
}

export function createRecipe(input: RecipeInput): Promise<Recipe> {
  return request<Recipe>('/api/recipes', writeRequest('POST', input))
}

export function updateRecipe(id: number, input: RecipeInput): Promise<Recipe> {
  return request<Recipe>(`/api/recipes/${id}`, writeRequest('PUT', input))
}

export async function deleteRecipe(id: number): Promise<void> {
  await request<void>(`/api/recipes/${id}`, { method: 'DELETE' })
}

function writeRequest(method: 'POST' | 'PUT', input: RecipeInput): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(body?.detail ?? 'Rezeptverwaltung nicht verfügbar')
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
