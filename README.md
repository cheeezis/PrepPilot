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
  -> Tagesplan aus einer oder zwei ganzen Portionen
  -> Rezept, Zutaten und Zubereitung im Frontend anzeigen
```

Die Zutaten werden aktuell nur angezeigt. PrepPilot berechnet die Nährwerte aus
den manuell angegebenen Werten pro Portion und normalisiert keine einzelnen
Lebensmittel.

## Lokal starten

`start-preppilot.bat` startet PostgreSQL, Backend und Frontend. Die Anwendung
ist anschließend unter <http://127.0.0.1:5173> erreichbar. Mit
`stop-preppilot.bat` werden die lokalen Dienste beendet.

Weitere Hinweise stehen in [`docs/development.md`](docs/development.md).

Das Projekt befindet sich in Entwicklung und ist nicht für den produktiven
Einsatz gedacht.
