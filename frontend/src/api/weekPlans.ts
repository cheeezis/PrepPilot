import type { DayPlan, DayPlanRequest } from './dayPlans'

export type WeekPlanRequest = DayPlanRequest & {
  days: number
}

export type WeekPlanDay = {
  day: number
  block_start_day: number
  block_end_day: number
  prep_with_previous: boolean
  plan: DayPlan
}

export type WeekPlanResponse = {
  outcome: 'plan_found' | 'approximation' | 'no_usable_plan'
  days: WeekPlanDay[]
}

export async function createWeekPlan(
  request: WeekPlanRequest,
  signal?: AbortSignal,
): Promise<WeekPlanResponse> {
  const response = await fetch('/api/week-plans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  })

  if (!response.ok) {
    throw new Error('Wochenplan konnte nicht erstellt werden.')
  }

  return (await response.json()) as WeekPlanResponse
}
