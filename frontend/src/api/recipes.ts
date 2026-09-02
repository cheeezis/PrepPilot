import type { NutrientValues } from './dayPlans'

export type Recipe = {
  id: number
  title: string
  servings: number
  source_url: string
  license_name: string
  attribution_text: string
  nutrients: NutrientValues
  ingredients: string[]
  instructions: string[]
}

export async function getRecipes(signal?: AbortSignal): Promise<Recipe[]> {
  const response = await fetch('/api/recipes', { signal })
  if (!response.ok) throw new Error('Rezeptbestand konnte nicht geladen werden.')
  return (await response.json()) as Recipe[]
}
