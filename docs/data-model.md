# Datenmodell

Der Recipe-first-MVP besitzt genau eine fachliche Tabelle: `recipes`.

Sie speichert:

- Quellenname, externe ID und Original-URL
- Titel, NHS-Mahlzeitenkategorien und ursprüngliche Portionszahl
- Kalorien, Protein, Kohlenhydrate, Zucker, Fett, gesättigte Fettsäuren,
  Ballaststoffe und Salz pro Portion
- originale Zutaten- und Zubereitungslisten
- optionale Vorbereitungs- und Kochzeit
- validierte Importdaten, Inhalts-Hash und Importzeitpunkt
- Lizenzname und Attributionstext

`source_name + external_id` ist eindeutig. Ein erneuter identischer Import
erzeugt keinen zweiten Datensatz. Zutaten sind absichtlich noch keine eigenen
Tabellen: Für die Planung werden ausschließlich die Makros des Gesamtgerichts
verwendet.

`categories` speichert eine kleine Liste aus `breakfast`, `lunch`, `dinner` und
`snack`. Mehrere Werte sind nötig, weil NHS dasselbe Rezept in mehreren
Sammlungen führen kann. NHS-Getränke werden dabei als Snack abgebildet. Für
diese überschaubare Quellenmetadaten-Liste ist keine zusätzliche
Kategorietabelle nötig.

`alembic_version` ist eine technische Alembic-Tabelle und kein zusätzliches
fachliches Datenmodell.
