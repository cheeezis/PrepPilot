# Produktdefinition

Stand: 25. August 2026

## Vision

PrepPilot übersetzt tägliche Kalorien- und Makroziele in einen vollständigen,
praktisch umsetzbaren Ernährungsplan mit passender Einkaufsliste.

Langfristig plant PrepPilot eine abwechslungsreiche Woche aus mehreren
Mahlzeiten pro Tag. Persönliche Rahmenbedingungen wie Ernährungsformen,
Ausschlüsse, eigene Rezepte, Vorräte und Budget können später berücksichtigt
werden. Der feste Mittelpunkt bleibt die Ernährungsplanung; PrepPilot soll kein
allgemeiner Kalorientracker, Rezeptportal oder Haushaltsmanager werden.

## Problemstatement

Menschen mit täglichen Kalorien- und Makrozielen wissen häufig, wie viel sie
essen möchten. Die Übersetzung dieser Ziele in zusammenpassende Mahlzeiten,
praktikable Mengen und einen vollständigen Wocheneinkauf erfordert jedoch viel
manuelle Suche und Berechnung.

## Zielgruppe

Die erste Zielgruppe ist eine Einzelperson, die:

- ihre Ernährung anhand von Kalorien und Makronährstoffen plant,
- mehrere Mahlzeiten am Tag isst und für mehrere Tage vorbereitet,
- aktuell Rezepte, Nährwertangaben, Mengenberechnung und Einkaufsliste manuell
  kombiniert,
- keine Allergien oder besondere Ernährungsform berücksichtigt haben muss.

## Produktversprechen

> Gib deine täglichen Kalorien- und Makroziele an und erhalte einen
> vollständigen, praktisch portionierten Tagesplan samt Einkaufsliste für die
> Woche.

## Fachliche Leitlinien

Eine Mahlzeit muss kein klassisches Kochrezept sein. Gekochte Gerichte,
Brotmahlzeiten, Skyr, Shakes und einfache Snacks werden gemeinsam als
Mahlzeiten behandelt. Jede Mahlzeit besitzt definierte Lebensmittel, Mengen,
Nährwerte, einen Mahlzeitentyp und praktikable Portionsvarianten.

Die Planung bewertet die gesamte Tagesbilanz. Nutzer müssen keine Zielwerte je
Mahlzeit festlegen.

- Kalorien werden innerhalb eines Zielbereichs optimiert.
- Protein wird als Mindestwert behandelt.
- Fett erhält einen Zielbereich.
- Kohlenhydrate sind der flexibelste Wert.
- Abweichungen werden sichtbar und verständlich ausgewiesen.
- Praktikable Mengen sind wichtiger als rechnerische Perfektion.
- Die Planung ist im MVP deterministisch und nachvollziehbar.

Die anfänglichen Toleranzen stehen in `docs/planning-rules.md`. Welche Zielwerte
der kuratierte Katalog zuverlässig abdeckt, wird während der Daten- und
Planungsphasen praktisch überprüft.

## Primärer Nutzerfluss

1. Der Nutzer gibt sein tägliches Ziel für Kalorien, Protein, Fett und
   Kohlenhydrate an.
2. Er wählt die Anzahl der Mahlzeiten pro Tag. Das MVP unterstützt zunächst
   drei bis sechs Mahlzeiten; fünf sind der Standardwert.
3. PrepPilot erstellt zwei bis drei passende vollständige Tagespläne.
4. Der Nutzer vergleicht Mahlzeiten, Mengen, Tageswerte und sichtbare
   Abweichungen und wählt einen Plan aus.
5. PrepPilot wiederholt diesen Tagesplan für sieben Tage.
6. Der Nutzer öffnet die aggregierte Einkaufsliste für die Woche.

## MVP-Umfang

### Kernfunktionen

- Tagesziele für Kalorien, Protein, Fett und Kohlenhydrate erfassen
- drei bis sechs Mahlzeiten pro Tag wählen
- zwei bis drei Tagespläne deterministisch aus einem kuratierten Katalog
  erzeugen
- praktikable Portionsvarianten und Nährwerte pro Mahlzeit anzeigen
- Tagesbilanz und Zielabweichungen anzeigen

### Unterstützende Funktionen

- kleinen kuratierten Katalog aus Frühstücken, Hauptgerichten, Snacks,
  Brotmahlzeiten und Shakes bereitstellen
