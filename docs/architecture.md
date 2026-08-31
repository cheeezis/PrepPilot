# Architektur

Stand: 31. August 2026

Dieses Dokument hält bestätigte technische Entscheidungen fest. Details werden
schrittweise ergänzt, bevor das jeweilige Grundgerüst umgesetzt wird.

## Ziele

- klar verständliches Fullstack-Portfolio-Projekt
- fachliche Planungslogik unabhängig von der Benutzeroberfläche
- reproduzierbare Berechnungen und gut testbare Verantwortlichkeiten
- möglichst wenig Infrastruktur- und Abstraktionsaufwand im MVP

## Bestätigter Kern-Stack

- Frontend: React-SPA mit TypeScript und Vite 8
- Frontend-Laufzeit und Paketverwaltung: Node.js 24 LTS mit npm
- Backend: Python 3.14 mit FastAPI
- Python-Umgebung und Paketverwaltung: `venv` aus der Standardbibliothek und pip
- Datenbank: PostgreSQL
- Datenbankzugriff: synchrones SQLAlchemy 2 mit psycopg 3
- Datenbankmigrationen: Alembic

Frontend-Abhängigkeiten werden über die npm-Lockdatei reproduzierbar
festgehalten. Direkte Backend-Abhängigkeiten stehen mit fester Version in
`pyproject.toml`; pip löst deren transitive Abhängigkeiten bei der Installation
auf. Ergänzende Bibliotheken werden erst ausgewählt, wenn die jeweilige Phase
sie benötigt.

## Repository-Form

PrepPilot wird als Monorepo geführt. Frontend, Backend, Dokumentation und
gemeinsame Infrastruktur werden zusammen versioniert.

Die erste grobe Form ist:

```text
PrepPilot/
├── frontend/
├── backend/
├── docs/
└── gemeinsame Infrastrukturdateien
```

Diese Darstellung legt noch keine detaillierte Ordnerstruktur innerhalb von
Frontend oder Backend fest.

## Systemgrenze und Datenfluss

```text
Browser
  ↓
React-/TypeScript-Frontend
  ↓ HTTP/JSON
FastAPI-Backend
  ↓
PostgreSQL
```

### Frontend

Das Frontend stellt Daten dar, nimmt Nutzereingaben entgegen und kommuniziert
mit dem Backend. Es greift weder direkt auf PostgreSQL noch auf externe
Lebensmittelquellen zu. Fachliche Planungs- und Nährwertlogik gehört nicht in
das Frontend.

### Backend

Das Backend ist die fachliche und technische Systemgrenze. Es validiert
Eingaben, berechnet und bewertet Tagespläne, berechnet Nährwerte und koordiniert
den Datenzugriff.

Das Backend wird als modularer Monolith entwickelt: eine deploybare Anwendung
mit klar getrennten Fachbereichen, nicht als Sammlung von Microservices.

### Datenbank

PostgreSQL speichert die internen Lebensmittel, Mahlzeiten und später erzeugte
Pläne. Ausschließlich das Backend greift direkt auf die Datenbank zu.

Die versionierte JSON-Datei ist ausschließlich die nachvollziehbare Seed-Quelle.
Nach Migration und Seed liest der laufende Planer Lebensmittel, Mahlzeiten,
Zutaten, Rollen und Portionsfaktoren aus PostgreSQL. Eine nicht erreichbare,
unvollständige oder leere Datenbank macht sowohl den Systemcheck als auch die
Planerstellung bewusst nicht verfügbar.

Der Datenbankzugriff erfolgt zunächst synchron. Das passt zur ebenso synchronen
Planungslogik und vermeidet im MVP die zusätzliche Komplexität asynchroner
Sessions. SQLAlchemy bildet die Python-seitige Datenzugriffsschicht, psycopg
stellt die Verbindung zu PostgreSQL her und Alembic versioniert spätere
Schemaänderungen. Die Alembic-Umgebung wird erst mit dem ersten Datenmodell in
Phase 3 angelegt.

## Wochenplan und Einkaufsliste

