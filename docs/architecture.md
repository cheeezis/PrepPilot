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

Der NHS-Adapter akzeptiert ausschließlich 33 fest hinterlegte URLs. Er liest
Titel und Zutaten aus Recipe-JSON-LD, die sichtbare Methodenliste aus dem
Rezeptbereich sowie Portionen, Zeiten und acht Nährwerte aus dem wiederkehrenden
Rezeptkopf. Unvollständige oder energetisch widersprüchliche Seiten werden
abgelehnt. Bis zu vier Seiten werden parallel abgerufen; Auswertung und
Datenbankspeicherung erfolgen anschließend geordnet. Quelle plus URL
identifizieren ein Rezept; ein Inhalts-Hash erkennt unveränderte Wiederholungen
und Aktualisierungen.

Die Kategorie wird aus den offiziellen NHS-Sammlungen Frühstück, Mittagessen
und Abendessen übernommen. Sie ist im Rezeptbestand sichtbar und filterbar.
Jeder Tagesplan kombiniert genau ein Rezept aus jeder der drei Kategorien.

Der Planer fragt keine externe Quelle ab. Er arbeitet nur mit vollständigen
Rezepten aus PostgreSQL und skaliert sie mit einer oder zwei ganzen Portionen.
Rezeptgruppen, die selbst mit zwei Portionen die äußeren Zielgrenzen nicht
erreichen können, werden vor der Portionssuche sicher verworfen. Aus den
verbleibenden Kombinationen hält der Planer nur die drei aktuell besten im
Speicher. Die bestehenden Zielbereiche und das nachvollziehbare Scoring bleiben
erhalten; es werden keine potenziell gültigen Pläne ausgeblendet.
