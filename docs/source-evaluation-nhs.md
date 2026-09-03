# Quellenprüfung: NHS Healthier Families

Stand: 2. September 2026

## Ergebnis

NHS Healthier Families ist für den Recipe-first-MVP ein bedingt geeigneter
erster Kandidat. Zehn geprüfte Rezeptseiten enthalten jeweils Titel,
Portionszahl, Zutaten, Zubereitung sowie Kalorien, Protein, Kohlenhydrate und
Fett pro Portion.

Die Rezepte passen fachlich besser zu PrepPilot als die zuerst geprüften
USDA-Kinderrezepte. Die Stichprobe enthält Hauptgerichte mit bis zu 52 Gramm
Protein pro Portion und erzeugt bereits gültige Pläne für das bestehende
Referenzprofil.

## Technisches Format

Ein technischer Abruf aller zehn Seiten am 2. September 2026 bestätigt jeweils
ein `schema.org/Recipe`-JSON-LD mit Titel, Zutaten und Zubereitung. Portionszahl,
Zubereitungszeiten und Nährwerte stehen zusätzlich in einem wiederkehrenden
HTML-Bereich. Es gibt für diesen Bereich keine bestätigte eigene Rezept-API.

Der erste Adapter wäre deshalb ein begrenzter HTML-Importer:

1. ausschließlich zehn fest hinterlegte Rezept-URLs abrufen
2. Titel, Zutaten und Anleitung aus JSON-LD lesen
3. Portionen, Zeiten und vier Makros aus dem Rezeptkopf lesen
4. keine Bilder, Logos, Bewertungen oder Seitennavigation übernehmen
5. extrahierte Daten, Quell-URL, Abrufzeit und Inhalts-Hash speichern

Die kanonische URL dient im ersten Schnitt als externe Rezeptkennung. Ein
identischer Seiteninhalt darf keinen neuen Datensatz erzeugen.

## Stichprobe

Alle Werte sind Angaben pro Portion von der jeweiligen NHS-Seite.

