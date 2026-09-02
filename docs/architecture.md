# Architektur

Stand: 1. September 2026

## Kern

PrepPilot ist ein modularer Monolith:

- React und TypeScript im Frontend
- FastAPI und Python im Backend
- PostgreSQL mit SQLAlchemy und Alembic
- Docker Compose ausschließlich für die lokale Datenbank

Das Frontend greift nur auf die PrepPilot-API zu. Der Planer liest ausschließlich
vollständige, freigegebene Lebensmittel und Mahlzeiten aus PostgreSQL. Externe
Datenquellen sind niemals eine Laufzeitabhängigkeit der Planung.

## Produktiver Katalog

`foods`, `meals`, `meal_ingredients`, `meal_roles` und
`meal_portion_factors` bilden die stabile Grenze zum Planer. Die versionierte
`catalog.json` liefert den kuratierten Grundbestand. Ein Seed ersetzt nur
Einträge mit der Herkunft `curated_seed`; kontrolliert importierte Einträge
bleiben erhalten.

Der Planer kennt keine externen Rezeptformate, Haushaltsmaße, unsicheren
Zutatenzuordnungen oder Nährwertsuchergebnisse.

## Behaltener Importkern

Externe Rezepte werden zunächst quellenneutral in `recipe_imports` und
`recipe_import_ingredients` gespeichert. Rohdaten, Quellkennung und Inhalts-Hash
bleiben erhalten. Die Normalisierung ist deterministisch und führt zu
`ready_for_catalog_review`, `needs_review` oder `rejected`.

Bestätigte Entscheidungen werden getrennt gespeichert:

- `food_aliases` für wiederverwendbare Zutatenbezeichnungen
- `food_measure_defaults` für belegte Stück- und Portionsgewichte
- `import_review_decisions` als nachvollziehbare Entscheidungshistorie

Nur ein vollständig normalisierter und ausdrücklich bestätigter Rezeptimport
darf über den Promotion-Service eine Mahlzeit erzeugen. Die Importtabellen
werden nicht direkt vom Planer gelesen.

## Lebensmittel-Referenzdaten

Die offiziellen FoodData-Central-Archive für Foundation Foods und SR Legacy
können als kompakter lokaler Referenzbestand in `food_reference_items` geladen
werden. Diese Datensätze sind Nährwertprofile und ausdrücklich keine automatisch
freigegebenen Lebensmittel.

Die frühere direkte FDC-Suche, heuristische Vorschlagslogik und automatische
Materialisierung wurden entfernt. Ein breiter Zutatenbegriff wie „chicken“ darf
nicht allein anhand eines ähnlich benannten Nährwertprofils zugeordnet werden.

## Neue Quellengrenze

Ein neuer Rezeptadapter wird als Importprozess implementiert und ruft direkt den
quellenneutralen Import-Service auf. Für den Datenaufbau werden keine temporären
internen HTTP-Endpunkte angelegt. Ein Adapter muss mindestens folgende Metadaten
liefern:

- stabile Quell- und Rezeptkennung
- Rohdaten und Quellrevision
- Titel, Zutaten, Zubereitung und belastbare Portionen
- Lizenz, Attribution und Quell-URL

Bulk-Import ist nur für ausdrücklich kompatibel lizenzierte Quellen erlaubt.
Scraping geschützter Seiten ist kein Weg zum PrepPilot-Grundbestand.
Nutzerinitiierte URL-Imports werden später als getrennte Produktfunktion
bewertet.

## Nächste Modellentscheidung

Vor einem großen Rezeptlauf werden Zutatenidentität und Nährwertprofil getrennt:

```text
Quellenzutat
  -> kanonisches Lebensmittelkonzept
  -> ein oder mehrere Nährwertprofile mit Herkunft und Zustand
```

Eine Quellenzutat wird einmal einem Konzept zugeordnet. Das ausgewählte
Nährwertprofil darf davon unabhängig geändert oder ergänzt werden. Die genaue
Migration wird erst im nächsten Umsetzungsschnitt festgelegt.

## Qualitätsgrenzen

- Keine Schätzung fehlender Portionen im automatischen Import.
- Keine automatische Freigabe mehrdeutiger Zutaten.
- Keine Veröffentlichung unvollständiger Nährwerte.
- Idempotente Imports anhand Quelle, externer Kennung und Inhalt.
- Pytest, Ruff und Mypy müssen vor einem Commit vollständig bestehen.

## Noch zu entscheiden

- genaue Tabellen für Lebensmittelkonzepte und Nährwertprofile
- Betriebsform für Importläufe: Kommando, Job oder Admin-Oberfläche
- Umgang mit CC-BY-SA-abgeleiteten Rezepttexten im Produkt
- CI/CD und Deployment-Ziel
