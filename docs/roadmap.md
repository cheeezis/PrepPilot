# Produkt- und Entwicklungs-Roadmap

Stand: 28. August 2026

Diese Roadmap führt PrepPilot von der Produktidee zu einem validierten Minimum
Viable Product (MVP), also der kleinsten sinnvoll nutzbaren Produktversion. Die
Phasen bauen aufeinander auf. Eine Phase gilt erst als abgeschlossen, wenn ihr
überprüfbares Abnahmekriterium erfüllt ist. Noch nicht priorisierte Ideen nach
dem MVP stehen getrennt in `docs/product-backlog.md`.

Der MVP umfasst die Phasen 0 bis 6. Nach Phase 5 ist die erste Version nutzbar;
Phase 6 prüft mit realen Nutzern, ob sie das Produktversprechen tatsächlich
erfüllt. Erst danach werden Erweiterungen aus dem Backlog priorisiert.

## Aktueller Stand

| Phase | Ergebnis | Status |
| --- | --- | --- |
| 0 | Produkt klar ausgerichtet | abgeschlossen |
| 1 | Regeln für einen guten Tagesplan festgelegt | abgeschlossen |
| 2 | Technisches Grundgerüst lauffähig | abgeschlossen |
| 3 | Lebensmittel- und Mahlzeitendaten verfügbar | abgeschlossen |
| 4 | Tagesplaner nutzbar | abgeschlossen |
| 5 | Wochenplan und Einkaufsliste nutzbar | abgeschlossen |
| 6 | MVP mit Zielnutzern validiert | in Bearbeitung |

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

**Status:** abgeschlossen

Bestätigte Architekturentscheidungen stehen in `docs/architecture.md`.

## Phase 3: Daten- und Kataloggrundlage schaffen

**Ziel:** PrepPilot besitzt einen kleinen, verlässlichen internen Datenbestand,
aus dem sich realistische Tagespläne bilden lassen.

**Umfang:**

- Lebensmittel, Nährwerte, Mahlzeiten und normalisierte Zutatenmengen
  modellieren
- Datenbanktabellen und nachvollziehbare Migrationen anlegen
- generische und markenspezifische Lebensmittel unterscheiden
- Anforderungen an Datenqualität, Einheiten, Herkunft und Freigabe festlegen
- externe Datenquellen fachlich und rechtlich bewerten
- geeignete Lebensmittel und Nährwerte nachvollziehbar aus FoodData Central,
  Open Food Facts oder Herstellerangaben auswählen
- sämtliche Zutatenmengen des freigegebenen Katalogs direkt in Gramm oder
  Millilitern kuratieren
- den versionierten Katalog reproduzierbar in die Datenbank laden
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
Lebensmittel-API und keine Verarbeitung externer Rezeptmaße.

**Status:** abgeschlossen

Das bestätigte MVP-Datenmodell steht in `docs/data-model.md`.

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

**Status:** abgeschlossen

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

**Status:** abgeschlossen

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

**Status:** in Bearbeitung

## Nächster Meilenstein

Phase 3 ist abgeschlossen. Der versionierte Arbeitskatalog enthält 21
Lebensmittel und je zwei Mahlzeiten für alle fünf Rollen. Sämtliche Nährwerte
sind gegen FoodData Central oder ein konkretes europäisches
Herstelleretikett geprüft und ihre Herkunft ist direkt am Katalogeintrag
festgehalten. Die Kohlenhydratwerte verwenden einheitlich die europäische
Definition ohne Ballaststoffe. Nach der erneuten Auswertung ermöglichen die
freigegebenen Portionsfaktoren für jede Referenzstruktur von drei bis sechs
Mahlzeiten mindestens zwei gültige Kombinationen.

Phase 4 ist abgeschlossen. Die Planungslogik erzeugt aus Tageszielen und
Mahlzeitenanzahl reproduzierbar bis zu drei gültige Tagespläne oder transparent
bewertete Annäherungen. Unbrauchbare Kandidaten und inhaltlich doppelte Pläne
werden ausgeschlossen. Der erste API-Endpunkt und eine einfache Oberfläche für
Eingabe, Nährwertübersicht und Mahlzeitendetails sind umgesetzt. Ein Vorschlag
kann ausgewählt und für den nächsten Schritt im Frontend vorgemerkt werden.
Die Bewertung zeigt für jeden Nährwert Ist-Wert, Zielbereich und eine konkrete
Unter- oder Überschreitung. Harte und weiche Abweichungen bleiben unterscheidbar.
Zusätzliche niedrige und hohe Zielprofile sowie der vollständige Ablauf von der
Eingabe bis zur Auswahl sind automatisiert geprüft.

Phase 5 ist abgeschlossen. Der ausgewählte Tagesplan wird für alle sieben
Wochentage dargestellt und aus seinen normalisierten Zutaten entsteht eine
aggregierte Einkaufsliste. Die Summenberechnung ist mit Unit-Tests abgesichert;
der vollständige Ablauf ist als Browser-Test abgedeckt und die Oberfläche wurde
auf Desktop- und Mobilgröße geprüft. Der Nutzerfluss wurde manuell abgenommen.
Der Planer lädt seinen freigegebenen Katalog nun tatsächlich aus PostgreSQL;
ohne erreichbare und befüllte Datenbank werden Systemcheck und Planung als nicht
verfügbar gemeldet.

Phase 6 ist vorbereitet. `docs/mvp-validation.md` legt drei geeignete
Testpersonen, eine einheitliche Aufgabe, Beobachtungskriterien, Nachfragen und
messbare Abnahmebedingungen vor dem ersten Test fest. Als Nächstes werden die
drei Tests durchgeführt und ohne nachträgliche Änderung der Kriterien
ausgewertet.
