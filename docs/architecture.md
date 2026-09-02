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

## Lebensmittelkonzepte und Nährwertprofile

Vor einem großen Rezeptlauf werden Zutatenidentität und Nährwertprofil getrennt:

```text
Quellenzutat
  -> kanonisches Lebensmittelkonzept
  -> ein oder mehrere Nährwertprofile mit Herkunft und Zustand
```

`food_concepts` speichert die stabile fachliche Identität.
`food_source_identifiers` speichert jede externe Zutatenkennung genau einmal.
Solange `concept_id` dort leer ist, bildet die Zeile den gemeinsamen offenen
Review-Fall für alle betroffenen Rezepte. Nach der einmaligen Zuordnung gilt sie
für bestehende und spätere Importe derselben Quellenkennung. Jedes konkrete
`food` verweist über `concept_id` auf genau ein Konzept; ein Konzept kann dadurch
weiterhin mehrere Nährwertprofile besitzen. Eine importierte Zutatenzeile
verweist über `source_identifier_id` auf die Quellenkennung und hält das erkannte
Konzept zusätzlich über `concept_id` fest.

Der Katalog beschreibt für jedes Food-Profil einen ausdrücklichen
`concept_key` und `concept_name`. Dadurch kann ein konkretes Profil wie
`milk_1_5` dem allgemeinen Konzept `milk` zugeordnet werden. Der Seed migriert
Quellen- und Rezeptzuordnungen von den früheren 1:1-Konzepten und entfernt nur
Konzepte, die danach von keinem Food, keiner Quellenidentität und keiner
Importzutat mehr referenziert werden. Mehrere Foods desselben Konzepts führen
bewusst noch nicht zu einer automatischen Standardauswahl.
Besitzt ein geklärtes Konzept genau ein Food-Profil, darf dieses deterministisch
verwendet werden. Bei mehreren oder keinem Profil bleibt die Rezeptzutat in der
Review-Grenze.

Eine lokale interne Importprüfung macht Rezeptimporte, offene Identitäten und
deren Häufigkeit sichtbar. Ihre Endpunkte lesen ausschließlich den Importzustand
oder ordnen eine Quellenidentität einem bestehenden Konzept zu. Sie starten
keine externen Importläufe und sind keine öffentliche Produkt-API.

## Qualitätsgrenzen

- Keine Schätzung fehlender Portionen im automatischen Import.
- Keine automatische Freigabe mehrdeutiger Zutaten.
- Keine Veröffentlichung unvollständiger Nährwerte.
- Idempotente Imports anhand Quelle, externer Kennung und Inhalt.
- Pytest, Ruff und Mypy müssen vor einem Commit vollständig bestehen.

## Noch zu entscheiden

- Regeln zum Anlegen neuer Konzepte und Auswählen konkreter Nährwertprofile
- Betriebsform für Importläufe: Kommando, Job oder Admin-Oberfläche
- Umgang mit CC-BY-SA-abgeleiteten Rezepttexten im Produkt
- CI/CD und Deployment-Ziel
