# Architektur

Stand: 28. August 2026

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
- MVP-Datenquelle: versionierter und beim Laden validierter JSON-Katalog

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
versionierter Katalog
```

### Frontend

Das Frontend stellt Daten dar, nimmt Nutzereingaben entgegen und kommuniziert
mit dem Backend. Es greift weder direkt auf den Katalog noch auf externe
Lebensmittelquellen zu. Fachliche Planungs- und Nährwertlogik gehört nicht in
das Frontend.

### Backend

Das Backend ist die fachliche und technische Systemgrenze. Es validiert
Eingaben, berechnet und bewertet Tagespläne, berechnet Nährwerte und koordiniert
den Datenzugriff.

Das Backend wird als modularer Monolith entwickelt: eine deploybare Anwendung
mit klar getrennten Fachbereichen, nicht als Sammlung von Microservices.

### Katalogspeicher

Der kleine, kuratierte MVP-Katalog liegt als versionierte JSON-Datei im
Repository. Das Backend lädt und validiert ihn vollständig, bevor der Planer
ihn verwendet. Damit gibt es genau eine produktive Katalogquelle.

PostgreSQL, SQLAlchemy und Alembic gehören nicht zur Laufzeitarchitektur des
MVP. Eine Datenbank wird erst wieder eingeführt, wenn eine beschlossene Funktion
veränderliche oder nutzerspezifische Daten dauerhaft speichern muss, etwa
importierte Rezepte, eigene Mahlzeiten, Konten oder gespeicherte Pläne.

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

Der MVP-Katalog wird klein gehalten und im Repository versioniert. FoodData
Central, Open Food Facts und Herstellerangaben dienen nur als Quellen für
ausgewählte Katalogwerte; der laufende Planer ruft sie nicht auf.

Ein späterer Rezeptimport bildet einen getrennten Eingangsbereich. Erst ein
vollständig normalisiertes Rezept darf in den produktiven Katalog übernommen
werden. Fehlende Umrechnungen führen zu einer Prüfwarteschlange und nicht zu
einem unsicheren generischen Gewichts-Fallback. Diese Import- und Prüflogik wird
nicht vorsorglich im MVP implementiert.

## Lokale Entwicklungsumgebung

Frontend und Backend laufen während der lokalen Entwicklung direkt auf dem
Host. Für den MVP ist kein zusätzlicher Infrastrukturdienst und damit auch kein
Docker-Container notwendig.

## Qualitäts- und Testwerkzeuge

Das Frontend verwendet Oxlint für statische Codeprüfungen, den
TypeScript-Compiler für die Typprüfung und Vitest für schnelle automatisierte
Tests. Vitest nutzt dieselbe Transformationsgrundlage wie Vite. Playwright
prüft vollständige Nutzerflüsse im Browser und startet dafür Frontend und
Backend selbst. Der Tagesplaner-End-to-End-Test benötigt keine zusätzliche
Infrastruktur. Er wird im Frontend mit `npm run test:e2e` ausgeführt.

Das Backend verwendet Ruff für Linting und Formatierung, mypy für die statische
Typprüfung und pytest für automatisierte Tests.

Die normalen Testläufe benötigen keine gestarteten Server oder externe
Infrastruktur. Separate Integrationstests dürfen später eine tatsächlich
benötigte Infrastruktur prüfen und werden als solche kenntlich gemacht.

## Noch zu entscheiden

- genaue API-Gestaltung
- interne Backend-Module und Abhängigkeitsrichtung
- Persistenztechnik, sobald eine konkrete Funktion dauerhafte Daten benötigt
- CI/CD und Deployment-Ziel
