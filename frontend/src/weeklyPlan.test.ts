import { describe, expect, it } from 'vitest'
import type { PlannedMeal } from './api/dayPlans'
import { buildShoppingList } from './weeklyPlan'

const nutrients = { calories: 0, protein: 0, carbs: 0, fat: 0 }

const meals: PlannedMeal[] = [
  {
    key: 'breakfast',
    name: 'Frühstück',
    role: 'first_meal',
    portion_factor: 1,
    nutrients,
    ingredients: [
      { food_key: 'oats', name: 'Haferflocken', amount: 50, unit: 'g' },
      { food_key: 'milk', name: 'Milch', amount: 200, unit: 'ml' },
    ],
  },
  {
    key: 'snack',
    name: 'Snack',
    role: 'protein_snack',
    portion_factor: 1,
    nutrients,
    ingredients: [
      { food_key: 'oats', name: 'Haferflocken', amount: 20, unit: 'g' },
      { food_key: 'banana', name: 'Banane', amount: 100, unit: 'g' },
    ],
  },
]

describe('buildShoppingList', () => {
  it('aggregates ingredients across meals and seven equal days', () => {
    expect(buildShoppingList(meals)).toEqual([
      { foodKey: 'banana', name: 'Banane', amount: 700, unit: 'g' },
      { foodKey: 'oats', name: 'Haferflocken', amount: 490, unit: 'g' },
      { foodKey: 'milk', name: 'Milch', amount: 1400, unit: 'ml' },
    ])
  })

  it('can calculate a different number of equal days', () => {
    expect(buildShoppingList(meals, 2)).toEqual([
      { foodKey: 'banana', name: 'Banane', amount: 200, unit: 'g' },
      { foodKey: 'oats', name: 'Haferflocken', amount: 140, unit: 'g' },
      { foodKey: 'milk', name: 'Milch', amount: 400, unit: 'ml' },
    ])
  })
})
