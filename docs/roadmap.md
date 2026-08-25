# Produkt- und Entwicklungs-Roadmap

Stand: 25. August 2026

Diese Roadmap führt PrepPilot von der Produktidee zu einem validierten Minimum
Viable Product (MVP), also der kleinsten sinnvoll nutzbaren Produktversion, und
anschließend zu möglichen Erweiterungen. Die Phasen bauen aufeinander auf. Eine
Phase gilt erst als abgeschlossen, wenn ihr überprüfbares Abnahmekriterium
erfüllt ist.

Der MVP umfasst die Phasen 0 bis 6. Nach Phase 5 ist die erste Version nutzbar;
Phase 6 prüft mit realen Nutzern, ob sie das Produktversprechen tatsächlich
erfüllt. Erweiterungen ab Phase 7 werden erst danach priorisiert.

## Aktueller Stand

| Phase | Ergebnis | Status |
| --- | --- | --- |
| 0 | Produkt klar ausgerichtet | abgeschlossen |
| 1 | Regeln für einen guten Tagesplan festgelegt | abgeschlossen |
| 2 | Technisches Grundgerüst lauffähig | ausstehend |
| 3 | Lebensmittel- und Mahlzeitendaten verfügbar | ausstehend |
| 4 | Tagesplaner nutzbar | ausstehend |
| 5 | Wochenplan und Einkaufsliste nutzbar | ausstehend |
| 6 | MVP mit Zielnutzern validiert | ausstehend |
| 7 | Abwechslungsreiche Wochenplanung | später |
| 8 | Personalisierung und erweiterter Einkauf | später |

## Phase 0: Produkt ausrichten

**Ziel:** Es ist eindeutig, für wen PrepPilot welches Problem löst und was der
erste Produktumfang bewusst nicht leistet.

**Umfang:**

- Problemstatement, Zielgruppe und Produktversprechen festlegen
- primären Nutzerfluss definieren
- MVP und bewusste Nicht-Ziele abgrenzen
- messbare Erfolgskriterien formulieren

**Abnahme:** Die Produktdefinition in `docs/product.md` ist gemeinsam bestätigt.

**Status:** abgeschlossen

## Phase 1: Regeln für einen guten Tagesplan festlegen

**Ziel:** Vor der technischen Umsetzung ist verständlich, wann ein Tagesplan
gültig, praktikabel oder nur eine Annäherung ist.

**Umfang:**

- ein reales Referenzprofil mit Tageszielen und Mahlzeitenanzahl definieren
- Referenzprofile für drei bis sechs Mahlzeiten definieren
- harte und weiche Regeln für Kalorien und Makronährstoffe unterscheiden
- grundlegende Mahlzeitenrollen beschreiben
- grundlegende Portionsskalierung und Größenordnung der Mahlzeiten festlegen
- Priorität von Protein, Kalorien, Fett und Kohlenhydraten festlegen
- zulässige Annäherungen, Ausschlussgrenzen und ihre Reihenfolge festlegen
- Rundungs- und Transparenzregeln bestimmen

**Abnahme:** Nährwertsummen und Mahlzeitenstrukturen können anhand von
`docs/planning-rules.md` eindeutig als gültig, Annäherung oder unbrauchbar
bewertet und nachvollziehbar geordnet werden. Die Regeln reichen aus, um
Datenmodell und Planungslogik zu entwickeln. Datenabhängige Details dürfen in
den dafür vorgesehenen Entwicklungsphasen überprüft und angepasst werden.

**Status:** abgeschlossen

Konkrete Grundportionen und Katalogkategorien folgen in Phase 3. Weitere
Zielprofile und Grenzfälle werden zusammen mit der Planungslogik in Phase 4
getestet.

## Phase 2: Technisches Grundgerüst aufbauen

**Ziel:** Frontend, Backend und Datenbank bilden ein reproduzierbares, testbares
Fundament, ohne bereits Produktfunktionen vorwegzunehmen.

**Umfang:**

- ergänzende Entwicklungswerkzeuge und unterstützte Versionen auswählen
- minimale Monorepo-Struktur für Frontend und Backend festlegen
- React-/TypeScript-Frontend lokal starten
- FastAPI-Backend lokal starten
- PostgreSQL lokal bereitstellen und mit dem Backend verbinden
- einen einfachen Systemcheck zwischen Frontend, Backend und Datenbank einrichten
- grundlegende Formatierung, Typprüfung und Tests ausführbar machen
- lokale Einrichtung nachvollziehbar dokumentieren

**Abnahme:** Nach einer frischen Einrichtung lassen sich alle drei
Anwendungsteile starten. Das Frontend erreicht den Backend-Systemcheck, das
Backend erreicht PostgreSQL und alle grundlegenden Qualitätsprüfungen bestehen.

**Status:** ausstehend

Bestätigte Architekturentscheidungen stehen in `docs/architecture.md`.

## Phase 3: Daten- und Kataloggrundlage schaffen

**Ziel:** PrepPilot besitzt einen kleinen, verlässlichen internen Datenbestand,
aus dem sich realistische Tagespläne bilden lassen.

**Umfang:**

- Lebensmittel, Nährwerte, Mahlzeiten, Zutaten und Portionen modellieren
- Datenbanktabellen und nachvollziehbare Migrationen anlegen
- generische und markenspezifische Lebensmittel unterscheiden
- Anforderungen an Datenqualität, Einheiten, Herkunft und Freigabe festlegen
- externe Datenquellen fachlich und rechtlich bewerten
- einen kleinen Katalog aus einfachen Mahlzeiten, Snacks und Hauptgerichten
  bereitstellen
