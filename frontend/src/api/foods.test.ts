import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createFood,
  deleteFood,
  listFoods,
  type Food,
  type FoodInput,
  updateFood,
} from './foods'

const input: FoodInput = {
  name: 'Haferflocken',
  base_unit: 'g',
  calories_kcal: 372.5,
  protein_g: 13.5,
  carbohydrates_g: 58.7,
  fat_g: 7,
}

const food: Food = {
  id: 1,
  ...input,
  created_at: '2026-09-04T08:00:00Z',
  updated_at: '2026-09-04T08:00:00Z',
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('food API', () => {
  it('lists foods', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([food]))
    vi.stubGlobal('fetch', fetchMock)

    await expect(listFoods()).resolves.toEqual([food])
    expect(fetchMock).toHaveBeenCalledWith('/api/foods', { signal: undefined })
  })

  it('creates and updates foods', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(food, 201))
      .mockResolvedValueOnce(jsonResponse({ ...food, name: 'Haferdrink' }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(createFood(input)).resolves.toEqual(food)
    await expect(updateFood(1, { ...input, name: 'Haferdrink' })).resolves.toMatchObject(
      { name: 'Haferdrink' },
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/foods',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      '/api/foods/1',
      expect.objectContaining({ method: 'PUT' }),
    )
  })

  it('deletes foods', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(deleteFood(1)).resolves.toBeUndefined()
    expect(fetchMock).toHaveBeenCalledWith('/api/foods/1', { method: 'DELETE' })
  })

  it('uses the API error detail', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse({ detail: 'Lebensmittel bereits vorhanden' }, 409),
      ),
    )

    await expect(createFood(input)).rejects.toThrow(
      'Lebensmittel bereits vorhanden',
    )
  })
})

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}
