import { afterEach, describe, expect, it, vi } from 'vitest'
import { getRecipes } from './recipes'

afterEach(() => vi.unstubAllGlobals())

describe('getRecipes', () => {
  it('loads the stored recipe inventory', async () => {
    const recipes = [{ id: 1, title: 'Roast chicken dinner recipe' }]
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(recipes), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(getRecipes()).resolves.toEqual(recipes)
    expect(fetchMock).toHaveBeenCalledWith('/api/recipes', { signal: undefined })
  })
})
