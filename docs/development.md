# Lokale Entwicklung

Stand: 2. September 2026

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

Über die Navigation `Importprüfung` ist zusätzlich der lokale interne
Importzustand sichtbar. Ein begrenzter Wikibooks-Lauf wird im Ordner `backend`
zunächst ohne Datenbankänderung geprüft:

```powershell
.\.venv\Scripts\python.exe -m preppilot_api.wikibooks_import --limit 5
```

Nur mit dem ausdrücklichen Schalter `--write` werden geeignete Kandidaten in die
Recipe-Inbox geschrieben:

```powershell
.\.venv\Scripts\python.exe -m preppilot_api.wikibooks_import --limit 5 --write
```

Der Bericht nennt entdeckte, geeignete, abgelehnte, importierte und bereits
vorhandene Seiten. Die Laufgröße ist technisch auf höchstens 25 begrenzt.

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
