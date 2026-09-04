import type { FoodCategory } from './api/foods'

export const foodCategories: Array<{ value: FoodCategory; label: string }> = [
  { value: 'protein', label: 'Proteinquellen' },
  { value: 'carbohydrate', label: 'Getreide & Stärke' },
  { value: 'vegetable', label: 'Gemüse & Hülsenfrüchte' },
  { value: 'fruit', label: 'Obst' },
  { value: 'dairy', label: 'Milchprodukte' },
  { value: 'fat', label: 'Fette & Öle' },
  { value: 'sauce', label: 'Saucen & Würzmittel' },
  { value: 'spice', label: 'Gewürze & Kräuter' },
  { value: 'other', label: 'Sonstiges' },
]

export function foodCategoryLabel(category: FoodCategory): string {
  return foodCategories.find((item) => item.value === category)?.label ?? category
}
