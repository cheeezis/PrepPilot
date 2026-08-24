# Architektur

Stand: 24. August 2026

Dieses Dokument hält bestätigte technische Entscheidungen fest. Details werden
schrittweise ergänzt, bevor das jeweilige Grundgerüst umgesetzt wird.

## Ziele

- klar verständliches Fullstack-Portfolio-Projekt
- fachliche Planungslogik unabhängig von der Benutzeroberfläche
- reproduzierbare Berechnungen und gut testbare Verantwortlichkeiten
- möglichst wenig Infrastruktur- und Abstraktionsaufwand im MVP

## Bestätigter Kern-Stack

- Frontend: React mit TypeScript
- Backend: Python mit FastAPI
- Datenbank: PostgreSQL

Konkrete Versionen und ergänzende Bibliotheken sind noch nicht ausgewählt.

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

## Noch zu entscheiden

- Frontend-Build- und Testwerkzeuge
- Python-Projekt- und Abhängigkeitsverwaltung
- Datenbankzugriff und Migrationen
- genaue API-Gestaltung
- interne Backend-Module und Abhängigkeitsrichtung
- lokale Entwicklungsumgebung und Containerisierung
- CI/CD und Deployment-Ziel
