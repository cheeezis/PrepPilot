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
