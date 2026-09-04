import { expect, test, type APIRequestContext } from '@playwright/test'

const createdRecipeIds: number[] = []

function recipe(category: 'breakfast' | 'lunch' | 'dinner' | 'snack') {
  return {
    title: `E2E ${category} recipe`,
    categories: [category],
    servings: 4,
    calories_per_serving: category === 'snack' ? 250 : 500,
    protein_per_serving: category === 'snack' ? 15 : 30,
    carbs_per_serving: category === 'snack' ? 25 : 55,
    fat_per_serving: category === 'snack' ? 7 : 15,
    ingredients: ['1 test ingredient'],
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
