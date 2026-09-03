# PrepPilot

PrepPilot baut einen kleinen, nachvollziehbaren Tagesplan aus vollständigen
Rezepten. Der Recipe-first-MVP importiert 20 fest geprüfte Rezepte von NHS
Healthier Families, speichert deren Nährwerte pro Portion in PostgreSQL und
kombiniert sie passend zu Kalorien- und Makrozielen.

Der aktuelle Ablauf:

```text
20 freigegebene NHS-Seiten
  -> validieren und idempotent importieren
  -> recipes in PostgreSQL
  -> Tagesplan aus ganzen Portionen
  -> Rezept, Zutaten und Quelle im Frontend anzeigen
```

Lebensmittel-Normalisierung, Einkaufslisten und Wochenpläne gehören bewusst
nicht zu diesem ersten Schnitt. Die Abgrenzung steht in
[`docs/recipe-first-mvp.md`](docs/recipe-first-mvp.md).

Das Projekt befindet sich in Entwicklung und ist nicht für den produktiven
Einsatz gedacht.
