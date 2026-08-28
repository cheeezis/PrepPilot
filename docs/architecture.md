# Architektur

Stand: 27. August 2026

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
Eingaben, berechnet und bewertet Tagespläne, berechnet Nährwerte und
Einkaufsmengen und koordiniert den Datenzugriff.

Das Backend wird als modularer Monolith entwickelt: eine deploybare Anwendung
mit klar getrennten Fachbereichen, nicht als Sammlung von Microservices.

### Datenbank

PostgreSQL speichert die internen Lebensmittel, Mahlzeiten und später erzeugte
Pläne. Ausschließlich das Backend greift direkt auf die Datenbank zu.

Der Datenbankzugriff erfolgt zunächst synchron. Das passt zur ebenso synchronen
Planungslogik und vermeidet im MVP die zusätzliche Komplexität asynchroner
Sessions. SQLAlchemy bildet die Python-seitige Datenzugriffsschicht, psycopg
stellt die Verbindung zu PostgreSQL her und Alembic versioniert spätere
Schemaänderungen. Die Alembic-Umgebung wird erst mit dem ersten Datenmodell in
Phase 3 angelegt.

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

Ein späterer Rezeptimport bildet einen getrennten Eingangsbereich. Erst ein
vollständig normalisiertes Rezept darf in den produktiven Katalog übernommen
werden. Fehlende Umrechnungen führen zu einer Prüfwarteschlange und nicht zu
einem unsicheren generischen Gewichts-Fallback. Diese Import- und Prüflogik wird
nicht vorsorglich im MVP implementiert.

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
Backend selbst. Der Tagesplaner-End-to-End-Test benötigt keine laufende
Datenbank. Er wird im Frontend mit `npm run test:e2e` ausgeführt.

Das Backend verwendet Ruff für Linting und Formatierung, mypy für die statische
Typprüfung und pytest für automatisierte Tests.

Die normalen Testläufe benötigen keine gestarteten Server oder externe
Infrastruktur. Abhängigkeiten wie PostgreSQL werden in diesen Tests gezielt
ersetzt. Separate Integrationstests dürfen später die echte Infrastruktur
prüfen und werden als solche kenntlich gemacht.

## Noch zu entscheiden

- genaue API-Gestaltung
- interne Backend-Module und Abhängigkeitsrichtung
- CI/CD und Deployment-Ziel
