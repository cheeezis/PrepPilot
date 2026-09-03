# Lokale Entwicklung

## Datenbank

PostgreSQL starten:

```powershell
docker compose up -d postgres
```

Nach dem ausdrücklich freigegebenen Recipe-first-Reset wird das neue Schema im
Backend angelegt:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

## Backend

```powershell
cd backend
.\.venv\Scripts\fastapi.exe dev src/preppilot_api/main.py
```

Prüfungen:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy src
.\.venv\Scripts\python.exe -m pytest
```

## Frontend

```powershell
cd frontend
npm run dev
```

Prüfungen:

```powershell
npm run lint
npm test
npm run build
```

Im Browser startet „33 NHS-Rezepte importieren“ den begrenzten Import. Der
zweite Lauf muss 20 unveränderte Rezepte und keine Duplikate melden.
