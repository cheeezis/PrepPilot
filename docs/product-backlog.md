# Produkt-Backlog

Stand: 2. September 2026

## Nächster Produktabschnitt

### Recipe-first-MVP

Der nächste Schnitt baut einen vollständigen, aber bewusst kleinen Ablauf aus
genau einer Quelle. Importierte Rezepte bringen ihre Nährwerte pro Portion
bereits mit und können deshalb ohne normalisierte Lebensmittel geplant werden.

Der erste Prüfkandidat ist die USDA Child Nutrition Recipe Box. Zunächst wird
eine Stichprobe von zehn geeigneten Rezepten hinsichtlich Datenformat,
Nährwertvollständigkeit und dauerhafter Nutzbarkeit geprüft.

Die verbindliche Spezifikation steht in
[`recipe-first-mvp.md`](recipe-first-mvp.md).

### Nutzerinitiierter URL-Import

Ein späterer Nutzer kann ein einzelnes Rezept aus einer URL in seine private
Sammlung übernehmen. Schema.org/JSON-LD und `recipe-scrapers` sind dafür
technisch geeignet. Diese Funktion ist von einem Bulk-Katalogimport zu trennen
und muss Quellrechte, Attribution und Bilder gesondert behandeln.

### Importbetrieb

Noch zu entscheiden ist, ob wiederholte Importläufe als Kommando, Hintergrundjob
oder kleine Admin-Oberfläche gestartet werden. Temporäre interne HTTP-Endpunkte
sollen dafür nicht erneut entstehen.

### Zutaten und Lebensmittel

Normalisierte Zutaten, Lebensmittelkonzepte und eigene Nährwertprofile werden
erst nach dem Recipe-first-MVP wieder aufgenommen. Sie dienen dann konkreten
Funktionen wie Einkaufslisten, Allergenen, Ausschlüssen und Ersetzungen, nicht
der grundlegenden Freigabe eines importierten Rezepts.

## Produktvalidierung

Der technische MVP soll mit geeigneten Personen aus der Zielgruppe geprüft
werden. Erfolgskriterien und Ablauf werden festgelegt, sobald eine passende
Testgruppe verfügbar ist.

## Spätere Produktfunktionen

- unterschiedliche Tagespläne innerhalb einer Woche
- Mahlzeiten austauschen und Wiederholungen steuern
- Ernährungsformen, Ausschlüsse und Favoriten
- eigene Mahlzeiten und gespeicherte Pläne
- Benutzerkonten und geräteübergreifende Nutzung
- Zucker, Ballaststoffe, Salz und Allergene
- Preise, Packungsgrößen, Budgets und Vorräte
- Produkt- und Mahlzeitenbilder
- KI-gestützte, aber niemals selbstständig freigebende Review-Vorschläge