- ausgewählten Tagesplan siebenmal als Wochenplan verwenden
- Zutatenmengen für die Woche korrekt aggregieren
- Einkaufsliste auf mobilen und größeren Bildschirmen nutzbar darstellen

## Erfolgskriterien

Das MVP gilt als erfolgreich, wenn:

- ein neuer Nutzer ohne Erklärung in höchstens drei Minuten einen Plan samt
  Einkaufsliste erstellen kann,
- für die ausdrücklich unterstützten Zielbereiche mindestens zwei gültige
  Tagespläne erzeugt werden,
- Kalorien und Fett innerhalb der festgelegten Toleranzen liegen,
- das Protein-Mindestziel erreicht oder eine Abweichung deutlich erklärt wird,
- Mengen realistisch und ohne zusätzliche Berechnung verwendbar sind,
- Nährwerte und Wocheneinkaufsliste rechnerisch zum gewählten Plan passen,
- Testnutzer den erzeugten Plan als praktisch genug für einen realen
  Wochenversuch bewerten.

Während Katalog und Planungslogik entstehen, werden konkrete Testprofile für
unterschiedliche Zielwerte und drei bis sechs Mahlzeiten ergänzt. Diese Profile
bilden die technische und fachliche Abnahme der Planungslogik.

## Bewusste Nicht-Ziele des MVP

- sieben unterschiedliche Tagespläne oder frei konfigurierbare Wochenvielfalt
- Allergien oder medizinische Ernährungsberatung
- vegetarische, vegane oder andere Ernährungsfilter
- persönliche Ausschlusszutaten und Geschmackspräferenzen
- Benutzerkonten oder geräteübergreifende Synchronisation
- eigene Rezepte und Rezeptverwaltung durch Nutzer
- Vorratsverwaltung
- Preise, Packungsgrößen oder Budgetoptimierung
- Live-Abhängigkeit von einer externen Rezept- oder Nährwert-API
- automatische Nährwertberechnung
- KI-generierte Rezepte oder Pläne
- exaktes Treffen jedes einzelnen Makrowerts
- native mobile Anwendungen

## Katalogstrategie

Das MVP verwendet einen kleinen, lokal verfügbaren und fachlich geprüften
Lebensmittel- und Mahlzeitenkatalog. Der interne Lebensmittelkatalog kombiniert
zwei Arten von Einträgen:

- wenige markenspezifische Produkte werden manuell und exakt erfasst,
- generische Lebensmittel werden aus geeigneten externen Datenquellen
  übernommen.

Externe Daten werden vor ihrer Verwendung importiert, vereinheitlicht und
fachlich geprüft. Erst freigegebene Einträge dürfen für die Planerstellung
verwendet werden. Jeder Eintrag hält seine Herkunft und den Stand der
übernommenen Daten fest.

Eine externe API ist damit eine mögliche Importquelle, aber keine
Laufzeitvoraussetzung der Planung. Vor einer Übernahme externer Inhalte müssen
Nutzungsrechte, Speicherung, Attribution, Nährwertqualität und metrische Mengen
geklärt sein. Konkrete Anbieter sind noch nicht ausgewählt.

## Spätere Produktentwicklung

Nach erfolgreicher MVP-Validierung kann PrepPilot schrittweise erweitern:

- mehrere unterschiedliche Tagespläne und steuerbare Wiederholungen,
- Ernährungsformen, Ausschlüsse und Favoriten,
- eigene Mahlzeiten und wiederverwendbare Vorlagen,
- Austausch einzelner Mahlzeiten bei fortbestehenden Tageszielen,
- flexible Mahlzeiten- oder Snack-Slots mit reserviertem Makro-Budget,
- Vorräte, Packungsgrößen, Preise und Budget,
- Rezeptimport und automatische Nährwertberechnung,
- optionale KI-Unterstützung.

Diese Punkte sind keine Zusage für die Umsetzung. Ihre Priorität richtet sich
nach der Nutzung und dem Feedback zum vorherigen Produktstand.

## Noch zu entscheiden

Erst vor Beginn der jeweiligen Umsetzung werden festgelegt:

- konkrete Toleranzen und unterstützte Makro-Zielbereiche,
- Größe, Herkunft und Qualitätskriterien des Startkatalogs,
- erlaubte Portionsvarianten je Mahlzeit,
- ergänzende Technologien, Architekturdetails und Deployment-Ziel.
