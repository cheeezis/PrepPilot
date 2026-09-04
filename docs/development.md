# Lokale Entwicklung

## Anwendung

Im Projektordner startet `start-preppilot.bat` PostgreSQL, FastAPI und Vite.
`stop-preppilot.bat` beendet die lokalen Dienste.

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
