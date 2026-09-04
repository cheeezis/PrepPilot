import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { RecipeCatalog } from './RecipeCatalog'

describe('RecipeCatalog', () => {
  it('shows the required recipe fields', () => {
    const html = renderToStaticMarkup(<RecipeCatalog />)

    expect(html).toContain('Rezept hinzufügen')
    expect(html).toContain('Portionen')
    expect(html).toContain('Frühstück')
    expect(html).toContain('Snack')
    expect(html).toContain('Zutaten')
    expect(html).toContain('Zubereitung')
  })
})
