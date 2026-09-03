# PrepPilot

PrepPilot baut einen kleinen, nachvollziehbaren Tagesplan aus vollständigen
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
  -> Tagesplan aus ganzen Portionen
  -> Rezept, Zutaten und Quelle im Frontend anzeigen
```

Lebensmittel-Normalisierung, Einkaufslisten und Wochenpläne gehören bewusst
nicht zu diesem ersten Schnitt. Die Abgrenzung steht in
[`docs/recipe-first-mvp.md`](docs/recipe-first-mvp.md).

Das Projekt befindet sich in Entwicklung und ist nicht für den produktiven
Einsatz gedacht.
