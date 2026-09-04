# Lokale Entwicklung

## Voraussetzungen

- Python 3.14
- Node.js mit npm
- Docker Desktop mit laufender Docker Engine

## Einmalige Einrichtung

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

cd ..\frontend
npm install
```

## Anwendung starten und stoppen

PostgreSQL wird im Projektordner gestartet:

```powershell
docker compose up -d postgres
```

Danach werden zunächst die Migrationen und anschließend das Backend in einem
zweiten Terminal gestartet:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn preppilot_api.main:app --host 127.0.0.1 --port 8000
```

Das Frontend läuft in einem dritten Terminal:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

- Frontend: <http://127.0.0.1:5173>
- Backend-Dokumentation: <http://127.0.0.1:8000/docs>
- Healthcheck: <http://127.0.0.1:8000/api/health>

Backend und Frontend werden in ihren Terminals mit `Strg+C` beendet. Danach
kann PostgreSQL im Projektordner gestoppt werden:

```powershell
docker compose stop postgres
```

Die V5-Daten bleiben im Docker-Volume `postgres-v5-data` erhalten. Das frühere
V4-Volume bleibt getrennt und wird nicht automatisch gelöscht.

## Konfiguration

Das Backend liest Einstellungen mit dem Präfix `PREPPILOT_`. Die
Datenbankverbindung kann beispielsweise überschrieben werden:

```powershell
$env:PREPPILOT_DATABASE_URL = "postgresql+psycopg://user:password@localhost/database"
```

Ohne Überschreibung wird die lokale Compose-Datenbank `preppilot_v5` verwendet.

## Migrationen

Offene Migrationen anwenden:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Eine neue Revision wird erst zusammen mit einer konkreten Schemaänderung
angelegt. Autogenerierte Migrationen müssen vor dem Commit geprüft werden.

## Backend prüfen

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest
```

## Frontend prüfen

```powershell
cd frontend
npm run lint
npm test
npm run build
```
