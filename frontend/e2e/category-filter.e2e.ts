import { expect, test } from '@playwright/test'

const recipe = (id: number, title: string, categories: Array<'breakfast' | 'lunch' | 'dinner' | 'snack'>) => ({
  id,
  title,
  categories,
  servings: 2,
  source_url: `https://www.nhs.uk/healthier-families/recipes/${title.toLowerCase()}/`,
  license_name: 'Open Government Licence v3.0',
  attribution_text: 'Quelle: NHS',
  nutrients: {
    calories: 400,
    protein: 20,
    carbs: 50,
    fat: 12,
    sugar: 8,
    saturated_fat: 3,
    fiber: 6,
    salt: 1,
  },
  ingredients: ['1 test ingredient'],
  instructions: ['Test instruction.'],
})

test('filters stored recipes by their official NHS category', async ({ page }) => {
  await page.route('**/api/health', async (route) => {
    await route.fulfill({ json: { status: 'ok' } })
  })
  await page.route('**/api/recipes', async (route) => {
    await route.fulfill({
      json: [
        recipe(1, 'Scrambled eggs', ['breakfast', 'lunch']),
        recipe(2, 'Full English breakfast', ['breakfast']),
        recipe(3, 'Falafels', ['lunch']),
        recipe(4, 'Pasta carbonara', ['dinner']),
        recipe(5, 'Forest fruit milkshake', ['snack']),
      ],
    })
  })

  await page.goto('/recipes')

  const recipes = page.locator('.recipe-card')
  await expect(recipes).toHaveCount(5)
  await page.getByRole('button', { name: 'Frühstück 2' }).click()
  await expect(recipes).toHaveCount(2)
  await page.getByRole('button', { name: 'Mittagessen 2' }).click()
  await expect(recipes).toHaveCount(2)
  await page.getByRole('button', { name: 'Abendessen 1' }).click()
  await expect(recipes).toHaveCount(1)
  await expect(recipes.first()).toContainText('Pasta carbonara')
  await page.getByRole('button', { name: 'Snack 1' }).click()
  await expect(recipes).toHaveCount(1)
  await expect(recipes.first()).toContainText('Forest fruit milkshake')
  await page.getByRole('button', { name: 'Alle 5' }).click()
  await page.getByRole('searchbox', { name: 'Rezepte durchsuchen' }).fill('falafel')
  await expect(recipes).toHaveCount(1)
  await expect(recipes.first()).toContainText('Falafels')

  await page.getByRole('link', { name: 'Planer' }).click()
  await expect(page).toHaveURL(/\/$/)
  await expect(
    page.getByRole('heading', { name: 'Ein Tagesplan, der zu deinen Zielen passt.' }),
  ).toBeVisible()
})
