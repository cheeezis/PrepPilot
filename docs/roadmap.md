# Produkt- und Entwicklungs-Roadmap

Stand: 3. September 2026

## Aktueller Stand: Recipe-first-MVP

Der frühere Lebensmittel-, Normalisierungs- und Import-Inbox-Ansatz wurde durch
einen kleinen vertikalen Rezeptablauf ersetzt.

| Schnitt | Ergebnis | Status |
|---|---|---|
| Quellenprüfung | zehn geeignete NHS-Rezepte und Nutzungsbedingungen geprüft | abgeschlossen |
| Datenmodell | eine fachliche Tabelle `recipes` | abgeschlossen |
| Datenbank | alte lokale Tabellen entfernt und neue Basismigration ausgeführt | abgeschlossen |
| Import | begrenzter, validierender und idempotenter NHS-Import | abgeschlossen |
| Planung | Kombination gespeicherter Rezeptmakros mit ganzen Portionen | abgeschlossen |
| Frontend | Import, Rezeptbestand, Rezeptdetails und Tagespläne sichtbar | abgeschlossen |
| Abnahme | Backend-, Frontend- und Browsertests | abgeschlossen |
| Technische Rezeptqualität | zehn Rezepte vollständig und Methodenschritte lesbar getrennt | abgeschlossen |
| Katalogerweiterung | 33 NHS-Rezepte ausgewogen und kontrolliert geprüft | abgeschlossen |
| Quellkategorien | NHS-Kategorien gespeichert und im Rezeptbestand filterbar | abgeschlossen |

Der aktuelle Ablauf und seine Grenzen stehen in
[`recipe-first-mvp.md`](recipe-first-mvp.md).

## Nächster Produktabschnitt

1. Rezeptübersicht mit weiteren Nutzern auf Verständlichkeit prüfen
2. feste Tagesstruktur aus Frühstück, Mittagessen und Abendessen bewerten
3. erst nach Bewertung der Planvielfalt weitere NHS-Rezepte aufnehmen

## Später

- zweite rechtlich kompatible Rezeptquelle
- Nutzerimport einzelner Rezept-URLs
- Ernährungsformen, Ausschlüsse und Favoriten
- Snacks als eigene Kategorie und optionale zusätzliche Mahlzeiten
- normalisierte Zutaten für Filter und Einkaufslisten
- Lebensmittelprofile für eigene Rezepte und Ersetzungen
- Benutzerkonten und gespeicherte Pläne

Die früheren technischen Phasen bleiben über die Git-Historie nachvollziehbar,
bestimmen aber nicht mehr die aktuelle Architektur.
