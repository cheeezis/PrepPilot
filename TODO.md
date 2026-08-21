# PrepPilot – Roadmap

Diese Liste ist die gemeinsame Arbeitsgrundlage. Aufgaben werden grundsätzlich
in Reihenfolge umgesetzt; neue Ideen landen zunächst im Backlog.

## 0. Produktkern und MVP

PrepPilot verbindet langfristig zwei Modi:

1. **Zielgerichtet optimieren:** Ein Gericht auf Portionen, Kalorien, Protein
   und Budget anpassen.
2. **Aus dem Vorrat kochen:** Vorhandene und bald ablaufende Lebensmittel mit
   passenden Rezepten abgleichen.

Der Optimierer ist der primäre MVP-Nutzerfluss:

`Ziele eingeben → Gericht wählen → Mengen optimieren → Ergebnis prüfen → Einkaufsliste`

Das MVP gilt als erfolgreich, wenn für mindestens ein realistisches Gericht
deterministisch geeignete Zutatenmengen berechnet werden und Nährwerte, Kosten,
Zielabweichungen sowie die daraus entstehende Einkaufsliste nachvollziehbar
dargestellt werden. Der Vorrat wird bei Bedarf von den Einkaufsmengen abgezogen.

- [x] Produktversprechen formulieren
- [x] Optimierung und Vorrats-Matching als verbundene Produktmodi festlegen
- [x] Primären MVP-Nutzerfluss definieren
- [x] KI auf Import und Interpretation begrenzen; Berechnungen deterministisch halten
- [ ] Konkrete MVP-Erfolgskriterien mit einem Referenzgericht abnehmen

## 1. Technisches Fundament

- [x] Next.js, React, TypeScript und SQLite für den lokalen MVP einrichten
- [x] Architektur und Ordnerstruktur festlegen
- [x] Linting, TypeScript-Prüfung und Unit-Tests einrichten
- [x] Migrationen, Seed-Daten und lokale Setup-Anleitung ergänzen
- [ ] Automatische Formatierung einrichten
- [ ] Entscheidung über einen separaten Python-Optimierungsservice treffen
- [ ] PostgreSQL erst für Mehrbenutzerbetrieb und Deployment einführen

## 2. Vorhandenes Produktfundament

- [x] Lebensmittel, Einheiten und Umrechnungen modellieren
- [x] Rezepte, Zutaten, Portionen und optionale Zutaten modellieren
- [x] Fünf strukturierte Beispielrezepte anlegen
- [x] Vorräte anlegen, anzeigen, bearbeiten, löschen und zusammenführen
- [x] Rezept-Ranking aus vorhandenen Vorräten erzeugen
- [x] Fehlende Zutaten auf eine Einkaufsliste übernehmen
- [x] Einkäufe abhaken und in den Vorrat übernehmen
- [x] Bestände nach dem Kochen reduzieren

## 3. Optimierungsfähige Lebensmitteldaten

- [x] Bezugsmenge für Nährwert- und Preisdaten definieren
- [x] Kalorien, Protein, Kohlenhydrate und Fett pro Lebensmittel modellieren
- [x] Preis, Packungsgröße und kaufbare Einheit modellieren
- [x] Quelle und Stand der Nährwert- und Preisdaten speichern
- [x] Validierung für unvollständige oder widersprüchliche Daten ergänzen
- [x] Datenbankschema und Migration erstellen
- [x] Lebensmittel eines Referenzgerichts mit realistischen Daten ausstatten

## 4. Optimierungsfähige Rezepte

- [ ] Zutaten als fest, skalierbar oder optimierbar kennzeichnen
- [ ] Sinnvolle Mindest- und Höchstmengen pro Zutat definieren
- [ ] Zutatenrollen wie Proteinquelle, Kohlenhydratquelle, Gemüse und Fett abbilden
- [ ] Grundmengen zuverlässig auf eine gewünschte Portionszahl skalieren
- [ ] Ein Referenzgericht vollständig für die Optimierung kalibrieren
- [ ] Kulinarisch unsinnige Mengen durch Grenzen verhindern

## 5. Deterministische Berechnungs- und Optimierungsengine