Im MVP wird ein ausgewählter Tagesplan unverändert für alle sieben Wochentage
verwendet. Die Auswahl bleibt im Frontend-Zustand und wird noch nicht dauerhaft
gespeichert.

Die Einkaufsliste ist eine reine Darstellungssumme: Das Frontend multipliziert
die bereits vom Backend gelieferten, normalisierten Zutatenmengen mit sieben
und fasst gleiche Lebensmittel mit gleicher Einheit zusammen. Dabei finden
weder Nährwertberechnungen noch Einheitenumrechnungen statt. Für diesen festen
Wochenplan wäre ein zusätzlicher Backend-Endpunkt oder ein eigenes Datenmodell
unnötige MVP-Komplexität.

## Katalog- und Importgrenze

Der produktive Mahlzeitenkatalog ist die dauerhafte Schnittstelle zur
Planungslogik. Er enthält ausschließlich vollständige Zutatenzuordnungen und
bereits normalisierte Mengen in Gramm oder Millilitern. Der Planer kennt weder
externe Rezeptformate noch Haushaltsmaße, Portionstabellen oder unsichere
Zuordnungen.

Der MVP-Katalog wird klein gehalten, im Repository versioniert und
reproduzierbar in PostgreSQL geladen. FoodData Central, Open Food Facts und
Herstellerangaben dienen nur als Quellen für ausgewählte Katalogwerte; der
laufende Planer ruft sie nicht auf.

Phase 6A bildet einen getrennten Eingangsbereich in PostgreSQL. Strukturierte
Rohrezepte werden idempotent aufgenommen, deterministisch normalisiert und über
interne Backend-Endpunkte geprüft. Fehlende Umrechnungen führen zu einer
Prüfwarteschlange und nicht zu einem unsicheren generischen Gewichts-Fallback.
Bestätigte Aliase und Portionsstandards bleiben bei einem erneuten Katalog-Seed
erhalten.

Erst ein vollständig normalisiertes und anschließend fachlich freigegebenes
Rezept darf in den produktiven Katalog übernommen werden. Phase 6A endet vorher
bei `ready_for_catalog_review`; der Planer liest keine Importtabellen. Eine
Live-Verbindung zu einer Rezept- oder Lebensmittel-API ist weiterhin keine
Laufzeitvoraussetzung.

Phase 6B veröffentlicht einen solchen Kandidaten transaktional als Mahlzeit.
Die Mahlzeitenherkunft und der eindeutige Verweis zum Rezeptimport verhindern
doppelte Freigaben. Der Seed aktualisiert und entfernt nur Mahlzeiten mit der
Herkunft `curated_seed`; veröffentlichte Importmahlzeiten bleiben erhalten. Der
Planer benötigt dadurch keine Importlogik und liest weiterhin ausschließlich
den produktiven Datenbankkatalog.

Phase 6C ergänzt davor genau einen TheMealDB-Adapter. Der interne Endpunkt ruft
ein Rezept nur auf ausdrückliche Anforderung anhand seiner externen ID ab. Der
Adapter bewahrt das empfangene Rezeptobjekt als Rohdaten und übersetzt dessen
Zutaten-/Maßpaare in das bestehende, quellenneutrale Inbox-Format. Einfache
Brüche werden deterministisch in Dezimalmengen überführt; unsichere Texte werden
nicht geschätzt. Weil TheMealDB keine verlässliche Portionenzahl liefert, muss
diese vor einer möglichen Freigabe geprüft und ergänzt werden.

Netzwerk- und Anbieterdetails enden am Adapter. Weder Normalisierung noch
Katalogfreigabe oder Planung rufen TheMealDB auf. Der Entwicklungszugang nutzt
standardmäßig den von TheMealDB dokumentierten Testschlüssel `1`; Schlüssel,
Basis-URL und Timeout bleiben über `PREPPILOT_`-Umgebungsvariablen
konfigurierbar.

