import type { MealRole } from './recipes'

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

export type WeeklyPlan = {
  id: number
  start_date: string
  end_date: string
  snacks_per_day: number
  calories_target_kcal: number
  protein_minimum_g: number
  carbohydrates_target_g: number
  fat_maximum_g: number
  assignments: MealAssignment[]
  created_at: string
  updated_at: string
}

export type WeeklyPlanInput = Pick<WeeklyPlan, 'start_date' | 'snacks_per_day' | 'calories_target_kcal' | 'protein_minimum_g' | 'carbohydrates_target_g' | 'fat_maximum_g'> & { replace_existing: boolean }

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
