import { afterEach, describe, expect, it, vi } from 'vitest'
import { getImportReview, resolveFoodIdentity } from './importReview'

afterEach(() => {
  vi.unstubAllGlobals()
})

const overview = {
  summary: {
    recipe_count: 2,
    open_identity_count: 1,
    review_ingredient_count: 2,
  },
  open_identities: [],
  concepts: [],
  recipes: [],
}

describe('import review API', () => {
  it('loads the internal import overview', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(overview), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(getImportReview()).resolves.toEqual(overview)
    expect(fetchMock).toHaveBeenCalledWith('/api/internal/import-review', {
      signal: undefined,
    })
  })

  it('resolves a source identity to one concept', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(overview), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await resolveFoodIdentity(12, 'tomato')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/internal/import-review/food-identities/12/resolve',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ concept_key: 'tomato' }),
      },
    )
  })
})
