# Lokale Entwicklung

Stand: 28. August 2026

PrepPilot benötigt lokal PostgreSQL, das Backend und das Frontend. Alle Befehle
werden in PowerShell ausgeführt.

## Datenbank vorbereiten

Im Repository-Hauptordner:

```powershell
docker compose up -d
docker compose ps
```

Beim ersten Start, nach neuen Migrationen oder nach Änderungen am kuratierten
Katalog im Ordner `backend`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m preppilot_api.catalog_seed
```

Der Seed synchronisiert den kuratierten Grundbestand reproduzierbar mit der
versionierten `catalog.json`. Kontrolliert importierte Lebensmittel und
Mahlzeiten werden dabei nicht überschrieben.

## Anwendung starten

Backend im Ordner `backend`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn preppilot_api.main:app --reload --port 8000
```

Frontend in einem zweiten Terminal im Ordner `frontend`:

```powershell
npm run dev
```

Die Oberfläche ist anschließend unter `http://localhost:5173` erreichbar. Erst
wenn PostgreSQL erreichbar und der Katalog befüllt ist, zeigt sie `System bereit`
an und erstellt Tagespläne.

## Prüfungen

Backend im Ordner `backend`:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src tests
```

Frontend im Ordner `frontend`:

```powershell
npm test
npm run lint
npm run build
npm run test:e2e
```

Für den End-to-End-Test muss der migrierte und befüllte PostgreSQL-Container
laufen.
