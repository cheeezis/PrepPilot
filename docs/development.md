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

Im Browser startet „NHS-Katalog synchronisieren“ die automatische Erkennung und
den Import. Der zweite Lauf muss die bereits gespeicherten Rezepte als
unverändert melden und darf keine Duplikate erzeugen.
