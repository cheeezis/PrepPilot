# Lokale Entwicklung

## Anwendung

Voraussetzungen sind Python 3.14, Node.js und ein gestartetes Docker Desktop.
Die Abhängigkeiten werden einmalig eingerichtet:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

cd ..\frontend
npm install
```

Im Projektordner startet `start-preppilot.bat` den PostgreSQL-Container, wendet
offene Alembic-Migrationen an und startet danach FastAPI und Vite.
`stop-preppilot.bat` beendet alle drei lokalen Dienste. Die PostgreSQL-Daten
bleiben im Docker-Volume `postgres-data` erhalten.

Nach einer Schemaänderung im Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

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
npm run test:e2e
```

Die Browser-Tests legen eigene Testrezepte an und löschen ausschließlich diese
Datensätze nach dem Lauf wieder.