| Rezept | kcal | Protein | Kohlenhydrate | Fett |
|---|---:|---:|---:|---:|
| [Roast chicken dinner](https://www.nhs.uk/healthier-families/recipes/roast-dinner/) | 525 | 52 g | 48 g | 15,5 g |
| [Spaghetti carbonara](https://www.nhs.uk/healthier-families/recipes/pasta-carbonara/) | 409 | 26,5 g | 61 g | 9 g |
| [Bang-tasty chicken drumsticks](https://www.nhs.uk/healthier-families/recipes/roast-chicken-drumsticks/) | 404 | 36 g | 54 g | 6,5 g |
| [Roast chicken breast with peppers](https://www.nhs.uk/healthier-families/recipes/roast-chicken-breast-with-peppers/) | 384 | 42 g | 48 g | 4 g |
| [Sweet and sour chicken](https://www.nhs.uk/healthier-families/recipes/sweet-and-sour-chicken/) | 295 | 21 g | 45 g | 5 g |
| [Brilliant beef curry](https://www.nhs.uk/healthier-families/recipes/brilliant-beef-curry/) | 384 | 22 g | 67 g | 3,5 g |
| [Classic cottage pie](https://www.nhs.uk/healthier-families/recipes/classic-cottage-pie/) | 363 | 25,5 g | 49,7 g | 5,3 g |
| [Salmon and broccoli pasta](https://www.nhs.uk/healthier-families/recipes/salmon-and-broccoli-pasta/) | 465 | 34,2 g | 45,9 g | 13,8 g |
| [Super scrambled eggs](https://www.nhs.uk/healthier-families/recipes/super-scrambled-eggs/) | 255 | 17 g | 19 g | 13 g |
| [Sausage, tomato and butter bean bake](https://www.nhs.uk/healthier-families/recipes/sausage-tomato-butter-bean-bake/) | 296 | 21,5 g | 30,8 g | 7,2 g |

## Planbarkeit

Eine rein lesende Kombinationsprüfung verwendete fünf unterschiedliche
Rezepte und je eine oder zwei ganze Portionen. Für das Referenzprofil mit
2.500 kcal, mindestens 220 g Protein, höchstens 71 g Fett und 233 g
Kohlenhydraten entstanden 20 gültige Kombinationen.

Eine der Kombinationen erreicht:

- 2.502 kcal
- 225,5 g Protein
- 278 g Kohlenhydrate
- 63,5 g Fett

Damit ist die Stichprobe ausreichend, um den vertikalen Planungsablauf zu
entwickeln. Ob zwei Portionen eines konkreten Rezepts praktisch sinnvoll sind,
wird im Frontend sichtbar gemacht und später mit Nutzern validiert.

## Lizenz und Attribution

Die [allgemeinen NHS-Bedingungen](https://www.nhs.uk/our-policies/terms-and-conditions/)
stellen Website-Inhalte grundsätzlich unter die Open Government Licence,
einschließlich kommerzieller Nutzung und Bearbeitung. Ausgenommen sind
insbesondere Bilder, Logos, Marken und
[kenntlich gemachtes Drittmaterial](https://www.nhs.uk/our-policies/terms-and-conditions/content-not-licensed-for-re-use/).

Für PrepPilot folgt daraus als technische Produktregel:

- keine NHS-Bilder oder Logos importieren
- jede Rezeptseite als Quelle verlinken
- Lizenz `Open Government Licence v3.0` speichern und sichtbar nennen
- den vorgeschriebenen Attributionstext im Produkt anzeigen
- Abrufdatum und Inhalts-Hash speichern
- Änderungen der NHS-Nutzungsbedingungen vor einem öffentlichen Release erneut
  prüfen

Diese Prüfung ist eine technische Quellenbewertung und keine Rechtsberatung.

## Entscheidung für den ersten Schnitt

Der erste Import bleibt auf die zehn geprüften URLs begrenzt. Es findet kein
offenes Crawling der NHS-Website statt. Erst wenn Import, Speicherung, Planung
und Anzeige vollständig funktionieren, wird über weitere NHS-Rezepte
entschieden.

## Kontrollierte Erweiterung auf 20 Rezepte

Nach der Abnahme des ersten Schnitts wurden 19 weitere Hauptgericht-Kandidaten
aus der offiziellen NHS-Rezeptübersicht technisch geprüft. Zehn davon erweitern
den festen Bestand zunächst auf insgesamt 20 Rezepte:

| Rezept | kcal | Protein | Kohlenhydrate | Fett |
|---|---:|---:|---:|---:|
| Bajan cou cou with spicy fish | 410 | 37,3 g | 48 g | 5,2 g |
| Baked potatoes with mince | 306 | 20,6 g | 44,4 g | 3,5 g |
| Bengali-style chicken curry | 428 | 26 g | 62 g | 7 g |
| Caribbean tofu and sweet potato curry | 440 | 14,9 g | 51 g | 12,7 g |
| Chilli con carne | 488 | 30 g | 82 g | 5 g |
| Crunchy fish fingers with wedges | 416 | 34 g | 56 g | 2 g |
| Falafel | 371 | 16,9 g | 56,5 g | 6,3 g |
| Healthier full English breakfast | 262 | 20 g | 19 g | 13 g |
| Meat-free cottage pie | 345 | 20 g | 52 g | 6 g |
| Prawn jambalaya | 342 | 17,9 g | 59,3 g | 2,7 g |

Alle zehn Seiten liefern dieselben Pflichtfelder und jeweils 4 bis 7 sichtbare
Methodenschritte. Ein zweiter Prüflauf vermeidet weiterhin Duplikate.

„Chicken jalfrezi“ wurde bewusst nicht aufgenommen: Die Quellseite nennt 334
kcal und gleichzeitig 79 g Fett pro Portion. Diese Angaben sind energetisch
widersprüchlich. Der Importer lehnt solche Fälle künftig automatisch ab.

Bei fünf Mahlzeiten entstehen mit 20 Rezepten rechnerisch knapp 500.000
Rezept-Portions-Kombinationen. Der Planer verwirft Rezeptgruppen vor der
Portionssuche, wenn sie die äußeren Nährwertgrenzen nachweislich nicht erreichen
können, und hält nur die drei besten Treffer im Speicher. Vor einer weiteren
Katalogvergrößerung mussten Kategorien zusätzlich die Planvielfalt steuerbar
machen.

## Ausgewogene Erweiterung auf 33 Rezepte

Der zweite kontrollierte Ausbau ergänzt sechs Frühstücks- und sieben
Mittagsrezepte aus den offiziellen NHS-Sammlungen. Zusammen mit dem bestehenden
Katalog stehen damit 8 Frühstücke, 8 Mittagessen und 17 Abendessen zur Verfügung.
Alle 13 neuen Seiten wurden vor der Freigabe mit denselben Pflichtfeldern,
Nährwertprüfungen und lesbaren Zubereitungsschritten validiert.

Eine freie Kombination aller 33 Rezepte benötigte für das Referenzprofil rund
24 Sekunden. Die feste Auswahl aus genau einem Frühstück, einem Mittagessen und
einem Abendessen begrenzt den Suchraum fachlich nachvollziehbar. Snacks werden
später als eigene Kategorie ergänzt.
