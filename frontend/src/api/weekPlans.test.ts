import { afterEach, describe, expect, it, vi } from 'vitest'
import { createWeekPlan, type WeekPlanRequest } from './weekPlans'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('createWeekPlan', () => {
  it('posts targets, meals and the requested number of days', async () => {
    const result = { outcome: 'no_usable_plan', days: [] }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(result), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const request: WeekPlanRequest = {
      days: 5,
      calories: 2000,
      protein_minimum: 120,
      fat_maximum: 70,
      carbs: 220,
      meal_categories: ['breakfast', 'lunch', 'dinner'],
    }

    await expect(createWeekPlan(request)).resolves.toEqual(result)
    expect(fetchMock).toHaveBeenCalledWith('/api/week-plans', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: undefined,
    })
  })

  it('throws for an unsuccessful response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('{}', { status: 422 })),
    )

    await expect(createWeekPlan({
      days: 2,
      calories: 2000,
      protein_minimum: 120,
      fat_maximum: 70,
      carbs: 220,
      meal_categories: ['breakfast'],
    })).rejects.toThrow('Wochenplan konnte nicht erstellt werden.')
  })
})