Phase 6D macht bestätigte Normalisierungsmetadaten reproduzierbar. Der
versionierte Katalog kann je Lebensmittel eindeutige externe Aliase und
belegte Standardmengen für konkrete Maße enthalten. Der Seed übernimmt diese
Einträge idempotent in `food_aliases` und `food_measure_defaults`, ohne später
manuell geprüfte Ergänzungen zu löschen. Alias-Kollisionen zwischen
Lebensmitteln brechen bereits die Katalogvalidierung ab.

Eine Stichprobe aus acht realen Rezepten dient als bewusster Qualitätscheck und
nicht als Katalog-Massenimport. Nur der vollständig geprüfte
Banana-Pancakes-Kandidat wird veröffentlicht. Die Originalquelle bestätigt zwei
Portionen und zehn Minuten Zubereitungszeit. Relevante Zutaten werden vollständig
abgebildet; nur Backpulver und Vanille werden nach ausdrücklicher Entscheidung
aus der Nährwert- und Einkaufsberechnung ausgeschlossen.

Phase 6E führt für Lebensmittel dieselbe Sicherheitsgrenze ein. Der
FoodData-Central-Adapter ruft genau eine bekannte FDC-ID ab und speichert die
unveränderte Antwort zunächst in `food_imports`. Nur Foundation- und SR-Legacy-
Datensätze werden als generische Kandidaten ausgewertet. Nährstoffkennungen
werden explizit zugeordnet; europäische Kohlenhydrate entstehen als Differenz
aus Gesamt-Kohlenhydraten und Ballaststoffen.

Die Food-Inbox schreibt nicht direkt in `foods`. Erst ein vollständiger und
ausdrücklich freigegebener Kandidat erzeugt ein gramm-basiertes Lebensmittel.
`Food.origin` und der eindeutige Verweis zum Food-Import schützen vor doppelter
Freigabe. Der Seed verwaltet ausschließlich `curated_seed`-Lebensmittel und
erhält importierte Lebensmittel. Der FDC-Schlüssel wird nur über
`PREPPILOT_FOOD_DATA_CENTRAL_API_KEY` konfiguriert und nicht im Repository
gespeichert; für lokale Erkundung ist der dokumentierte `DEMO_KEY`
voreingestellt.

## Lokale Entwicklungsumgebung

PostgreSQL läuft lokal über Docker Compose. Die PostgreSQL-Version und die
notwendige Entwicklungskonfiguration werden dadurch im Repository festgehalten
und lassen sich auf einem neuen Rechner reproduzieren.

Die Entwicklungsumgebung verwendet das offizielle
`postgres:18.6-bookworm`-Image. Daten liegen in einem benannten Docker-Volume
und bleiben beim Stoppen oder Ersetzen des Containers erhalten.

Frontend und Backend laufen während der lokalen Entwicklung zunächst direkt
auf dem Host. Sie werden im MVP nicht allein aus Gründen der Einheitlichkeit
containerisiert. Damit bleibt schnelles Neuladen und Debugging unkompliziert,
während nur die zustandsbehaftete Infrastruktur isoliert betrieben wird.

## Qualitäts- und Testwerkzeuge

Das Frontend verwendet Oxlint für statische Codeprüfungen, den
TypeScript-Compiler für die Typprüfung und Vitest für schnelle automatisierte
Tests. Vitest nutzt dieselbe Transformationsgrundlage wie Vite. Playwright
prüft vollständige Nutzerflüsse im Browser und startet dafür Frontend und
Backend selbst. Der Tagesplaner-End-to-End-Test verwendet den laufenden,
befüllten PostgreSQL-Katalog und wird im Frontend mit `npm run test:e2e`
ausgeführt.

Das Backend verwendet Ruff für Linting und Formatierung, mypy für die statische
Typprüfung und pytest für automatisierte Tests.

Die schnellen Unit- und API-Tests benötigen keine gestarteten Server oder
externe Infrastruktur. PostgreSQL wird darin gezielt ersetzt. Der
End-to-End-Test ist zugleich der Integrationstest für den vollständigen Weg vom
Browser über das Backend bis zum Datenbankkatalog.

## Noch zu entscheiden

- genaue API-Gestaltung
- interne Backend-Module und Abhängigkeitsrichtung
- CI/CD und Deployment-Ziel
