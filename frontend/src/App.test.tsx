import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('shows the food catalog and its required fields', () => {
    const html = renderToStaticMarkup(<App />)

    expect(html).toContain('Lebensmittel hinzufügen')
    expect(html).toContain('pro 100 g')
    expect(html).toContain('Kalorien')
    expect(html).toContain('Protein')
    expect(html).toContain('Kohlenhydrate')
    expect(html).toContain('Fett')
  })
})
