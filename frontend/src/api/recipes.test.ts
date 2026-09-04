import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  createRecipe,
  deleteRecipe,
  getRecipes,
  updateRecipe,
  type RecipeInput,
} from './recipes'

afterEach(() => vi.unstubAllGlobals())

const input: RecipeInput = {
  title: 'Kartoffel-Curry',
  categories: ['lunch', 'dinner'],
  servings: 4,
  calories_per_serving: 520,
  protein_per_serving: 32,
  carbs_per_serving: 61,
  fat_per_serving: 14,
  sugar_per_serving: null,
  saturated_fat_per_serving: null,
  fiber_per_serving: null,
  salt_per_serving: null,
  ingredients: ['800 g Kartoffeln'],
  instructions: ['Alles garen.'],
  preparation_minutes: 15,
  cooking_minutes: 30,
  source_url: null,
}

describe('recipe API', () => {
  it('loads the personal recipe inventory', async () => {
    const recipes = [{ id: 1, title: 'Kartoffel-Curry' }]
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(recipes), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(getRecipes()).resolves.toEqual(recipes)
    expect(fetchMock).toHaveBeenCalledWith('/api/recipes', { signal: undefined })
  })

  it('creates and updates recipes as JSON', async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(
      new Response(JSON.stringify({ id: 1, ...input }), { status: 200 }),
    ))
    vi.stubGlobal('fetch', fetchMock)

    await createRecipe(input)
    await updateRecipe(1, input)

    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/recipes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    })
    expect(fetchMock).toHaveBeenNthCalledWith(2, '/api/recipes/1', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    })
  })

  it('deletes a recipe', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetchMock)

    await deleteRecipe(7)

    expect(fetchMock).toHaveBeenCalledWith('/api/recipes/7', { method: 'DELETE' })
  })
})
