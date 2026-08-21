# PrepPilot – Roadmap

Diese Liste ist die gemeinsame Arbeitsgrundlage. Aufgaben werden in Reihenfolge umgesetzt; neue Ideen landen zunächst im Backlog.

## 0. Produktfundament

- [x] Produktversprechen formulieren
- [x] MVP-Nutzerfluss definieren
- [x] MVP gegen spätere Funktionen abgrenzen
- [ ] Erfolgskriterien für das MVP festlegen

## 1. Technisches Fundament

- [ ] Tech-Stack auswählen
- [ ] Architektur und Ordnerstruktur festlegen
- [ ] Entwicklungsumgebung scaffolden
- [ ] Formatierung, Linting und Tests einrichten
- [ ] `.env.example` und Setup-Anleitung ergänzen

## 2. Domänen- und Datenmodell

- [ ] `Food` als normalisierte Lebensmittelidentität modellieren
- [ ] Einheiten und Umrechnungen definieren
- [ ] `InventoryItem` für Vorräte modellieren
- [ ] `Recipe`, `RecipeIngredient` und Portionen modellieren
- [ ] Pflicht-, optionale und ersetzbare Zutaten abbilden
- [ ] Ernährungsformen, Allergene und Nährwerte abbilden
- [ ] Datenbankschema und Migrationen erstellen

## 3. Vorratsverwaltung

- [ ] Vorräte anlegen, bearbeiten und löschen
- [ ] Menge, Einheit und Lagerort erfassen
- [ ] Öffnungs- und Verbrauchsdatum erfassen
- [ ] Grundzutaten als dauerhaft vorhanden markieren
- [ ] Bestände nach dem Kochen reduzieren

## 4. Rezeptdatenbank

- [ ] Rezepte anlegen, bearbeiten und löschen
- [ ] Zutaten strukturiert zuordnen
- [ ] Portionen skalieren
- [ ] Zubereitungszeit, Nährwerte und Tags erfassen
- [ ] Mindestens 20 realistische Beispielrezepte importieren

## 5. Matching-Engine

- [ ] Vorhandene, fehlende und optionale Zutaten bestimmen
- [ ] Mengen bei der Bewertung berücksichtigen
- [ ] Erste nachvollziehbare Score-Formel definieren
- [ ] Bald ablaufende Vorräte höher gewichten
- [ ] Zeit, Ernährung und zusätzliche Einkäufe einbeziehen
- [ ] Begründungen für Empfehlungen erzeugen
- [ ] Matching-Logik mit Unit-Tests absichern

## 6. Nutzeroberfläche

- [ ] Onboarding und Präferenzen
- [ ] Vorratsübersicht
- [ ] Rezept-Ranking mit Match-Score
- [ ] Rezeptdetail mit vorhandenen und fehlenden Zutaten
- [ ] Kochvorgang bestätigen
- [ ] Leere, ladende und fehlerhafte Zustände gestalten
- [ ] Mobile Darstellung optimieren

## 7. Einkaufsliste

- [ ] Fehlende Zutaten übernehmen
- [ ] Doppelte Einträge zusammenfassen
- [ ] Einträge abhaken
- [ ] Eingekaufte Lebensmittel in den Vorrat übernehmen

## 8. MVP-Abnahme

- [ ] Zentralen Nutzerfluss als End-to-End-Test abdecken
- [ ] Barrierefreiheit und Tastaturbedienung prüfen
- [ ] Beispielnutzer durch den vollständigen Ablauf führen
- [ ] Feedback dokumentieren und priorisieren
- [ ] MVP veröffentlichen

## Späterer Backlog

- Wochenpläne über mehrere Rezepte optimieren
- Packungsgrößen und echte Preise berücksichtigen
- Barcode-, Kassenbon- oder Kühlschrank-Scan
- Kalenderintegration
- Haushalte mit mehreren Profilen
- automatische Austauschzutaten
- Import von Rezept-Webseiten