- [ ] Eingabeschema für Portionen, Kalorien, Protein, Makros und Budget definieren
- [x] Nährwerte pro Zutat, Gesamtgericht und Portion berechnen
- [ ] Kosten pro Zutat, Gesamtgericht und Portion berechnen
- [ ] Benötigte Packungsanzahl und tatsächliche Einkaufskosten berechnen
- [ ] Harte Bedingungen für Protein, Budget und ausgeschlossene Zutaten umsetzen
- [ ] Zielabweichungen für Kalorien, Fett und Kohlenhydrate bewerten
- [ ] Optimierungsmodus „nah am Kalorienziel“ implementieren
- [ ] Optimierungsmodus „möglichst günstig“ implementieren
- [ ] Optimierungsmodus „möglichst proteinreich“ implementieren
- [ ] Optimierungsmodus „ausgewogener Kompromiss“ implementieren
- [ ] Nicht erfüllbare Zielkombinationen erkennen und erklären
- [ ] Ergebnisse reproduzierbar und nachvollziehbar begründen
- [ ] Berechnungen und Optimierung umfassend mit Unit-Tests absichern

## 6. Optimierer-Oberfläche

- [ ] Formular für Portionszahl und Ernährungsziele erstellen
- [ ] Kalorienziel und Proteinminimum erfassen
- [ ] Optionale Fett-, Kohlenhydrat- und Budgetgrenzen erfassen
- [ ] Unverträglichkeiten und ausgeschlossene Zutaten berücksichtigen
- [ ] Gespeichertes Gericht auswählen
- [ ] Optimierungsmodus auswählen
- [ ] Ursprüngliche und optimierte Zutatenmengen vergleichen
- [ ] Nährwerte und Zielerreichung pro Portion darstellen
- [ ] Gesamt- und Portionskosten darstellen
- [ ] Packungsgrößen und Einkaufsmenge darstellen
- [ ] Aufteilung des fertigen Gerichts auf Portionen erklären
- [ ] Lade-, Fehler- und nicht erfüllbare Zustände gestalten

## 7. Verbindung mit Vorrat und Einkaufsliste

- [x] Vorhandene, fehlende und optionale Zutaten bestimmen
- [x] Mengen und kompatible Einheiten berücksichtigen
- [x] Bald ablaufende Vorräte im Rezept-Ranking höher gewichten
- [x] Erklärbare Match-Begründungen erzeugen
- [x] Einkaufsliste zusammenführen, abhaken und einräumen
- [ ] Optimierte statt ursprünglicher Rezeptmengen für das Matching verwenden
- [ ] Vorhandene Vorratsmengen von der optimierten Einkaufsliste abziehen
- [ ] Packungsgrößen beim Einkauf berücksichtigen
- [ ] Optimierte Mengen nach dem Kochen aus dem Vorrat abbuchen
- [ ] Zwischen „Ziele optimieren“ und „Aus Vorrat kochen“ wechseln können

## 8. Rezeptverwaltung und Import

- [ ] Rezepte anlegen, bearbeiten und löschen
- [ ] Mindestens 20 realistische und kalibrierte Beispielrezepte bereitstellen
- [ ] Rezepttext deterministisch in strukturierte Felder überführen
- [ ] Rezeptlinks importieren
- [ ] KI-gestützte Interpretation mit Bestätigungsansicht ergänzen
- [ ] Nährwert- und Mengenangaben vor dem Speichern validieren

## 9. Qualität und MVP-Abnahme

- [ ] Zentralen Optimierungsfluss als End-to-End-Test abdecken
- [ ] Vorrats- und Einkaufsfluss als End-to-End-Test abdecken
- [ ] Mobile Darstellung prüfen und verbessern
- [ ] Barrierefreiheit und Tastaturbedienung prüfen
- [ ] Referenzfall „6 Portionen, 900 kcal, 65 g Protein“ abnehmen
- [ ] Ergebnisse gegen eine unabhängige Kontrollrechnung prüfen
- [ ] Beispielnutzer durch beide Produktmodi führen
- [ ] Feedback dokumentieren und priorisieren

## 10. Veröffentlichung

- [ ] Nutzer- und Haushaltskonzept festlegen
- [ ] Produktionsdatenbank und Backups einrichten
- [ ] Docker und CI/CD ergänzen
- [ ] Datenschutz, Quellenangaben und rechtliche Hinweise prüfen
- [ ] MVP veröffentlichen

## Späterer Backlog

- Wochenpläne über mehrere Gerichte gemeinsam optimieren
- eigene Supermarktpreise und Preisverläufe
- Barcode-, Kassenbon- oder Kühlschrank-Scan
- automatische Austauschzutaten
- persönliche Bewertungen und lernende Präferenzen
- Kalenderintegration
- Haushalte mit mehreren Profilen
