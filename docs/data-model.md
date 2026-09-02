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

## Referenzdaten

- `food_reference_items`: lokal importierte FoodData-Central-Nährwertprofile

Die Referenztabelle ist vom produktiven Katalog getrennt. Ein vollständiges
Nährwertprofil ist nicht automatisch dasselbe wie ein kanonisches Lebensmittel.
Wird ein Profil später als `food` übernommen, stehen Quelle und Referenz direkt
am produktiven Food; eine zusätzliche Food-Inbox wird dafür nicht geführt.

`carbs_per_100` verwendet die europäische Bedeutung verwertbarer Kohlenhydrate
ohne Ballaststoffe. Bei FoodData Central wird dieser Wert aus
Gesamtkohlenhydraten minus Ballaststoffen abgeleitet, sofern beide Werte
vorliegen.

## Lebensmittelkonzepte

Die fachliche Zutatenidentität ist von konkreten Nährwertwerten getrennt:

- `food_concepts`: kanonische interne Identität, beispielsweise „Milch“
- `food_source_identifiers`: stabile externe Identitäten wie eine
  Wikibooks-Zutatenseite; eine leere `concept_id` kennzeichnet einen offenen,
  quellenweit wiederverwendbaren Review-Fall
- `foods.concept_id`: eindeutige Zugehörigkeit eines Nährwertprofils zu seinem
  Konzept
- `recipe_import_ingredients.concept_id`: erkannte Identität vor der Wahl eines
  konkreten Nährwertprofils
- `recipe_import_ingredients.source_identifier_id`: Verbindung zur einmalig
  gespeicherten externen Zutatenidentität

Ein Konzept darf mehrere Profile besitzen. Das Modell kennzeichnet absichtlich
noch kein Standardprofil: Wenn eine Quelle nur „Milch“ nennt, wird nicht
automatisch zwischen Vollmilch und fettarmer Milch entschieden. Der bestehende
Katalog wird beim Seed zunächst 1:1 abgebildet, damit Planer und Mahlzeiten
unverändert bleiben.

Wird eine externe Kennung einmal einem Konzept zugeordnet, werden alle bereits
damit verbundenen Rezeptimporte neu verarbeitet. Genau ein vorhandenes Profil
kann deterministisch verwendet werden; mehrere Profile bleiben mehrdeutig.

## Bewusste Grenzen

Noch nicht festgelegt sind die automatische Anlage neuer Konzepte und die
Auswahl zwischen konkurrierenden Nährwertprofilen. Ebenfalls nicht modelliert
sind Allergene, Preise, Packungsgrößen, Vorräte, Bilder und Nutzerdaten. Externe
Rezept- oder Lebensmittelquellen werden nicht vom Planer zur Laufzeit abgefragt.
