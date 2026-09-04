import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { WeeklyPlans } from './WeeklyPlans'

describe('WeeklyPlans', () => {
  it('shows all inputs required to generate a plan', () => {
    const html = renderToStaticMarkup(<WeeklyPlans />)
    expect(html).toContain('Startdatum')
    expect(html).toContain('Snacks pro Tag')
    expect(html).toContain('Kalorienmaximum')
    expect(html).toContain('Proteinminimum')
    expect(html).toContain('Kohlenhydratziel')
    expect(html).toContain('Fettmaximum')
  })
})
