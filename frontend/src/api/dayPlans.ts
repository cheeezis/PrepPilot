import type { RecipeCategory } from './recipes'

export type DayPlanRequest = {
  calories: number
  protein_minimum: number
  fat_maximum: number
  carbs: number
  meal_categories: RecipeCategory[]
}

export type NutrientValues = {
  calories: number
  protein: number
  carbs: number
  fat: number
  sugar: number | null
  saturated_fat: number | null
  fiber: number | null
  salt: number | null
}

export type RuleEvaluation = {
  metric: 'calories' | 'protein' | 'fat' | 'carbs'
  kind: 'hard' | 'soft'
  actual: number
  target: number | null
  minimum: number | null
  maximum: number | null
  satisfied: boolean
}

export type PlannedRecipe = {
  id: number
  title: string
  category: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  portions: number
  recipe_servings: number
  source_url: string | null
  nutrients: NutrientValues
  ingredients: string[]
  instructions: string[]
}

export type DayPlan = {
  status: 'valid' | 'approximation'
  score: number
  nutrients: NutrientValues
  evaluations: RuleEvaluation[]
  recipes: PlannedRecipe[]
}

export type DayPlansResponse = {
  outcome: 'plans_found' | 'approximations_only' | 'no_usable_plan'
  plans: DayPlan[]
}

export async function createDayPlans(
  request: DayPlanRequest,
  signal?: AbortSignal,
): Promise<DayPlansResponse> {
  const response = await fetch('/api/day-plans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  })

  if (!response.ok) {
    throw new Error('Tagespläne konnten nicht erstellt werden.')
  }

  return (await response.json()) as DayPlansResponse
}
