import { expect, test } from '@playwright/test'

let catalogSize = 0

test.beforeAll(async ({ request }, testInfo) => {
  testInfo.setTimeout(120_000)
  const response = await request.post('/api/imports/nhs', { timeout: 120_000 })
  expect(response.ok()).toBeTruthy()
  const recipesResponse = await request.get('/api/recipes')
  expect(recipesResponse.ok()).toBeTruthy()
  catalogSize = (await recipesResponse.json() as unknown[]).length
  expect(catalogSize).toBeGreaterThan(100)
})

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('System bereit')).toBeVisible()
})

test('shows the stored recipe inventory', async ({ page }) => {
  await page.getByRole('link', { name: 'Rezepte' }).click()
  await expect(page).toHaveURL(/\/recipes$/)
  await expect(page.getByRole('heading', { name: 'Gespeicherte Rezepte' })).toBeVisible()
  await expect(page.getByText(`${catalogSize} Rezepte`)).toBeVisible()
  const recipes = page.locator('.recipe-card')
  await expect(recipes).toHaveCount(catalogSize)
  await expect(recipes.first()).toContainText('525 kcal pro Portion · ergibt 6 Portionen')
  await recipes.first().locator('summary').click()
  await expect(
    recipes.first().getByRole('heading', { name: 'Zutaten für 6 Portionen' }),
  ).toBeVisible()
  await expect(recipes.first().getByText('Ballaststoffe')).toBeVisible()
  await expect(recipes.first().getByRole('heading', { name: 'Zubereitung' })).toBeVisible()
  await expect(
    recipes.first().getByRole('link', { name: 'Originalrezept beim NHS' }),
  ).toBeVisible()
})

test('creates and selects a valid day plan', async ({ page }) => {
  await page.getByRole('button', { name: 'Tagespläne erstellen' }).click()

  await expect(page.getByRole('heading', { name: '3 Tagespläne' })).toBeVisible()
  const plans = page.getByRole('article')
  await expect(plans).toHaveCount(3)
  await expect(plans.first().getByText(/Ziel 2\.000 kcal/)).toBeVisible()

  const secondPlan = plans.nth(1)
  await secondPlan.getByRole('button', { name: 'Diesen Plan auswählen' }).click()

  await expect(page.getByText('Vorschlag 2 ausgewählt')).toBeVisible()
  await expect(secondPlan.getByText(/Portion/).first()).toBeVisible()
  await secondPlan.locator('details').first().locator('summary').click()
  await expect(
    secondPlan.getByText(/PrepPilot rechnet sie noch nicht/).first(),
  ).toBeVisible()
  await expect(
    secondPlan.getByRole('link', { name: 'Originalrezept beim NHS' }).first(),
  ).toBeVisible()
  await expect(
    secondPlan.getByRole('button', { name: 'Ausgewählt' }),
  ).toHaveAttribute('aria-pressed', 'true')
})

test('adds a snack when it is selected', async ({ page }) => {
  await page.getByRole('checkbox', { name: 'Snack' }).check()
  await page.getByRole('button', { name: 'Tagespläne erstellen' }).click()

  await expect(page.getByRole('heading', { name: '3 Tagespläne' })).toBeVisible({
    timeout: 30_000,
  })
  const firstPlan = page.getByRole('article').first()
  await expect(firstPlan.getByText(/Snack ·/)).toBeVisible()
  await expect(firstPlan.locator('.meal')).toHaveCount(4)
})

test('creates a meal-prep plan for consecutive days', async ({ page }) => {
  await page.getByRole('radio', { name: 'Mehrere Tage' }).check()
  await page.getByLabel('Anzahl der Tage').selectOption('3')
  await page.getByRole('button', { name: 'Wochenplan erstellen' }).click()

  await expect(page.getByRole('heading', { name: '3-Tage-Plan' })).toBeVisible({
    timeout: 30_000,
  })
  const days = page.getByRole('article')
  await expect(days).toHaveCount(3)
  await expect(days.nth(1).getByText('Gemeinsam mit Tag 1 vorbereiten')).toBeVisible()
  await expect(days.nth(2).getByText('Gemeinsam mit Tag 2 vorbereiten')).toHaveCount(0)
})

test('explains hard and soft deviations for approximations', async ({ page }) => {
  await page.getByRole('spinbutton', { name: 'Kalorien kcal' }).fill('1800')
  await page.getByRole('spinbutton', { name: 'Protein mindestens g' }).fill('200')
  await page.getByRole('button', { name: 'Tagespläne erstellen' }).click()

  await expect(
    page.getByText('Kein Plan trifft alle harten Ziele. Die besten Annäherungen:'),
  ).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Annäherung' })).toHaveCount(3)
  await expect(page.getByText('Außerhalb').first()).toBeVisible()
  await expect(page.getByText('Weiche Abweichung').first()).toBeVisible()
  await expect(
    page.getByText(/unter dem (Mindestwert|Zielbereich)/).first(),
  ).toBeVisible()

  await page
    .getByRole('article')
    .first()
    .getByRole('button', { name: 'Diesen Plan auswählen' })
    .click()
  await expect(page.getByText('Vorschlag 1 ausgewählt')).toBeVisible()
})
