# Produkt- und Entwicklungs-Roadmap

Stand: 2. September 2026

## Abgeschlossene Produktphasen

| Phase | Ergebnis | Status |
|---|---|---|
| 0 | Produktziel und Zielgruppe beschrieben | abgeschlossen |
| 1 | Fachliche Planungsregeln festgelegt | abgeschlossen |
| 2 | Technischer Stack und Systemgrenzen festgelegt | abgeschlossen |
| 3 | Kuratierter Lebensmittel- und Mahlzeitenkatalog in PostgreSQL | abgeschlossen |
| 4 | Tagesplaner und API | abgeschlossen |
| 5 | Wochenansicht und Einkaufsliste | abgeschlossen |
| 6A | Quellenneutrale Rezept-Inbox und deterministische Normalisierung | abgeschlossen |
| 6B | Kontrollierte Veröffentlichung normalisierter Rezepte | abgeschlossen |

Damit ist der technische MVP abgeschlossen. Der Planer arbeitet ausschließlich
mit dem freigegebenen PostgreSQL-Katalog und benötigt keine externe Datenquelle
zur Laufzeit.

## Behaltener Stand aus der Import-Erkundung

Die Import-Erkundung hat drei dauerhaft brauchbare Bausteine geliefert:

1. Rohrezepte können idempotent und getrennt vom Produktivkatalog gespeichert
   werden.
2. Unvollständige Zutaten und Mengen bleiben hinter einer nachvollziehbaren
   Review-Grenze.
3. Foundation Foods und SR Legacy können als lokaler FDC-Referenzbestand
   gespeichert werden.

Quellenspezifische TheMealDB-Logik, direkte FDC-Einzelrequests, heuristische
Zutatenvorschläge, automatische Food-Materialisierung und die dazugehörigen
internen HTTP-Endpunkte wurden nach der Erkundung entfernt. Sie haben gezeigt,
dass zusätzliche Nährwertdatensätze keine fehlende Zutatenontologie ersetzen.

## Nächster Meilenstein: Recipe-first-MVP

PrepPilot wird zunächst auf einen kleinen vertikalen Produktablauf reduziert:
vollständige Rezepte aus einer Quelle importieren, mit ihren bereits gelieferten
Nährwerten in PostgreSQL speichern und daraus einen Tagesplan erzeugen.

Die Zutatennormalisierung ist keine Voraussetzung mehr für den Planer. Ein
importiertes Rezept wird über seine eigenen Werte pro Portion geplant.
Lebensmittelprofile werden erst wieder eingeführt, wenn eine konkrete spätere
Funktion wie Einkaufsliste, Ausschluss oder Ersetzung sie benötigt.

Die vollständige Abgrenzung und Abnahme steht in
[`recipe-first-mvp.md`](recipe-first-mvp.md).

### Umsetzungsschnitte

1. aktuelle Tabellen und Dienste gegen das neue Ziel klassifizieren
2. zehn echte Kandidaten einer rechtlich kompatiblen Quelle prüfen
3. minimales Rezeptmodell und neue Ausgangsmigration festlegen
4. genau diese Quelle kontrolliert anbinden
5. Planer auf Nährwerte pro Rezeptportion umstellen
6. gespeicherte Rezepte und erzeugte Pläne im Frontend sichtbar machen
7. vollständigen Ablauf automatisiert und im Browser abnehmen

## Nicht Teil des nächsten Schnitts

- Bulk-Scraping kommerzieller Rezeptseiten
- Nährwertberechnung aus einzelnen Zutaten
- Zutatenontologie und Lebensmittelprofile
- Quellen ohne dauerhaft speicherbare Rezept- und Nährwertdaten
- Bilderimport
- regelmäßiger Hintergrundbetrieb
- öffentliche Import- oder Admin-Oberfläche
