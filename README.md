# PrepPilot

PrepPilot plant für eine Person eine vollständige Woche aus selbst gepflegten
Lebensmitteln und Rezepten. Ein Meal-Prep-Rezept erzeugt mehrere Portionen, die
innerhalb derselben Woche vollständig und nachvollziehbar verwendet werden.

## Aktueller Funktionsumfang

- genau sieben Tage mit Frühstück, Mittagessen, Abendessen und Snacks
- persönliche Lebensmittel als gemeinsame Nährwertquelle
- alltagstaugliche Einheiten wie Stück, Scheibe oder Dose mit eindeutiger
  Umrechnung in Gramm beziehungsweise Milliliter
- persönliche Rezepte mit Zutaten und eindeutiger Portionenzahl
- aus Zutaten berechnete Nährwerte pro Rezept und Portion
- reproduzierbare Wochenplanung ohne verlorene oder doppelte Batch-Portionen
- gruppierte und abhakbare Einkaufsliste für gespeicherte Wochenpläne
- gezielter Mahlzeitentausch mit passenden Vorschlägen und erwarteten
  Tagesnährwerten

Die technische Grundlage verwendet React/Vite, FastAPI, PostgreSQL und Alembic.
Lebensmittelkatalog, Rezeptverwaltung und ein persistentes Wochenmodell bilden
die umgesetzte fachliche Basis. Die Wochenplanung bewertet vorhandene Rezepte
reproduzierbar anhand der festgelegten Nährwertprioritäten und weist tägliche
Abweichungen aus. Der definierte V5-MVP sowie die ersten Erweiterungen für
Einkauf und Planbearbeitung sind vollständig umgesetzt und lokal abgenommen.

Der ursprüngliche MVP-Umfang steht im [`V5-Plan`](docs/v5-plan.md). Die aktuell
priorisierten nächsten Schritte führt der [`Backlog`](docs/backlog.md); frühere
Produktphasen dokumentiert die [`Projektgeschichte`](docs/project-history.md).

PrepPilot befindet sich in Entwicklung und ist keine medizinische
Ernährungsberatung.
