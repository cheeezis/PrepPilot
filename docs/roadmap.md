# Produkt-Roadmap

Stand: 21. August 2026

Diese Roadmap beschreibt überprüfbare Produktergebnisse. Sie legt noch keinen
Tech-Stack und keine Architektur fest. Eine Phase beginnt erst, wenn die
Abnahmekriterien der vorherigen Phase erfüllt sind.

## Phase 0: Produktgrundlage

Ziel: Das zu lösende Problem und die Grenze des ersten Produkts sind eindeutig.

- Problemstatement, Zielgruppe und Produktversprechen festhalten
- primären Nutzerfluss definieren
- MVP und bewusste Nicht-Ziele abgrenzen
- messbare Erfolgskriterien formulieren

Abnahme: Die Produktdefinition in `docs/product.md` ist bestätigt.

Status: abgeschlossen

## Phase 1: Fachliches Planungsmodell

Ziel: Vor technischem Aufbau ist anhand konkreter Beispiele nachweisbar, was
ein gültiger und praktikabler Tagesplan ist.

Status: in Bearbeitung

- repräsentative Nutzerprofile mit Tageszielen und drei bis sechs Mahlzeiten
  definieren
- Zielbereiche und Prioritäten für Kalorien, Protein, Fett und Kohlenhydrate
  konkretisieren
- Mahlzeitentypen und praktikable Portionsvarianten festlegen
- Regeln für nicht oder nur teilweise erfüllbare Ziele bestimmen
- einen kleinen Beispieldatensatz manuell durchplanen

Abnahme: Für jedes Testprofil lässt sich eindeutig entscheiden, welcher Plan
gültig ist, wie Vorschläge verglichen werden und welche Abweichung angezeigt
wird.

## Phase 2: Kataloggrundlage

Ziel: Ein kleiner Katalog deckt die benötigten Mahlzeitentypen und Zielbereiche
mit verlässlichen Daten ab.

- Qualitätsanforderungen für Mahlzeiten, Zutaten, Mengen und Nährwerte festlegen
- Frühstücke, Hauptgerichte, Snacks, Brotmahlzeiten und Shakes kuratieren
- Daten auf einheitliche Einheiten und vollständige Nährwerte prüfen
- Herkunft und Nutzungsrechte jedes Inhalts dokumentieren
- Abdeckung gegen die Testprofile aus Phase 1 prüfen

Abnahme: Der Katalog kann für jedes unterstützte Testprofil mindestens zwei
praktikable Tagespläne bilden und ist ohne Live-API verfügbar.

## Phase 3: Planbarer Produktkern

Ziel: Der vollständige Kernfluss funktioniert mit echten Katalogdaten.

- Tagesziele und Mahlzeitenanzahl erfassen
- zwei bis drei nachvollziehbare Tagespläne erzeugen
- Mahlzeiten, Portionsmengen, Tageswerte und Abweichungen darstellen
- einen Vorschlag auswählen
- fachliche Regeln und Grenzfälle automatisiert prüfen

Abnahme: Alle vereinbarten Testprofile liefern reproduzierbare Ergebnisse und
der Nutzer kann einen Tagesplan ohne zusätzliche Berechnung auswählen.

## Phase 4: Wochenplan und Einkauf

Ziel: Aus dem gewählten Tagesplan entsteht ein praktisch nutzbarer Wocheneinkauf.

- Tagesplan für sieben Tage darstellen
- Zutaten über alle Mahlzeiten und Tage korrekt aggregieren
- Einheiten und Mengen verständlich ausgeben
- Einkaufsliste mobil nutzbar machen
- vollständigen primären Nutzerfluss testen

Abnahme: Ein Testnutzer erstellt in höchstens drei Minuten einen Plan und kann
die ausgegebene Einkaufsliste ohne externen Rechner verwenden.

## Phase 5: MVP-Validierung

Ziel: Reale Nutzung entscheidet, ob der Produktkern trägt.

- mehrere Zielnutzer einen realen Wochenplan erstellen lassen
- Verständlichkeit, Vertrauen, Planqualität und tatsächliche Nutzbarkeit
  beobachten
- Abbrüche und manuelle Korrekturen erfassen
- Erfolgskriterien aus der Produktdefinition auswerten
- nur die wichtigsten Probleme vor einer Erweiterung beheben

Abnahme: Nutzer bewerten mindestens einen erzeugten Plan als praktisch genug
für einen realen Wochenversuch. Rechenfehler und blockierende Probleme sind
behoben.

## Phase 6: Wochenvielfalt

Ziel: PrepPilot entwickelt sich vom wiederholten Tagesplan zu einem flexiblen
Wochenplan.

- mehrere unterschiedliche Tagespläne zulassen
- gewünschte Wiederholung und Abwechslung steuerbar machen
- einzelne Mahlzeiten austauschbar machen, ohne Tagesziele aus dem Blick zu
  verlieren
- Einkaufsliste für gemischte Wochenpläne aktualisieren

Abnahme: Nutzer erhalten mehr Abwechslung, ohne dass Planung und Einkauf
spürbar komplizierter werden.

## Phase 7: Personalisierung

Ziel: Häufig bestätigte persönliche Anforderungen werden unterstützt.

Mögliche Themen sind Ernährungsformen, Ausschlüsse, Favoriten, eigene
Mahlzeiten, Vorlagen und gespeicherte Pläne. Ihre Reihenfolge wird erst anhand
des MVP-Feedbacks festgelegt.

## Phase 8: Erweiterte Einkaufsplanung

Ziel: Nur bei nachgewiesenem Bedarf werden Haushalt und Kosten stärker
berücksichtigt.

Mögliche Themen sind Vorräte, Packungsgrößen, Preise und Budget. Externe APIs
und optionale KI-Funktionen werden jeweils als eigenständige Produktentscheidung
bewertet und dürfen den verlässlichen Kernfluss nicht voraussetzen.

## Nächster Entscheidungspunkt

Für Phase 1 und die fachliche Vorbereitung des Katalogs werden Tech-Stack und
Architektur noch nicht benötigt. Die nächste Arbeit ist fachlich: konkrete
Testprofile, Toleranzen und Kataloganforderungen festlegen. Erst wenn diese
Regeln belastbar sind, wird eine technische Architektur gewählt.
