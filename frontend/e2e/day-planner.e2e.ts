import { expect, test } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: '10 NHS-Rezepte importieren' }).click()
  await expect(page.getByRole('status')).toContainText(/neu|unverändert/)
  await expect(page.getByText('System bereit')).toBeVisible()
})

test('shows the stored recipe inventory', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'Gespeicherte Rezepte' })).toBeVisible()
  await expect(page.getByText('10 Rezepte')).toBeVisible()
  const recipes = page.locator('.recipe-card')
  await expect(recipes).toHaveCount(10)
  await expect(recipes.first()).toContainText('525 kcal pro Portion · ergibt 6 Portionen')
  await recipes.first().locator('summary').click()
  await expect(
    recipes.first().getByRole('heading', { name: 'Zutaten für 6 Portionen' }),
  ).toBeVisible()
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
  await expect(plans.first().getByText(/Ziel 2\.500 kcal/)).toBeVisible()

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

test('explains hard and soft deviations for approximations', async ({ page }) => {
  await page.getByRole('spinbutton', { name: 'Kalorien kcal' }).fill('1800')
  await page.getByRole('spinbutton', { name: 'Protein mindestens g' }).fill('160')
  await page.getByRole('combobox', { name: 'Mahlzeiten' }).selectOption('3')
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
