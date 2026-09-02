# Recipe-first-MVP

Stand: 2. September 2026

## Produktziel

PrepPilot importiert vollständige Rezepte aus genau einer externen Quelle,
speichert sie dauerhaft in PostgreSQL und erstellt aus den von der Quelle
gelieferten Nährwerten einen Tagesplan.

Der erste nutzbare Ablauf lautet:

```text
externe Rezeptquelle
  -> validieren und idempotent importieren
  -> vollständige Rezepte in PostgreSQL speichern
  -> Tagesplan aus Nährwerten pro Portion erstellen
  -> Rezepte und Plan im Frontend anzeigen
```

## Bewusst kleiner Funktionsumfang

Der MVP kann:

- einen begrenzten Lauf aus genau einer freigegebenen Quelle starten
- vollständige Rezepte samt Herkunft speichern und aktualisieren
- den gespeicherten Rezeptbestand im Frontend anzeigen
- Tagespläne anhand von Kalorien, Protein, Kohlenhydraten und Fett erzeugen
- bei einem erneuten identischen Lauf Duplikate vermeiden

Der MVP kann noch nicht:

- Nährwerte aus einzelnen Zutaten berechnen
- Zutaten vereinheitlichen oder Lebensmittelprofile auswählen
- Einkaufslisten, Allergene, Ausschlüsse oder Ersetzungen ableiten
- mehrere Quellen zusammenführen
- eigene Rezepte, Benutzerkonten oder Hintergrundimporte verwalten

## Anforderungen an die erste Quelle

Eine Quelle ist nur geeignet, wenn sie für jedes verwendbare Rezept liefert:

- stabile Rezeptkennung und Quell-URL
- Titel und belastbare Portionsangabe
- Kalorien, Protein, Kohlenhydrate und Fett pro Portion
- Zutaten und Zubereitung
- eine Nutzungserlaubnis, die das dauerhafte Speichern und Anzeigen zulässt

Die USDA Child Nutrition Recipe Box ist der erste Prüfkandidat. Vor der
Implementierung werden Datenformat, nutzbarer Umfang und Rechte noch einmal an
einer kleinen Stichprobe bestätigt. Kommerzielle APIs mit Cache- oder
Speicherverbot sind kein Grundbestand für diesen MVP.

## Zielmodell

Für den ersten Schnitt genügt eine produktive Tabelle `recipes`. Sie enthält
mindestens:

- interne ID
- Quelle, externe ID und Quell-URL
- Titel und Anzahl der Portionen
- Kalorien, Protein, Kohlenhydrate und Fett pro Portion
- Zutaten als quellennahe strukturierte Daten
- Zubereitung und optionale Zubereitungszeit
- Originaldaten, Inhalts-Hash und Importzeitpunkt

Quelle und externe ID identifizieren ein Rezept eindeutig. Der Inhalts-Hash
erkennt unveränderte und aktualisierte Quelldaten. Nur vollständig validierte
Rezepte werden gespeichert; abgelehnte Kandidaten erscheinen im Laufbericht,
aber nicht im produktiven Bestand.

`recipes` ist zugleich der Katalog des Planers. Eine zusätzliche Trennung in
`meals`, `foods` und normalisierte Zutaten ist für diesen MVP nicht vorgesehen.

## Planungsregeln

- Maßgeblich sind ausschließlich die gespeicherten Quellenwerte pro Portion.
- Ein Rezept kann über ganzzahlige Portionen skaliert werden.
- Der Nutzer gibt Zielwerte und die gewünschte Anzahl der Mahlzeiten an.
- Der Planer liefert passende Kombinationen oder kennzeichnet die beste
  Annäherung transparent.
- Die Herkunft jedes geplanten Rezepts bleibt im Frontend sichtbar.

## Klassifikation des bestehenden Systems

Die folgende Klassifikation beschreibt den geplanten Umbau. Sie löscht noch
keine Tabelle und keinen Dienst.

### PostgreSQL-Tabellen

