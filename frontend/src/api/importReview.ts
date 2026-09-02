export type ImportReviewSummary = {
  recipe_count: number
  open_identity_count: number
  review_ingredient_count: number
}

export type FoodConceptOption = {
  key: string
  name: string
  profile_count: number
}

export type OpenFoodIdentity = {
  id: number
  source_name: string
  external_id: string
  source_label: string | null
  source_url: string | null
  ingredient_count: number
  recipe_count: number
}

export type RecipeIngredientReview = {
  id: number
  raw_line: string
  status: string
  review_reason: string | null
  source_identifier_id: number | null
  source_label: string | null
  concept_key: string | null
  food_key: string | null
}

export type RecipeImportReview = {
  id: number
  title: string
  source_name: string
  external_id: string
  status: string
  ingredients: RecipeIngredientReview[]
}

export type ImportReviewOverview = {
  summary: ImportReviewSummary
  open_identities: OpenFoodIdentity[]
  concepts: FoodConceptOption[]
  recipes: RecipeImportReview[]
}

export async function getImportReview(
  signal?: AbortSignal,
): Promise<ImportReviewOverview> {
  const response = await fetch('/api/internal/import-review', { signal })
  if (!response.ok) {
    throw new Error('Importübersicht konnte nicht geladen werden.')
  }
  return (await response.json()) as ImportReviewOverview
}

export async function resolveFoodIdentity(
  identifierId: number,
  conceptKey: string,
): Promise<ImportReviewOverview> {
  const response = await fetch(
    `/api/internal/import-review/food-identities/${identifierId}/resolve`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ concept_key: conceptKey }),
    },
  )
  if (!response.ok) {
    throw new Error('Zutatenidentität konnte nicht zugeordnet werden.')
  }
  return (await response.json()) as ImportReviewOverview
}
