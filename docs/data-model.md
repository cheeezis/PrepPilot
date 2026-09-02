# Datenmodell

Der Recipe-first-MVP besitzt genau eine fachliche Tabelle: `recipes`.

Sie speichert:

- Quellenname, externe ID und Original-URL
- Titel und ursprüngliche Portionszahl
- Kalorien, Protein, Kohlenhydrate und Fett pro Portion
- originale Zutaten- und Zubereitungslisten
- optionale Vorbereitungs- und Kochzeit
- validierte Importdaten, Inhalts-Hash und Importzeitpunkt
- Lizenzname und Attributionstext

`source_name + external_id` ist eindeutig. Ein erneuter identischer Import
erzeugt keinen zweiten Datensatz. Zutaten sind absichtlich noch keine eigenen
Tabellen: Für die Planung werden ausschließlich die Makros des Gesamtgerichts
verwendet.

`alembic_version` ist eine technische Alembic-Tabelle und kein zusätzliches
fachliches Datenmodell.
