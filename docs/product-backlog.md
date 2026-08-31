# Produkt-Backlog

Stand: 31. August 2026

Dieses Backlog sammelt interessante Produktideen, die noch nicht Teil einer
beschlossenen Roadmap-Phase sind. Ein Eintrag ist keine Umsetzungszusage. Bevor
eine Idee in die Roadmap wandert, klären wir kurz das Nutzerproblem, den Nutzen,
den kleinsten sinnvollen Umfang und den passenden Zeitpunkt. Bereits
priorisierte Ausschnitte werden hier nur noch zur Abgrenzung ihrer späteren
Folgeschritte erwähnt.

## Produktvalidierung

### MVP mit geeigneten Zielnutzern testen

Sobald tatsächlich geeignete Personen aus der Zielgruppe verfügbar sind, soll
geprüft werden, ob sie ohne Erklärung einen Wochenplan samt Einkaufsliste
erstellen und das Ergebnis als praktisch einschätzen. Zahl, Ablauf und
Erfolgskriterien werden erst dann passend zur erreichbaren Testgruppe
festgelegt. Für den technischen MVP werden keine beliebigen Personen als
stellvertretende Testnutzer verpflichtet.

## Katalog und Datenimport

### Import-Inbox und Zutaten-Normalisierung

**Status:** als Phase 6A in `docs/roadmap.md` abgeschlossen

Der abgeschlossene erste Abschnitt nimmt Rezepte in einem getrennten
PostgreSQL-Bereich auf, normalisiert Zutaten deterministisch und stellt
unvollständige Ergebnisse mit konkreten Gründen zur internen Prüfung bereit.
Er enthält weder eine Live-Anbindung an einen Rezeptanbieter noch die
Veröffentlichung im produktiven Katalog.

### Normalisierte Rezepte in den produktiven Katalog übernehmen

**Status:** als Phase 6B in `docs/roadmap.md` abgeschlossen

Ein eigener Folgeabschnitt soll vollständig normalisierte Kandidaten fachlich
prüfen und anschließend kontrolliert als Mahlzeiten veröffentlichen. Vorher
müssen insbesondere Mahlzeitenrolle, Grundportion, erlaubte Portionsfaktoren,
Zubereitungszeit und Anleitung festgelegt werden.

Dabei muss auch die bisherige Seed-Strategie angepasst werden: Der
reproduzierbare versionierte Arbeitskatalog darf veröffentlichte Importdaten
nicht löschen oder unkontrolliert überschreiben. Der genaue Freigabe- und
Aktualisierungsprozess wird erst vor diesem Abschnitt beschlossen.

### Live-Rezeptquellen und weitere Adapter

**Status:** erster TheMealDB-Adapter als Phase 6C und praktische Härtung mit
acht realen Rezepten als Phase 6D abgeschlossen; weitere Adapter und
automatisierte Abrufe bleiben im Backlog

Nach der Import-Inbox kann ein konkreter Rezeptanbieter anhand von
Datenqualität, strukturierten Zutatenmengen, Nutzungsrechten, Kosten,
Rate-Limits und stabilen externen Kennungen ausgewählt werden. Quellenadapter
übersetzen ausschließlich in das interne Rohimportformat; anbieterspezifische
Felder gelangen nicht in den Planer.

FoodData Central bleibt die bevorzugte Recherchequelle für generische
Lebensmittel, Nährwerte und mögliche Portionsstandards. Open Food Facts kann
später getrennt für konkrete Markenprodukte bewertet werden. Externe APIs
bleiben Import- oder Recherchequellen und werden keine Laufzeitvoraussetzung
der Planung.

### Rezepte durch Nutzer importieren

Nutzer könnten eigene Rezeptquellen angeben und daraus Mahlzeiten samt
angenäherten Nährwerten anlegen. Diese Funktion baut auf der getrennten
Importpipeline und Prüfwarteschlange auf und gehört nicht zum MVP.

### KI-unterstützte Katalogpflege

Ein LLM könnte in der Prüfwarteschlange Zutatenzuordnungen, passende
FoodData-Central-Portionen oder plausible Standardgewichte vorschlagen und die
Vorschläge begründen. Deterministische Validierung und die Freigabegrenze zum
produktiven Katalog bleiben davon getrennt; ein LLM-Vorschlag darf ein
unvollständiges Rezept nicht selbstständig freigeben.

## Flexiblere Planung

- unterschiedliche Tagespläne innerhalb einer Woche
- steuerbare Wiederholung und Abwechslung
- einzelne Mahlzeiten austauschen
- flexible Mahlzeiten- oder Snack-Slots
- Nutzungshistorie bei neuen Vorschlägen berücksichtigen
- Einkaufsliste für gemischte Wochenpläne aktualisieren

## Personalisierung

- Ernährungsformen, Ausschlüsse und Favoriten
- eigene Mahlzeiten, Vorlagen und gespeicherte Pläne
- Benutzerkonten und geräteübergreifende Nutzung

## Weitere Produktdaten

- Zucker, Ballaststoffe und Salz
- Allergendaten und darauf aufbauende Filter
- Preise, Packungsgrößen und Budget
- Produkt- und Mahlzeitenbilder

## Einkauf und Vorräte

- vorhandene Vorräte berücksichtigen
- Einkaufsmengen auf Packungsgrößen aufrunden
- Einkaufskosten schätzen und Budgets berücksichtigen
