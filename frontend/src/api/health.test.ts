import { afterEach, describe, expect, it, vi } from 'vitest'
import { getHealth } from './health'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('getHealth', () => {
  it('returns the system status for a successful response', async () => {
    const health = { status: 'ok', database: 'ok', recipes: 'empty' }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(health), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(getHealth()).resolves.toEqual(health)
    expect(fetchMock).toHaveBeenCalledWith('/api/health', {
      signal: undefined,
    })
  })

  it('throws for an unsuccessful response', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          status: 'error',
          database: 'unavailable',
          recipes: 'unavailable',
        }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(getHealth()).rejects.toThrow(
      'Systemcheck fehlgeschlagen: unavailable',
    )
  })
})
