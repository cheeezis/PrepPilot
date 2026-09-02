import { afterEach, describe, expect, it, vi } from 'vitest'
import { importNhsRecipes } from './imports'

afterEach(() => vi.unstubAllGlobals())

describe('importNhsRecipes', () => {
  it('starts the bounded NHS import', async () => {
    const result = { created: 10, updated: 0, unchanged: 0, rejected: 0, items: [] }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(result), { status: 200 }),
    )
    vi.stubGlobal('fetch', fetchMock)
    await expect(importNhsRecipes()).resolves.toEqual(result)
    expect(fetchMock).toHaveBeenCalledWith('/api/imports/nhs', { method: 'POST' })
  })
})
