import { expect, test } from '@playwright/test'

test('shows the source and concrete reason for a rejected recipe', async ({ page }) => {
  await page.route('**/api/recipes', async (route) => {
    await route.fulfill({ json: [] })
  })
  await page.route('**/api/imports/nhs', async (route) => {
    await route.fulfill({
      json: {
        created: 0,
        updated: 0,
        unchanged: 9,
        rejected: 1,
        items: [
          {
            source_url: 'https://www.nhs.uk/healthier-families/recipes/test-recipe/',
            status: 'rejected',
            title: null,
            reason: 'protein missing',
          },
        ],
      },
    })
  })

  await page.goto('/recipes')
  await page.getByRole('button', { name: '20 NHS-Rezepte importieren' }).click()

  const status = page.getByRole('status')
  await expect(status).toContainText('1 abgelehnt')
  await expect(status.getByRole('link', { name: 'test recipe' })).toHaveAttribute(
    'href',
    'https://www.nhs.uk/healthier-families/recipes/test-recipe/',
  )
  await expect(
    status.getByText('Pflichtfeld „Protein“ fehlt auf der Quellseite.'),
  ).toBeVisible()
})
