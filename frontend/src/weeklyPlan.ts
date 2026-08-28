import type { PlannedMeal } from './api/dayPlans'

export const weekDays = [
  'Montag',
  'Dienstag',
  'Mittwoch',
  'Donnerstag',
  'Freitag',
  'Samstag',
  'Sonntag',
] as const

export type ShoppingListItem = {
  foodKey: string
  name: string
  amount: number
  unit: 'g' | 'ml'
}

export function buildShoppingList(
  meals: PlannedMeal[],
  dayCount: number = weekDays.length,
): ShoppingListItem[] {
  const totals = new Map<string, ShoppingListItem>()

  for (const meal of meals) {
    for (const ingredient of meal.ingredients) {
      const aggregateKey = `${ingredient.food_key}:${ingredient.unit}`
      const existing = totals.get(aggregateKey)
      const amount = ingredient.amount * dayCount

      if (existing) {
        existing.amount += amount
      } else {
        totals.set(aggregateKey, {
          foodKey: ingredient.food_key,
          name: ingredient.name,
          amount,
          unit: ingredient.unit,
        })
      }
    }
  }

  return [...totals.values()].sort((left, right) =>
    left.name.localeCompare(right.name, 'de'),
  )
}
