# Datenmodell

Stand: 1. September 2026

## Produktiver Katalog

- `foods`: freigegebene Lebensmittel mit Basiseinheit, vier MVP-Nährwerten und
  nachvollziehbarer Herkunft
- `meals`: freigegebene Mahlzeiten mit Herkunft, Zubereitungszeit und Anleitung
- `meal_ingredients`: Lebensmittel und normalisierte Menge einer Grundportion
- `meal_portion_factors`: erlaubte Skalierungsfaktoren
- `meal_roles`: Rollen einer Mahlzeit im Tagesplan

Alle produktiven Zutatenmengen liegen in Gramm oder Millilitern vor. Nährwerte
einer Mahlzeit werden aus ihren Lebensmitteln berechnet und nicht zusätzlich
gespeichert.

## Rezept-Inbox

- `recipe_imports`: Quelle, externe Kennung, Rohdaten, Inhalts-Hash, Portionen
  und Status
- `recipe_import_ingredients`: originale Zutatenzeile, Parsing-Ergebnis,
  Zuordnung, normalisierte Menge und Prüfgrund
- `food_aliases`: bestätigte wiederverwendbare Bezeichnungen
- `food_measure_defaults`: belegte lebensmittelspezifische Mengen
- `import_review_decisions`: Historie manueller Entscheidungen

Ein Rezeptimport ist `received`, `needs_review`,
`ready_for_catalog_review` oder `rejected`. Der Status
`ready_for_catalog_review` ist noch keine Freigabe für den Planer.

Metrische Einheiten werden direkt normalisiert. Teelöffel und Esslöffel nutzen
die festgelegten PrepPilot-Mengen. Stückangaben benötigen einen passenden
lebensmittelspezifischen Standard; einen generischen Gewichtsfallback gibt es
nicht.

## Food-Inbox und Referenzdaten

- `food_imports`: quellenneutrale Rohdaten und abgeleitete Kandidatenwerte vor
  einer kontrollierten Veröffentlichung
- `food_reference_items`: lokal importierte FoodData-Central-Nährwertprofile

Beide Tabellen sind vom produktiven Katalog getrennt. Ein vollständiges
Nährwertprofil ist nicht automatisch dasselbe wie ein kanonisches Lebensmittel.

`carbs_per_100` verwendet die europäische Bedeutung verwertbarer Kohlenhydrate
ohne Ballaststoffe. Bei FoodData Central wird dieser Wert aus
Gesamtkohlenhydraten minus Ballaststoffen abgeleitet, sofern beide Werte
vorliegen.

## Offene Modelllücke

`foods` verbindet derzeit noch Lebensmittelidentität und genau ein
Nährwertprofil. Für größere Rezeptbestände reicht das nicht aus. Geplant ist
eine explizite Trennung zwischen:

- kanonischem Lebensmittelkonzept, beispielsweise „Milch“
- Quellenidentität, beispielsweise einer Wikibooks-Zutatenseite
- Nährwertprofil, beispielsweise Vollmilch aus FDC oder CoFID
- Zustand beziehungsweise Verarbeitung, beispielsweise roh, gekocht oder
  getrocknet

Diese Tabellen existieren noch nicht. Sie werden vor dem ersten großen Import
als eigener, rückwärtskompatibler Migrationsschnitt entworfen.

## Bewusste Grenzen

Noch nicht modelliert sind konkurrierende Nährwertprofile, Allergene, Preise,
Packungsgrößen, Vorräte, Bilder und Nutzerdaten. Externe Rezept- oder
Lebensmittelquellen werden nicht vom Planer zur Laufzeit abgefragt.
