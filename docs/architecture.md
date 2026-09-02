# Architektur

PrepPilot besteht aus React/Vite, FastAPI und PostgreSQL. Alembic verwaltet das
Schema.

```text
React
  -> POST /api/imports/nhs
       -> NHS-Adapter -> recipes
  -> POST /api/day-plans
       -> Recipe-Repository -> Planer
  -> Ergebnis mit Portionen, Zutaten und Quelllink
```

Der NHS-Adapter akzeptiert ausschließlich zehn fest hinterlegte URLs. Er liest
Titel, Zutaten und Zubereitung aus Recipe-JSON-LD sowie Portionen, Zeiten und
vier Makros aus dem wiederkehrenden Rezeptkopf. Unvollständige Seiten werden
abgelehnt. Quelle plus URL identifizieren ein Rezept; ein Inhalts-Hash erkennt
unveränderte Wiederholungen und Aktualisierungen.

Der Planer fragt keine externe Quelle ab. Er arbeitet nur mit vollständigen
Rezepten aus PostgreSQL und skaliert sie mit einer oder zwei ganzen Portionen.
Die bestehenden Zielbereiche und das nachvollziehbare Scoring bleiben erhalten.
