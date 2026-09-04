# Architektur

PrepPilot besteht aus React/Vite, FastAPI und PostgreSQL. Alembic verwaltet das
Schema.

```text
React
  -> GET/POST/PUT/DELETE /api/recipes
       -> Recipe-Repository -> recipes
  -> POST /api/day-plans
       -> Recipe-Repository -> Planer
  -> Ergebnis mit je einer Portion, Zutaten und Zubereitung
```

Es gibt fachlich nur die Tabelle `recipes`. Ein Rezept enthält eine oder mehrere
Mahlzeitenkategorien, seine Rezeptausbeute, Nährwerte pro Portion,
strukturierte Zutaten und Zubereitung. Eine Zutat besteht aus Menge, Einheit und
Bezeichnung. Ein Quellenlink sowie Vorbereitungs- und Kochzeit sind optional.

Der Planer arbeitet ausschließlich mit gespeicherten persönlichen Rezepten und
fragt keine externe Quelle ab. Jeder Mahlzeitenplatz verwendet genau eine
Portion und damit die gespeicherten Nährwerte pro Portion. Bis zu drei
ausgewählte Mahlzeiten werden vollständig
durchsucht. Bei vier Mahlzeiten begrenzt eine reproduzierbare Vorauswahl den
Rechenraum; der vollständige Rezeptbestand bleibt gespeichert und sichtbar.

Eine leere Rezepttabelle ist ein gültiger Zustand. Die API bleibt erreichbar,
und der Planer erklärt, dass noch kein verwendbarer Plan vorhanden ist.
