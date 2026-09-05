import type { MealRole } from './recipes'
import type { BaseUnit, FoodCategory } from './foods'

export type MealAssignment = {
  id: number
  date: string
  day_index: number
  meal_role: MealRole
  slot_number: number
  recipe_id: number
  recipe_title: string
  portion_number: number | null
  recipe_servings: number
}

export type DailyNutrition = {
  date: string
  day_index: number
  calories_kcal: number
  protein_g: number
  carbohydrates_g: number
  fat_g: number
  calories_over_kcal: number
  protein_shortfall_g: number
  carbohydrates_difference_g: number
  fat_over_g: number
}

export type ShoppingListItem = {
  food_id: number
  food_name: string
  category: FoodCategory
  amount: number
  unit: BaseUnit
  equivalent_amount: number | null
  equivalent_unit: string | null
}

export type MealReplacementSuggestion = {
  recipe_id: number
  recipe_title: string
  daily_nutrition: DailyNutrition
}

export type WeeklyPlan = {
  id: number
  start_date: string
  end_date: string
  snacks_per_day: number
  calories_maximum_kcal: number
  protein_minimum_g: number
  carbohydrates_target_g: number
  fat_maximum_g: number
  assignments: MealAssignment[]
  daily_nutrition: DailyNutrition[]
  created_at: string
  updated_at: string
}

export type WeeklyPlanInput = Pick<WeeklyPlan, 'start_date' | 'snacks_per_day' | 'calories_maximum_kcal' | 'protein_minimum_g' | 'carbohydrates_target_g' | 'fat_maximum_g'> & { replace_existing: boolean }

export class WeeklyPlanApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export function listWeeklyPlans(signal?: AbortSignal): Promise<WeeklyPlan[]> {
  return request('/api/weekly-plans', { signal })
}

export function generateWeeklyPlan(input: WeeklyPlanInput): Promise<WeeklyPlan> {
  return request('/api/weekly-plans/generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(input) })
}

export function getShoppingList(planId: number): Promise<ShoppingListItem[]> {
  return request(`/api/weekly-plans/${planId}/shopping-list`)
}

export function getMealReplacements(planId: number, assignmentId: number): Promise<MealReplacementSuggestion[]> {
  return request(`/api/weekly-plans/${planId}/assignments/${assignmentId}/replacements`)
}

export function replaceMeal(planId: number, assignmentId: number, recipeId: number): Promise<WeeklyPlan> {
  return request(`/api/weekly-plans/${planId}/assignments/${assignmentId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ recipe_id: recipeId }) })
}

export async function deleteWeeklyPlan(id: number): Promise<void> {
  await request(`/api/weekly-plans/${id}`, { method: 'DELETE' })
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    throw new WeeklyPlanApiError(body?.detail ?? 'Wochenplanung nicht verfügbar', response.status)
  }
  if (response.status === 204) return undefined as T
  return await response.json() as T
}
