# Architektur

PrepPilot besteht aus React/Vite, FastAPI und PostgreSQL. Alembic verwaltet das
Schema.

```text
React
  -> POST /api/imports/nhs
       -> NHS-Adapter -> recipes
  -> POST /api/day-plans
       -> Recipe-Repository -> Planer
  -> POST /api/week-plans
       -> Recipe-Repository -> Planer -> Meal-Prep-Blöcke aus 1–3 Tagen
  -> Ergebnis mit Portionen, Zutaten und Quelllink
```

Der NHS-Adapter entdeckt Rezept-URLs über die offiziellen NHS-Filter für
Frühstück, Mittagessen, Abendessen, Snacks und Getränke. Getränke und Snacks
werden in PrepPilot gemeinsam als `snack` geführt; alle Rezepte aus der
Nachtisch-Sammlung werden ausgeschlossen. Der Adapter liest
Titel und Zutaten aus Recipe-JSON-LD, die sichtbare Methodenliste aus dem
Rezeptbereich sowie Portionen, Zeiten und acht Nährwerte aus dem wiederkehrenden
Rezeptkopf. Unvollständige oder energetisch widersprüchliche Seiten werden
abgelehnt. Bis zu vier Seiten werden parallel abgerufen; Auswertung und
Datenbankspeicherung erfolgen anschließend geordnet. Quelle plus URL
identifizieren ein Rezept; ein Inhalts-Hash erkennt unveränderte Wiederholungen
und Aktualisierungen.

Die Kategorien werden aus den offiziellen NHS-Sammlungen übernommen. Ein Rezept
kann mehreren Sammlungen angehören; deshalb speichert PrepPilot eine Liste. Sie
ist im Rezeptbestand sichtbar, durchsuchbar und filterbar. Im Planer wählt der
Nutzer die gewünschten Mahlzeiten aus. Frühstück, Mittagessen und Abendessen
sind voreingestellt; ein Snack kann ergänzt oder eine Hauptmahlzeit abgewählt
werden.

Der Planer fragt keine externe Quelle ab. Er arbeitet nur mit vollständigen
Rezepten aus PostgreSQL und skaliert sie mit einer oder zwei ganzen Portionen.
Rezeptgruppen, die selbst mit zwei Portionen die äußeren Zielgrenzen nicht
erreichen können, werden vor der Portionssuche sicher verworfen. Aus den
verbleibenden Kombinationen hält der Planer nur die drei aktuell besten im
Speicher. Bis zu drei ausgewählte Mahlzeiten werden vollständig durchsucht. Bei
vier Mahlzeiten begrenzt eine reproduzierbare, nährwertbasierte Vorauswahl den
Rechenraum, bevor die Kombinationen vollständig bewertet werden. Der gesamte
Rezeptkatalog bleibt dabei gespeichert und sichtbar. Die bestehenden
Zielbereiche und das nachvollziehbare Scoring bleiben erhalten.

Der Wochenplaner verwendet dieselben Tagesziele und Mahlzeitenrollen für drei
bis sieben Tage. Für jeden Block bewertet er passende Tagespläne zusammen mit
einer Blocklänge von ein bis drei Tagen. Nach den harten Nährwertregeln fließen
die Abweichung von den Tageszielen und die bei vollständigen NHS-Rezeptmengen
verbleibenden Portionen in die Auswahl ein. So liegen Wiederholungen bewusst
aufeinander und ein Rezept erscheint höchstens dreimal pro Woche. Es gibt
weiterhin keine eigene Wochentabelle; der Plan wird nur als API-Antwort erzeugt.
