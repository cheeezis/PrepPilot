import { expect, test, type APIRequestContext } from '@playwright/test'

const createdRecipeIds: number[] = []

function recipe(category: 'breakfast' | 'lunch' | 'dinner' | 'snack') {
  const nutrients = {
    breakfast: { calories: 550, protein: 30, carbs: 60, fat: 15 },
    lunch: { calories: 650, protein: 40, carbs: 75, fat: 20 },
    dinner: { calories: 800, protein: 50, carbs: 85, fat: 30 },
    snack: { calories: 200, protein: 10, carbs: 20, fat: 5 },
  }[category]
  return {
    title: `E2E ${category} recipe`,
    categories: [category],
    servings: 4,
    calories_per_serving: nutrients.calories,
    protein_per_serving: nutrients.protein,
    carbs_per_serving: nutrients.carbs,
    fat_per_serving: nutrients.fat,
    ingredients: [{ amount: 1, unit: 'Stück', name: 'Testzutat' }],
    instructions: ['Test instruction.'],
    preparation_minutes: 10,
    cooking_minutes: 20,
    source_url: null,
  }
}

async function createTestRecipe(
  request: APIRequestContext,
  category: 'breakfast' | 'lunch' | 'dinner' | 'snack',
) {
  const response = await request.post('/api/recipes', { data: recipe(category) })
  expect(response.ok()).toBeTruthy()
  createdRecipeIds.push((await response.json()).id as number)
}

test.beforeAll(async ({ request }) => {
  for (const category of ['breakfast', 'lunch', 'dinner', 'snack'] as const) {
    await createTestRecipe(request, category)
  }
})

test.afterAll(async ({ request }) => {
  for (const recipeId of createdRecipeIds) {
    await request.delete(`/api/recipes/${recipeId}`)
  }
})

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('System bereit')).toBeVisible()
})

test('shows the personal recipe inventory', async ({ page }) => {
  await page.getByRole('link', { name: 'Rezepte' }).click()
  await expect(page).toHaveURL(/\/recipes$/)
  await expect(
    page.getByRole('heading', { name: 'Meine gespeicherten Rezepte' }),
  ).toBeVisible()
  await expect(
    page.locator('.recipe-card').filter({ hasText: 'E2E breakfast recipe' }),
  ).toHaveCount(1)
})

test('creates and selects a valid day plan', async ({ page }) => {
  await page.getByRole('button', { name: 'Tagespläne erstellen' }).click()

  await expect(page.getByRole('heading', { name: /Tagespläne/ })).toBeVisible()
  const plans = page.getByRole('article')
  await expect(plans.first()).toContainText(/Ziel 2\.000 kcal/)
  await expect(plans.first().getByText('1 Portion eingeplant')).toHaveCount(3)
  await plans.first().getByRole('button', { name: 'Diesen Plan auswählen' }).click()
  await expect(page.getByText('Vorschlag 1 ausgewählt')).toBeVisible()
})

test('adds a snack when it is selected', async ({ page }) => {
  await page.getByRole('checkbox', { name: 'Snack' }).check()
  await page.getByRole('button', { name: 'Tagespläne erstellen' }).click()

  const firstPlan = page.getByRole('article').first()
  await expect(firstPlan.getByText(/Snack ·/)).toBeVisible()
  await expect(firstPlan.locator('.meal')).toHaveCount(4)
})

test('explains hard and soft deviations for approximations', async ({ page }) => {
  await page.getByRole('spinbutton', { name: 'Protein mindestens g' }).fill('125')
  await page.getByRole('button', { name: 'Tagespläne erstellen' }).click()

  await expect(
    page.getByText('Kein Plan trifft alle harten Ziele. Die besten Annäherungen:'),
  ).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Annäherung' }).first()).toBeVisible()
  await expect(page.getByText('Außerhalb').first()).toBeVisible()
})
