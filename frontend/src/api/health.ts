export type HealthResponse = {
  status: 'ok' | 'error'
  database: 'ok' | 'unavailable'
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch('/api/health', { signal })
  const health = (await response.json()) as HealthResponse

  if (!response.ok) {
    throw new Error(`Systemcheck fehlgeschlagen: ${health.database}`)
  }

  return health
}
