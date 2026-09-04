import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('App', () => {
  it('shows the empty V5 application state', () => {
    const html = renderToStaticMarkup(<App />)

    expect(html).toContain('Noch keine Lebensmittel oder Rezepte')
    expect(html).toContain('persönliche Lebensmittel')
    expect(html).not.toContain('Tagesplan')
  })
})
