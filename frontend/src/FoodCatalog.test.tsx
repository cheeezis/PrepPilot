import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'
import { FoodCategoryList } from './FoodCatalog'
import type { Food } from './api/foods'

const foods: Food[] = [
  {
    id: 1,
    name: 'Hähnchenbrust',
    base_unit: 'g',
    category: 'protein',
    calories_kcal: 102,
    protein_g: 23.56,
    carbohydrates_g: 0,
    fat_g: 0.68,
    portions: [{ id: 1, name: 'Portion', amount: 250 }],
    created_at: '2026-09-04T08:00:00Z',
    updated_at: '2026-09-04T08:00:00Z',
  },
  {
    id: 2,
    name: 'Naturreis',
    base_unit: 'g',
    category: 'carbohydrate',
    calories_kcal: 360,
    protein_g: 9.1,
    carbohydrates_g: 69,
    fat_g: 2.5,
    portions: [],
    created_at: '2026-09-04T08:00:00Z',
    updated_at: '2026-09-04T08:00:00Z',
  },
]

describe('FoodCategoryList', () => {
  it('renders foods in collapsed category groups with counts', () => {
    const html = renderToStaticMarkup(
      <FoodCategoryList foods={foods} onEdit={vi.fn()} onDelete={vi.fn()} onSavePortion={vi.fn()} onDeletePortion={vi.fn()} />,
    )

    expect(html).toContain('<details class="food-category-group">')
    expect(html).toContain('Proteinquellen')
    expect(html).toContain('Getreide &amp; Stärke')
    expect(html).toContain('Hähnchenbrust')
    expect(html).toContain('1 Portion = 250 g')
    expect(html).not.toContain('<details class="food-category-group" open="">')
  })
})