| Bestehende Tabelle | Entscheidung | Begründung |
|---|---|---|
| `meals` | ersetzen | Geht zusammen mit Rezeptdaten in `recipes` auf. |
| `recipe_imports` | ersetzen | Rohdaten und produktive Rezeptwerte werden für den MVP in `recipes` zusammengeführt. |
| `foods` | entfernen | Rezeptnährwerte werden nicht mehr aus Lebensmitteln berechnet. |
| `meal_ingredients` | entfernen | Quellennahe Zutaten liegen zunächst direkt am Rezept. |
| `meal_portion_factors` | entfernen | Der Planer skaliert mit ganzen Portionen statt kuratierten Faktoren. |
| `meal_roles` | entfernen | Kategorien und Rollen sind erst nach dem vertikalen MVP vorgesehen. |
| `recipe_import_ingredients` | entfernen | Zutaten müssen vor der Planung nicht einzeln normalisiert werden. |
| `food_imports` | entfernen | Einzelne Lebensmittel werden im MVP nicht importiert. |
| `food_reference_items` | entfernen | Der lokale FDC-Referenzbestand wird nicht benötigt. |
| `food_aliases` | entfernen | Es findet keine automatische Zutatenzuordnung statt. |
| `food_measure_defaults` | entfernen | Haushaltsmaße werden nicht in Gramm oder Milliliter umgerechnet. |
| `import_review_decisions` | entfernen | Die bisherige manuelle Zutatenprüfung entfällt. |
| `alembic_version` | beibehalten | Alembic verwaltet weiterhin den Datenbankstand. |

Da noch keine Produktionsdaten existieren, soll die bisherige
Migrationskette nach Freigabe durch eine verständliche neue Ausgangsmigration
ersetzt und die lokale Datenbank kontrolliert neu erstellt werden.

### Backend

| Bestandteil | Entscheidung | Begründung |
|---|---|---|
| FastAPI-Anwendung und Datenbankverbindung | beibehalten | Technische Basis bleibt passend. |
| Health-Endpunkt | anpassen | Prüft künftig Datenbank und Rezeptbestand statt Katalog. |
| Planbewertung und Abweichungsregeln | beibehalten | Zielbereiche und Scoring bleiben fachlich nützlich. |
| Planeroptionen und Mahlzeitenrollen | ersetzen | Optionen kommen direkt aus `recipes`; feste Rollen entfallen zunächst. |
| API für Tagespläne | anpassen | Liefert gespeicherte Rezepte und Quellenwerte statt berechneter Food-Werte. |
| Katalogdatei, Repository und Seed | entfernen | `catalog.json` ist nicht mehr der Produktivbestand. |
| Rezept-Inbox und Promotion | entfernen | Import und Produktivkatalog sind im MVP nicht getrennt. |
| Zutaten-Normalisierung und Review | entfernen | Unklare Einzelzutaten blockieren kein vollständiges Rezept. |
| Food-Import und FDC-Referenzimport | entfernen | Lebensmittelprofile gehören nicht zum ersten Schnitt. |

### Frontend

| Bestandteil | Entscheidung | Begründung |
|---|---|---|
| App-Grundlayout und Zielformular | beibehalten | Der zentrale Nutzerfluss bleibt gleich. |
| Darstellung von Plan und Abweichungen | anpassen | Zeigt Rezepte, Portionen und Quellen statt Food-Berechnung. |
| Wochenansicht | vorerst entfernen | Der MVP beweist zunächst nur einen Tagesplan. |
| Einkaufsliste | entfernen | Ohne normalisierte Zutaten wäre sie nicht belastbar. |
| Health- und Day-Plan-Client | anpassen | Antwortmodell wird kleiner und rezeptorientiert. |
| bestehende Tests | ersetzen oder anpassen | Nur Verhalten des neuen vertikalen Ablaufs bleibt relevant. |

### Vollständiger Datei-Audit

Das Repository enthält vor dem Umbau 72 versionierte Dateien. Die folgenden
27 Dateien gehören ausschließlich zum alten Katalog-, Lebensmittel- oder
Normalisierungsansatz und können im Recipe-first-Schnitt vollständig entfallen.

Alte Migrationen, die durch eine neue Ausgangsmigration ersetzt werden:

- `backend/migrations/versions/a8f4c2d91e60_create_mvp_catalog.py`
- `backend/migrations/versions/c3d7e6a421bf_add_meal_portion_factors.py`
- `backend/migrations/versions/e7b61c3094ad_add_recipe_import_inbox.py`
- `backend/migrations/versions/f4a2d891be37_add_imported_meal_origin.py`
- `backend/migrations/versions/a91c5e73d204_add_food_import_inbox.py`
- `backend/migrations/versions/b7d2e4f91a63_add_food_reference_catalog.py`

