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

## Nächster Meilenstein: belastbarer Datenbestand

### Abschnitt 1: Zutatenidentität

**Ziel:** Kanonische Lebensmittelkonzepte werden von konkreten
Nährwertprofilen getrennt.

**Aktueller Stand:** Datenmodell, explizite Konzeptzuordnung im kuratierten
Katalog und die eindeutige Registrierung externer Zutatenkennungen sind
implementiert. Jedes konkrete `food` verweist direkt auf sein allgemeineres
Konzept; beispielsweise gehört `milk_1_5` zu `milk`. Eine zusätzliche
Zuordnungstabelle oder eine automatische Standardprofil-Wahl gibt es nicht. Die
PostgreSQL-Abnahme bestätigt nach zwei identischen Seed-Läufen 24 Foods mit 24
direkten Konzeptverknüpfungen. Eine vorhandene Wikibooks-Zuordnung zu Milch
wurde dabei ohne Verlust auf das allgemeinere Konzept migriert. Externe
Zutatenkennungen können einmalig offen
gespeichert, von mehreren Rezepten wiederverwendet und später einem Konzept
zugeordnet werden. Die Zuordnung verarbeitet alle betroffenen Rezeptimporte
erneut; konkurrierende Food-Profile werden weiterhin nicht automatisch gewählt.
Eine lokale interne Frontend-Ansicht zeigt Rezeptimporte, offene Identitäten und
vorhandene Konzepte und erlaubt diese einmalige Zuordnung.

**Abnahme:**

- Eine externe kanonische Zutatenkennung kann genau einem internen Konzept
  zugeordnet werden.
- Ein Konzept kann mindestens ein Nährwertprofil mit Quelle und Zustand tragen.
- Bestehender Planer und kuratierter Katalog funktionieren unverändert weiter.
- Eine ungeklärte Zutat erzeugt genau einen wiederverwendbaren Review-Fall.

### Abschnitt 2: offener Rezeptadapter

**Ziel:** Ein begrenzter Wikibooks-Lauf übersetzt offen lizenzierte Rezepte in
das quellenneutrale Inbox-Format.

**Aktueller Stand:** Der Adapter läuft standardmäßig als schreibfreier Dry Run
und akzeptiert nur Seiten mit eindeutiger Portionszahl, Zutatenliste,
Zubereitung und kanonischen Zutatenlinks. Der erste reale Fünferlauf entdeckte
fünf Seiten, klassifizierte eine als geeignet und vier mit konkreten Gründen als
abgelehnt. Das geeignete Rezept wurde einmal importiert; der identische zweite
Lauf erkannte es als Duplikat. Page-ID, Revision, URL, CC-BY-SA-4.0-Hinweis und
Attribution liegen im Rohdatensatz.

**Abnahme:**

- Der Dry Run weist entdeckte, geeignete und abgelehnte Seiten samt Gründen aus.
- Importiert werden nur Rezepte mit Portionen, Zutaten und Anleitung.
- Seitenkennung, Revision, URL, Lizenz und Attribution bleiben erhalten.
- Kanonische Wikibooks-Zutatenlinks werden als externe Identitäten genutzt.
- Derselbe Lauf erzeugt keine Duplikate.

### Abschnitt 3: kontrollierter Bestandslauf

Erst nach erfolgreicher Abnahme der ersten beiden Abschnitte wird die Laufgröße
erhöht. Unbekannte Konzepte werden nach Häufigkeit priorisiert. Fehlende
Nährwertprofile blockieren nicht die Aufnahme des Rohrezepts, aber weiterhin
dessen Veröffentlichung im Planerkatalog.

## Nicht Teil des nächsten Schnitts

- Bulk-Scraping kommerzieller Rezeptseiten
- automatische Schätzung fehlender Portionen
- automatische Wahl einer beliebigen FDC-Variante
- Bilderimport
- regelmäßiger Hintergrundbetrieb
- öffentliche Import- oder Admin-Oberfläche
