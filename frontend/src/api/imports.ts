export type ImportItem = {
  source_url: string
  status: 'created' | 'updated' | 'unchanged' | 'rejected'
  title: string | null
  reason: string | null
}

export type ImportRun = {
  created: number
  updated: number
  unchanged: number
  rejected: number
  items: ImportItem[]
}

export async function importNhsRecipes(): Promise<ImportRun> {
  const response = await fetch('/api/imports/nhs', { method: 'POST' })
  if (!response.ok) throw new Error('Rezeptimport fehlgeschlagen.')
  return (await response.json()) as ImportRun
}
