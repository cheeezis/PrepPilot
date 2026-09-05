import { afterEach, describe, expect, it, vi } from 'vitest'
import { generateWeeklyPlan, getMealReplacements, getShoppingList, listWeeklyPlans, replaceMeal, WeeklyPlanApiError } from './weeklyPlans'

afterEach(() => vi.unstubAllGlobals())

describe('weekly plan api', () => {
  it('lists persisted plans', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('[]'))
    vi.stubGlobal('fetch', fetchMock)
    await expect(listWeeklyPlans()).resolves.toEqual([])
    expect(fetchMock).toHaveBeenCalledWith('/api/weekly-plans', { signal: undefined })
  })

  it('generates a plan with the selected targets', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: 1 })))
    vi.stubGlobal('fetch', fetchMock)
    await generateWeeklyPlan({ start_date: '2026-09-07', snacks_per_day: 1, calories_maximum_kcal: 2500, protein_minimum_g: 180, carbohydrates_target_g: 250, fat_maximum_g: 80, replace_existing: false })
    expect(fetchMock).toHaveBeenCalledWith('/api/weekly-plans/generate', expect.objectContaining({ method: 'POST' }))
  })

  it('loads the shopping list for a plan', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('[]'))
    vi.stubGlobal('fetch', fetchMock)
    await expect(getShoppingList(7)).resolves.toEqual([])
    expect(fetchMock).toHaveBeenCalledWith('/api/weekly-plans/7/shopping-list', undefined)
  })

  it('loads and applies meal replacements', async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(new Response('[]')))
    vi.stubGlobal('fetch', fetchMock)

    await expect(getMealReplacements(7, 12)).resolves.toEqual([])
    await replaceMeal(7, 12, 4)

    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/weekly-plans/7/assignments/12/replacements', undefined)
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/weekly-plans/7/assignments/12', expect.objectContaining({ method: 'PATCH', body: '{"recipe_id":4}' }))
  })

  it('preserves conflict status and detail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Plan existiert' }), { status: 409 })))
    await expect(listWeeklyPlans()).rejects.toEqual(new WeeklyPlanApiError('Plan existiert', 409))
  })
})
