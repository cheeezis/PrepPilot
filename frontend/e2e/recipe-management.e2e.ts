import { expect, test } from '@playwright/test'

const createdRecipeIds: number[] = []

test.afterEach(async ({ request }) => {
  for (const recipeId of createdRecipeIds.splice(0)) {
    await request.delete(`/api/recipes/${recipeId}`)
  }
})

test('creates, edits and deletes a personal recipe', async ({ page }) => {
  const suffix = Date.now()
  const originalTitle = `Mein Test-Curry ${suffix}`
  const updatedTitle = `Mein Curry mit Spinat ${suffix}`
  await page.goto('/recipes')

  await page.getByLabel('Rezeptname').fill(originalTitle)
  await page.getByLabel('Rezept ergibt').fill('4')
  await page.getByRole('checkbox', { name: 'Mittagessen' }).check()
  await page.getByLabel('Kalorien').fill('520')
  await page.getByRole('spinbutton', { name: 'Protein g' }).fill('32')
  await page.getByRole('spinbutton', { name: 'Kohlenhydrate g' }).fill('61')
  await page.getByRole('spinbutton', { name: 'Fett g' }).fill('14')
  await page.getByLabel('Menge Zutat 1').fill('800')
  await page.getByLabel('Einheit Zutat 1').fill('g')
  await page.getByLabel('Name Zutat 1').fill('Kartoffeln')
  await page.getByRole('button', { name: 'Zutat hinzufügen' }).click()
  await page.getByLabel('Menge Zutat 2').fill('1')
  await page.getByLabel('Einheit Zutat 2').fill('Dose')
  await page.getByLabel('Name Zutat 2').fill('Kichererbsen')
  await page.getByLabel('Zubereitung – ein Schritt pro Zeile').fill(
    'Kartoffeln schneiden.\nAlles köcheln lassen.',
  )
  const createResponsePromise = page.waitForResponse((response) => (
    response.request().method() === 'POST'
    && new URL(response.url()).pathname === '/api/recipes'
  ))
  await page.getByRole('button', { name: 'Rezept speichern' }).click()
  const createResponse = await createResponsePromise
  const recipeId = (await createResponse.json()).id as number
  createdRecipeIds.push(recipeId)

  const card = page.locator('.recipe-card').filter({ hasText: originalTitle })
  await expect(card).toHaveCount(1)
  await expect(page.getByLabel('Rezeptname')).toHaveValue('')
  await card.locator('summary').click()
  await card.getByRole('button', { name: 'Bearbeiten' }).click()
  await page.getByLabel('Rezeptname').fill(updatedTitle)
  await page.getByRole('button', { name: 'Änderungen speichern' }).click()

  const updatedCard = page.locator('.recipe-card').filter({ hasText: updatedTitle })
  await expect(updatedCard).toHaveCount(1)
  page.once('dialog', (dialog) => dialog.accept())
  await updatedCard.getByRole('button', { name: 'Löschen' }).click()
  await expect(updatedCard).toHaveCount(0)
  createdRecipeIds.splice(createdRecipeIds.indexOf(recipeId), 1)
})
