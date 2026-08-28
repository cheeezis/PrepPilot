export type DayPlanRequest = {
  calories: number
  protein_minimum: number
  fat_maximum: number
  carbs: number
  meal_count: number
}

export type NutrientValues = {
  calories: number
  protein: number
  carbs: number
  fat: number
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

export type PlannedIngredient = {
  food_key: string
  name: string
  amount: number
  unit: 'g' | 'ml'
}

export type PlannedMeal = {
  key: string
  name: string
  role: string
  portion_factor: number
  nutrients: NutrientValues
  ingredients: PlannedIngredient[]
}

export type DayPlan = {
  status: 'valid' | 'approximation'
  score: number
  nutrients: NutrientValues
  evaluations: RuleEvaluation[]
  meals: PlannedMeal[]
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
