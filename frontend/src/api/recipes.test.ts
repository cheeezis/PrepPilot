import { afterEach, describe, expect, it, vi } from 'vitest'
import { createRecipe, deleteRecipe, listRecipes, updateRecipe } from './recipes'

const input = {
  title: 'Porridge',
  servings: 2,
  meal_roles: ['breakfast'] as const,
  ingredients: [{ food_id: 3, amount: 100, food_portion_id: null }],
  instructions: ['Kochen.'],
}

afterEach(() => vi.unstubAllGlobals())

describe('recipe api', () => {
  it('lists recipes', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('[]'))
    vi.stubGlobal('fetch', fetchMock)
    await expect(listRecipes()).resolves.toEqual([])
    expect(fetchMock).toHaveBeenCalledWith('/api/recipes', { signal: undefined })
  })

  it('creates and updates recipes with JSON requests', async () => {
    const response = { ...input, id: 1 }
    const fetchMock = vi.fn().mockImplementation(
      () => Promise.resolve(new Response(JSON.stringify(response))),
    )
    vi.stubGlobal('fetch', fetchMock)

    await createRecipe({ ...input, meal_roles: [...input.meal_roles] })
    await updateRecipe(1, { ...input, meal_roles: [...input.meal_roles] })

    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/recipes', expect.objectContaining({ method: 'POST' }))
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/recipes/1', expect.objectContaining({ method: 'PUT' }))
  })

  it('deletes recipes', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)
    await deleteRecipe(4)
    expect(fetchMock).toHaveBeenCalledWith('/api/recipes/4', { method: 'DELETE' })
  })

  it('uses the API detail for errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(
      JSON.stringify({ detail: 'Unbekannte Lebensmittel-ID: 9' }),
      { status: 422 },
    )))
    await expect(createRecipe({ ...input, meal_roles: [...input.meal_roles] })).rejects.toThrow('Unbekannte Lebensmittel-ID: 9')
  })
})
