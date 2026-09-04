# PrepPilot

PrepPilot erstellt nachvollziehbare Tagespläne aus persönlichen Rezepten. Der
Nutzer hinterlegt Portionszahl, Nährwerte, Zutaten und Zubereitung selbst.
PostgreSQL speichert diese Rezepte; der Planer kombiniert ihre Nährwerte pro
Portion passend zu Kalorien- und Makrozielen.

Der aktuelle Ablauf:

```text
eigenes Rezept anlegen oder bearbeiten
  -> recipes in PostgreSQL
  -> gewünschte Mahlzeiten auswählen
  -> Tagesplan mit genau einer Portion je Mahlzeitenplatz
  -> Rezept, Zutaten und Zubereitung im Frontend anzeigen
```

Jede Zutat wird mit numerischer Menge, Einheit und Bezeichnung gespeichert. Die
Mengen gelten für das vollständige Rezept; die Nährwerte gelten pro Portion.

## Lokal starten

`start-preppilot.bat` startet PostgreSQL, Backend und Frontend. Die Anwendung
ist anschließend unter <http://127.0.0.1:5173> erreichbar. Mit
`stop-preppilot.bat` werden die lokalen Dienste beendet.

Weitere Hinweise stehen in [`docs/development.md`](docs/development.md).

Das Projekt befindet sich in Entwicklung und ist nicht für den produktiven
Einsatz gedacht.