Produktivcode, der entfernt wird:

- `backend/src/preppilot_api/catalog.json`
- `backend/src/preppilot_api/catalog_data.py`
- `backend/src/preppilot_api/catalog_repository.py`
- `backend/src/preppilot_api/catalog_seed.py`
- `backend/src/preppilot_api/food_imports.py`
- `backend/src/preppilot_api/food_reference.py`
- `backend/src/preppilot_api/recipe_catalog_promotion.py`
- `backend/src/preppilot_api/recipe_imports.py`

Tests und Fixtures, die nur den alten Ablauf prüfen:

- `backend/tests/fixtures/recipe_imports/metric_chicken_rice.json`
- `backend/tests/fixtures/recipe_imports/metric_whey_shake.json`
- `backend/tests/fixtures/recipe_imports/missing_measure.json`
- `backend/tests/fixtures/recipe_imports/unknown_food.json`
- `backend/tests/test_catalog_data.py`
- `backend/tests/test_catalog_seed.py`
- `backend/tests/test_food_imports.py`
- `backend/tests/test_food_reference.py`
- `backend/tests/test_real_recipe_pipeline.py`
- `backend/tests/test_recipe_catalog_promotion.py`
- `backend/tests/test_recipe_imports.py`

Frontendcode, der ohne Einkaufsliste nicht mehr benötigt wird:

- `frontend/src/weeklyPlan.ts`
- `frontend/src/weeklyPlan.test.ts`

Die folgenden zentralen Dateien bleiben bestehen, werden aber inhaltlich auf
den Recipe-first-Ablauf reduziert:

- `backend/src/preppilot_api/models.py`
- `backend/src/preppilot_api/main.py`
- `backend/src/preppilot_api/nutrition.py`
- `backend/src/preppilot_api/planner.py`
- `backend/tests/test_models.py`
- `backend/tests/test_health.py`
- `backend/tests/test_nutrition.py`
- `backend/tests/test_planner.py`
- `frontend/src/App.tsx`
- `frontend/src/App.css`
- `frontend/src/api/dayPlans.ts`
- `frontend/src/api/dayPlans.test.ts`
- `frontend/src/api/health.ts`
- `frontend/src/api/health.test.ts`
- `frontend/e2e/day-planner.e2e.ts`
- `README.md` und die fachlichen Dokumente unter `docs/`

Unverändert oder nahezu unverändert bleiben die technische Infrastruktur:

- Docker Compose und PostgreSQL
- FastAPI-, SQLAlchemy- und Alembic-Grundkonfiguration
- React-, Vite-, TypeScript-, Vitest- und Playwright-Konfiguration
- Python- und Node-Paketverwaltung
- Backend- und Frontend-Einstiegspunkte

## Sichere Umsetzungsreihenfolge

1. Zehn echte Kandidaten der ersten Quelle rein lesend untersuchen.
2. Datenformat, Nährwertvollständigkeit und dauerhafte Nutzbarkeit bestätigen.
3. Exaktes `recipes`-Schema anhand dieser Quelldaten festlegen.
4. Alte lokale Datenbank nach ausdrücklicher Freigabe neu erstellen.
5. Importer, Planer und API auf den neuen Ablauf reduzieren.
6. Frontend vereinfachen und den vollständigen Ablauf abnehmen.

## Abnahme

Der Recipe-first-MVP ist erreicht, wenn:

1. mindestens zehn vollständige Rezepte aus einer Quelle gespeichert sind,
2. ein identischer zweiter Import keine Duplikate erzeugt,
3. alle gespeicherten Rezepte vier Nährwerte pro Portion besitzen,
4. das Frontend den realen PostgreSQL-Bestand anzeigt,
5. der Planer daraus mindestens einen Tagesplan oder eine erklärte Annäherung
   erzeugt und
6. Backend-, Frontend- und Browsertests den vollständigen Ablauf abdecken.

## Wachstum nach der Abnahme

Erst nach diesem vertikalen Ablauf werden Funktionen einzeln ergänzt. Die
vorgesehene Reihenfolge ist:

1. weitere Rezepte derselben Quelle
2. Rezeptkategorien und bessere Planvielfalt
3. zweite rechtlich kompatible Quelle
4. normalisierte Zutaten für Filter und Einkaufslisten
5. Lebensmittel- und Nährwertprofile für eigene Rezepte oder Ersetzungen
