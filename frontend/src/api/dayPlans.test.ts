import { afterEach, describe, expect, it, vi } from 'vitest'
import { createDayPlans } from './dayPlans'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('createDayPlans', () => {
  it('posts the requested targets', async () => {
    const result = { outcome: 'no_usable_plan', plans: [] }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(result), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const request = {
      calories: 2500,
      protein_minimum: 220,
      fat_maximum: 71,
      carbs: 233,
    }

    await expect(createDayPlans(request)).resolves.toEqual(result)
    expect(fetchMock).toHaveBeenCalledWith('/api/day-plans', {
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

    await expect(
      createDayPlans({
        calories: 0,
        protein_minimum: 220,
        fat_maximum: 71,
        carbs: 233,
      }),
    ).rejects.toThrow('Tagespläne konnten nicht erstellt werden.')
  })
})
