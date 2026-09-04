# PrepPilot

PrepPilot ist ein persönlicher Meal-Prep-Planer für eine vollständige Woche.
Die Anwendung verbindet selbst gepflegte Lebensmittel mit eigenen Rezepten und
verteilt die Portionen eines vorbereiteten Rezepts nachvollziehbar auf sieben
Tage.

Der entscheidende Grundsatz: Wenn ein Meal-Prep-Rezept sechs Portionen ergibt,
werden genau diese sechs Portionen innerhalb derselben Woche verwendet. Jede
Mahlzeit verbraucht eine Portion; es entstehen weder unsichtbare zusätzliche
Portionen noch unberücksichtigte Reste.

## V5-MVP

Der erste V5-MVP ist bewusst auf einen klaren Alltagsfall begrenzt:

- eine Person und sieben zusammenhängende Tage
- Frühstück, Mittagessen und Abendessen
- persönliche Lebensmittel mit Nährwerten pro Bezugsmenge
- persönliche Rezepte mit Zutaten, Ausbeute und Meal-Prep-Kennzeichnung
- aus Lebensmitteln berechnete Rezept- und Portionsnährwerte
- reproduzierbare Wochenplanung mit vollständig verwendeten Meal-Prep-Batches

Snacks, mehrere Personen, externe Datenquellen, Einkaufslisten und
wochenübergreifende Reste gehören zunächst nicht zum MVP.

## Aktueller Stand

V5 ist ein sauberer Neustart auf dem Branch `rewrite/v5-foundation`. Die
technische Grundlage besteht aus React/Vite, FastAPI, PostgreSQL und Alembic.
Derzeit enthält sie bewusst noch keine fachlichen Tabellen oder Funktionen:

```text
React-Oberfläche mit leerem Anwendungszustand
  -> GET /api/health
  -> FastAPI prüft die PostgreSQL-Verbindung
```

Als nächster fachlicher Abschnitt entsteht der Lebensmittelkatalog.

## Lokal entwickeln

Vorausgesetzt werden Python 3.14, Node.js und Docker Desktop. Nach der einmaligen
Einrichtung werden Datenbank, Backend und Frontend in drei Terminals gestartet.
Die Anwendung ist anschließend unter <http://127.0.0.1:5173> erreichbar.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

cd ..\frontend
npm install

cd ..
docker compose up -d postgres
```

Die Befehle für Backend, Frontend und das Beenden der Dienste sowie alle
Prüfbefehle stehen in [`docs/development.md`](docs/development.md).

## Dokumentation

- [`docs/v5-plan.md`](docs/v5-plan.md): verbindlicher Umfang, Fachmodell und
  Umsetzungsreihenfolge
- [`docs/project-history.md`](docs/project-history.md): frühere Produktphasen
  und Gründe für den Neustart
- [`docs/development.md`](docs/development.md): lokale Einrichtung, Start und
  Prüfungen

PrepPilot befindet sich in Entwicklung und ist keine medizinische
Ernährungsberatung.
