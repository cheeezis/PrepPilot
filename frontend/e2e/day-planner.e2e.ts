import { expect, test } from '@playwright/test'

test('creates and selects a valid day plan', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByText('System bereit')).toBeVisible()
  await page.getByRole('button', { name: 'Tagespläne erstellen' }).click()

  await expect(page.getByRole('heading', { name: '3 Tagespläne' })).toBeVisible()
  const plans = page.getByRole('article')
  await expect(plans).toHaveCount(3)
  await expect(plans.first().getByText(/Ziel 2\.500 kcal/)).toBeVisible()

  const secondPlan = plans.nth(1)
  await secondPlan.getByRole('button', { name: 'Diesen Plan auswählen' }).click()

  await expect(page.getByRole('status')).toContainText('Vorschlag 2 ausgewählt')
  await expect(page.getByRole('heading', { name: 'Deine Woche' })).toBeVisible()
  await expect(page.getByTestId('week-day')).toHaveCount(7)
  await expect(page.getByRole('heading', { name: 'Einkaufsliste' })).toBeVisible()
  await expect(page.getByText('Gesamtmengen für sieben Tage.')).toBeVisible()
  await expect(
    secondPlan.getByRole('button', { name: 'Ausgewählt' }),
  ).toHaveAttribute('aria-pressed', 'true')
})

test('explains hard and soft deviations for approximations', async ({ page }) => {
  await page.goto('/')

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
  await expect(page.getByRole('status')).toContainText('Vorschlag 1 ausgewählt')
})

test('opens the internal import review with the current database state', async ({
  page,
}) => {
  await page.goto('/')

  await page.getByRole('button', { name: 'Importprüfung' }).click()

  await expect(
    page.getByRole('heading', { name: 'Importprüfung' }),
  ).toBeVisible()
  await expect(page.getByLabel('Importstatus')).toContainText('Rezepte')
  await expect(
    page.getByRole('heading', { name: 'Offene Zutatenidentitäten' }),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { name: 'Rezeptimporte' }),
  ).toBeVisible()
})
