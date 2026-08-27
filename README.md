# PrepPilot

PrepPilot ist eine React-/FastAPI-Anwendung mit PostgreSQL. Dieses Repository
enthält Frontend, Backend, Dokumentation und lokale Infrastruktur gemeinsam.

## Voraussetzungen

- Node.js 24 mit npm
- Python 3.14
- Docker Desktop mit Docker Compose

Die folgenden Befehle werden in PowerShell im Hauptverzeichnis des Repositorys
ausgeführt.

## Einmalige Einrichtung

```powershell
npm --prefix frontend install
python -m venv backend/.venv
Set-Location backend
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Set-Location ..
```

## Anwendung starten

PostgreSQL starten:

```powershell
docker compose up -d
```

Datenbankschema auf den aktuellen Stand bringen:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m preppilot_api.catalog_seed
Set-Location ..
```

`catalog_seed` ersetzt den Inhalt der vier Katalogtabellen durch den im
Repository versionierten MVP-Katalog. Der Befehl ist für die lokale
Entwicklungsdatenbank gedacht.

Die experimentelle Phase-3-Migrationshistorie wurde am 27. August 2026 durch
ein vereinfachtes Ausgangsschema ersetzt. Existiert noch eine damit aufgebaute
lokale Datenbank, muss das ausschließlich für PrepPilot verwendete Docker-Volume
einmal neu erstellt werden:

```powershell
docker compose down -v
docker compose up -d
Set-Location backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m preppilot_api.catalog_seed
Set-Location ..
```

`docker compose down -v` entfernt alle Daten der lokalen PrepPilot-Datenbank.

Backend in einem eigenen Terminal starten:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn preppilot_api.main:app --reload --app-dir backend/src --reload-dir backend --host 127.0.0.1 --port 8000
```

Frontend in einem weiteren Terminal starten:

```powershell
npm --prefix frontend run dev
```

Die Anwendung ist unter <http://127.0.0.1:5173> erreichbar. Der Backend-
Systemcheck liegt unter <http://127.0.0.1:8000/api/health>.

## Qualitätsprüfungen

Backend:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check src tests migrations
.\.venv\Scripts\python.exe -m ruff format --check src tests migrations
.\.venv\Scripts\python.exe -m mypy src tests
Set-Location ..
```

Frontend:

```powershell
npm --prefix frontend test
npm --prefix frontend run lint
npm --prefix frontend run build
```
