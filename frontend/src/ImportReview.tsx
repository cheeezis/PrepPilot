import { useEffect, useState, type ReactNode } from 'react'
import {
  getImportReview,
  resolveFoodIdentity,
  type FoodConceptOption,
  type ImportReviewOverview,
  type OpenFoodIdentity,
} from './api/importReview'

type LoadStatus = 'loading' | 'ready' | 'error'

const statusNames: Record<string, string> = {
  received: 'Empfangen',
  needs_review: 'Prüfung nötig',
  ready_for_catalog_review: 'Bereit für Katalogprüfung',
  rejected: 'Abgelehnt',
  normalized: 'Normalisiert',
  excluded: 'Ausgeschlossen',
}

const reviewReasonNames: Record<string, string> = {
  unknown_food: 'Lebensmittel noch unbekannt',
  ambiguous_food: 'Mehrere Nährwertprofile möglich',
  unsupported_unit: 'Einheit nicht unterstützt',
  missing_measure_default: 'Umrechnung fehlt',
  invalid_or_ranged_quantity: 'Menge nicht eindeutig',
  incompatible_measurement: 'Einheit passt nicht zum Profil',
  missing_serving_count: 'Portionszahl fehlt',
}

export function ImportReview() {
  const [status, setStatus] = useState<LoadStatus>('loading')
  const [overview, setOverview] = useState<ImportReviewOverview | null>(null)
  const [resolvingId, setResolvingId] = useState<number | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getImportReview(controller.signal)
      .then((value) => {
        setOverview(value)
        setStatus('ready')
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setStatus('error')
      })
    return () => controller.abort()
  }, [])

  async function handleResolve(identifierId: number, conceptKey: string) {
    setResolvingId(identifierId)
    try {
      setOverview(await resolveFoodIdentity(identifierId, conceptKey))
      setStatus('ready')
    } catch {
      setStatus('error')
    } finally {
      setResolvingId(null)
    }
  }

  return (
    <section className="import-review">
      <div className="import-review-heading">
        <p className="eyebrow">Interner Datenbereich</p>
        <h1>Importprüfung</h1>
        <p className="intro-copy">
          Hier siehst du, welche Rezepte angekommen sind, welche Zutaten sicher
          erkannt wurden und welche externe Identität einmalig geklärt werden muss.
        </p>
      </div>

      {status === 'loading' && <p className="notice">Importdaten werden geladen …</p>}
      {status === 'error' && (
        <p className="notice notice--error">
          Die Importübersicht konnte nicht vollständig geladen oder aktualisiert werden.
        </p>
      )}

      {overview && (
        <>
          <div className="import-summary" aria-label="Importstatus">
            <SummaryCard label="Rezepte" value={overview.summary.recipe_count} />
            <SummaryCard
              label="Offene Identitäten"
              value={overview.summary.open_identity_count}
              warning={overview.summary.open_identity_count > 0}
            />
            <SummaryCard
              label="Offene Zutatenzeilen"
              value={overview.summary.review_ingredient_count}
              warning={overview.summary.review_ingredient_count > 0}
            />
          </div>

          <section className="review-section" aria-labelledby="open-identities-heading">
            <div className="review-section-heading">
              <div>
                <p className="eyebrow">Einmalig klären</p>
                <h2 id="open-identities-heading">Offene Zutatenidentitäten</h2>
              </div>
              <p>Eine Zuordnung gilt für alle betroffenen Rezepte.</p>
            </div>
            {overview.open_identities.length === 0 ? (
              <EmptyState>
                Keine offene externe Zutatenidentität. Neue Fälle erscheinen hier
                automatisch nach einem Importlauf.
              </EmptyState>
            ) : (
              <div className="identity-list">
                {overview.open_identities.map((identity) => (
                  <IdentityCard
                    key={identity.id}
                    identity={identity}
                    concepts={overview.concepts}
                    resolving={resolvingId === identity.id}
                    onResolve={handleResolve}
                  />
                ))}
              </div>
            )}
          </section>

          <section className="review-section" aria-labelledby="recipe-imports-heading">
            <div className="review-section-heading">
              <div>
                <p className="eyebrow">Eingang</p>
                <h2 id="recipe-imports-heading">Rezeptimporte</h2>
              </div>
            </div>
            {overview.recipes.length === 0 ? (
              <EmptyState>
                Noch wurden keine Rezepte importiert. Der nächste Wikibooks-Adapter
                wird diesen Bereich mit echten Kandidaten füllen.
              </EmptyState>
            ) : (
              <div className="imported-recipe-list">
                {overview.recipes.map((recipe) => (
                  <article className="imported-recipe" key={recipe.id}>
                    <div className="imported-recipe-title">
                      <div>
                        <small>{recipe.source_name} · {recipe.external_id}</small>
                        <h3>{recipe.title}</h3>
                      </div>
                      <StatusBadge status={recipe.status} />
                    </div>
                    <ul>
                      {recipe.ingredients.map((ingredient) => (
                        <li key={ingredient.id}>
                          <div>
                            <strong>{ingredient.raw_line}</strong>
                            <small>
                              {ingredient.concept_key
                                ? `Konzept: ${ingredient.concept_key}`
                                : ingredient.source_label
                                  ? `Quelle: ${ingredient.source_label}`
                                  : 'Keine kanonische Quellenidentität'}
                            </small>
                          </div>
                          <span>
                            {ingredient.review_reason
                              ? reviewReasonNames[ingredient.review_reason]
                                ?? ingredient.review_reason
                              : statusNames[ingredient.status] ?? ingredient.status}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </section>
  )
}

function SummaryCard({
  label,
  value,
  warning = false,
}: {
  label: string
  value: number
  warning?: boolean
}) {
  return (
    <div className={`summary-card${warning ? ' summary-card--warning' : ''}`}>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  )
}

function IdentityCard({
  identity,
  concepts,
  resolving,
  onResolve,
}: {
  identity: OpenFoodIdentity
  concepts: FoodConceptOption[]
  resolving: boolean
  onResolve: (identifierId: number, conceptKey: string) => void
}) {
  const [conceptKey, setConceptKey] = useState('')

  return (
    <article className="identity-card">
      <div className="identity-details">
        <small>{identity.source_name} · ID {identity.external_id}</small>
        <h3>{identity.source_label ?? identity.external_id}</h3>
        <p>
          {identity.ingredient_count} Zutatenzeilen in {identity.recipe_count}
          {' '}{identity.recipe_count === 1 ? 'Rezept' : 'Rezepten'}
        </p>
        {identity.source_url && (
          <a href={identity.source_url} target="_blank" rel="noreferrer">
            Quellseite öffnen
          </a>
        )}
      </div>
      <div className="identity-action">
        <label className="field">
          <span>Lebensmittelkonzept</span>
          <select
            value={conceptKey}
            onChange={(event) => setConceptKey(event.target.value)}
          >
            <option value="" disabled>
              Konzept auswählen …
            </option>
            {concepts.map((concept) => (
              <option key={concept.key} value={concept.key}>
                {concept.name} ({concept.profile_count} Profile)
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={!conceptKey || resolving}
          onClick={() => onResolve(identity.id, conceptKey)}
        >
          {resolving ? 'Wird zugeordnet …' : 'Einmalig zuordnen'}
        </button>
      </div>
    </article>
  )
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`review-status review-status--${status}`}>
      {statusNames[status] ?? status}
    </span>
  )
}

function EmptyState({ children }: { children: ReactNode }) {
  return <p className="empty-state">{children}</p>
}
