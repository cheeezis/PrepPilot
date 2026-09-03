# PrepPilot

PrepPilot baut nachvollziehbare Tages- und Meal-Prep-Pläne aus vollständigen
Rezepten. Der Recipe-first-MVP entdeckt geeignete Rezepte im NHS-Katalog
Healthier Families automatisch, speichert deren Nährwerte pro Portion in
PostgreSQL und kombiniert sie passend zu Kalorien- und Makrozielen.

Der aktuell erkannte NHS-Bestand umfasst 169 relevante Seiten. Davon bestehen
149 die Qualitätsprüfung und liegen lokal als planbare oder sichtbare Rezepte
vor; 20 unvollständige oder widersprüchliche Seiten werden transparent
abgelehnt.

Der aktuelle Ablauf:

```text
NHS-Kategorien automatisch abfragen
  -> Nachtisch ausschließen
  -> Rezeptseiten validieren und idempotent importieren
  -> recipes in PostgreSQL
  -> gewünschte Mahlzeiten auswählen
  -> Tagesplan oder 3- bis 7-Tage-Plan aus ganzen Portionen
  -> gleiche Rezepte in passenden Blöcken aus ein bis drei Tagen
  -> Rezept, Zutaten und Quelle im Frontend anzeigen
```

Lebensmittel-Normalisierung, skalierte Zutaten und Einkaufslisten gehören
bewusst noch nicht zu diesem Schnitt. Die ursprüngliche MVP-Abgrenzung steht in
[`docs/recipe-first-mvp.md`](docs/recipe-first-mvp.md).

Das Projekt befindet sich in Entwicklung und ist nicht für den produktiven
Einsatz gedacht.