- passende Katalogkategorien, Grundportionen und erlaubte Portionsfaktoren
  festlegen
- konkrete Mahlzeiten für alle Rollen einschließlich des späten Snacks
  bereitstellen
- Katalogdaten gegen mehrere repräsentative Zielprofile prüfen

**Abnahme:** Die Datenbank kann reproduzierbar neu aufgebaut werden. Der
freigegebene Katalog enthält vollständige, nachvollziehbare Daten und ermöglicht
für jedes unterstützte Testprofil manuell mindestens zwei praktikable
Tagespläne. Die Planung benötigt keine Live-Verbindung zu einer externen
Lebensmittel-API.

**Status:** ausstehend

## Phase 4: Tagesplaner umsetzen

**Ziel:** Ein Nutzer erhält aus seinen Tageszielen zwei bis drei
nachvollziehbare Tagespläne und kann einen davon auswählen.

**Umfang:**

- Kalorien, Protein, Fett, Kohlenhydrate und Mahlzeitenanzahl erfassen
- Mahlzeiten und praktikable Portionen zu Tagesplänen kombinieren
- gültige Pläne und transparente Annäherungen bewerten
- zwei bis drei reproduzierbare Vorschläge anzeigen
- Nährwerte je Mahlzeit und für den gesamten Tag darstellen
- festgelegte Ausschlussgrenzen und Bewertungslogik anhand weiterer
  Zielprofile und realer Katalogdaten überprüfen
- Planungslogik und zentrale Grenzfälle automatisiert testen

**Abnahme:** Alle unterstützten Testprofile liefern reproduzierbare und fachlich
erklärbare Ergebnisse. Ein Nutzer kann ohne zusätzliche Berechnung einen
Tagesplan auswählen und jede relevante Zielabweichung erkennen.

**Status:** ausstehend

## Phase 5: Wochenplan und Einkaufsliste umsetzen

**Ziel:** Aus dem ausgewählten Tagesplan entsteht ein praktisch verwendbarer
Plan samt Einkauf für sieben Tage.

**Umfang:**

- ausgewählten Tagesplan für sieben Tage darstellen
- Zutatenmengen über alle Mahlzeiten und Tage korrekt aggregieren
- Einheiten und Mengen verständlich ausgeben
- Einkaufsliste auf mobilen und größeren Bildschirmen nutzbar machen
- vollständigen Nutzerfluss automatisiert testen

**Abnahme:** Ein Testnutzer erstellt in höchstens drei Minuten einen Wochenplan
und kann dessen Einkaufsliste ohne externen Rechner verwenden. Nährwerte und
Einkaufsmengen stimmen rechnerisch mit dem gewählten Plan überein.

**Status:** ausstehend

## Phase 6: MVP mit Zielnutzern validieren

**Ziel:** Reale Nutzung zeigt, ob PrepPilot verständlich ist und einen
praktischen Wochenversuch ermöglicht.

**Umfang:**

- Zahl und Auswahl der Testpersonen sowie den Ablauf vor Beginn festlegen
- mehrere Personen aus der Zielgruppe einen Wochenplan erstellen lassen
- Verständlichkeit, Vertrauen und wahrgenommene Planqualität beobachten
- Abbrüche, Rückfragen und manuelle Korrekturen erfassen
- Erfolgskriterien aus der Produktdefinition auswerten
- blockierende Probleme vor jeder Erweiterung beheben

**Abnahme:** Die vorab festgelegte Testgruppe schließt den primären Nutzerfluss
ohne Hilfe ab. Mindestens ein erzeugter Plan wird als praktisch genug für einen
realen Wochenversuch bewertet. Rechenfehler und blockierende Bedienprobleme
sind behoben.

**Status:** ausstehend

## Phase 7: Wochenplanung abwechslungsreicher machen

**Ziel:** Nutzer erhalten mehr Abwechslung und Kontrolle, ohne dass die Planung
kompliziert oder weniger verlässlich wird.

**Möglicher Umfang:**

- mehrere unterschiedliche Tagespläne innerhalb einer Woche
- steuerbare Wiederholung und Abwechslung
- einzelne Mahlzeiten austauschen, ohne Tagesziele aus dem Blick zu verlieren
- flexible Mahlzeiten- oder Snack-Slots
- Nutzungshistorie und weitere Vorschläge
- Einkaufsliste für gemischte Wochenpläne aktualisieren

**Abnahme:** Wird nach der MVP-Validierung anhand des bestätigten Nutzerbedarfs
konkretisiert.

**Status:** später

## Phase 8: Personalisierung und Einkauf erweitern

**Ziel:** Nur nachgewiesene persönliche und organisatorische Anforderungen
werden ergänzt, ohne PrepPilot zu einem allgemeinen Haushaltsmanager zu machen.

**Möglicher Umfang:**

- Ernährungsformen, Ausschlüsse und Favoriten
- eigene Mahlzeiten, Vorlagen und gespeicherte Pläne
- Benutzerkonten und geräteübergreifende Nutzung
- Vorräte, Packungsgrößen, Preise und Budget
- Rezeptimport und automatische Nährwertberechnung
- optionale KI-Unterstützung

**Abnahme:** Einzelne Themen erhalten erst nach der MVP-Validierung eigene
Erfolgskriterien und eine priorisierte Reihenfolge.

**Status:** später

## Nächster Meilenstein

Die fachlichen Planungsregeln aus Phase 1 sind ausreichend, um mit der
Entwicklung zu beginnen. Als Nächstes startet Phase 2 mit dem minimalen
technischen Grundgerüst auf Basis der bereits ausgewählten Architektur.
