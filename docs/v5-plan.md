# PrepPilot V5

Stand: 4. September 2026

## Umsetzungsstand

- Abschnitt 0 ist abgeschlossen; der V4-Stand ist mit `prototype-v4` markiert.
- Abschnitt 1 ist auf `rewrite/v5-foundation` umgesetzt und automatisiert
  geprüft. Der echte lokale Start mit Docker steht noch aus.
- Als Nächstes folgt Abschnitt 2, der Lebensmittelkatalog.

## Ziel

PrepPilot V5 plant für eine Person eine vollständige Woche aus selbst
gepflegten Lebensmitteln und Rezepten. Der Schwerpunkt ist realistisches Meal
Prepping: Ein Rezept kann mehrere Portionen ergeben, eine Mahlzeit verbraucht
genau eine Portion und vorbereitete Portionen werden innerhalb derselben Woche
vollständig verwendet.

V5 ist ein fachlicher und technischer Neustart im bestehenden Repository. Alte
Implementierungen dienen als dokumentierte Lernerfahrung, nicht als Grundlage,
die schrittweise weiter umgebaut werden muss.

## Festgelegter Umfang des ersten MVP

- genau eine Person
- genau sieben zusammenhängende Tage
- Frühstück, Mittagessen und Abendessen als tägliche Mahlzeitenplätze
- persönliche Lebensmittel und persönliche Rezepte
- ein Boolean `is_meal_prep` kennzeichnet vorkochbare Rezepte
- ein Rezept speichert seine gesamte Rezeptausbeute als Portionenzahl
- jede Einplanung verbraucht genau eine Portion
- wird ein Meal-Prep-Rezept gekocht, werden alle seine Portionen in derselben
  Planwoche verwendet
- dasselbe Gericht darf am selben Tag mittags und abends vorkommen
- Meal-Prep-Portionen dürfen flexibel verteilt werden, zum Beispiel bei sechs
  Portionen an zwei Tagen mittags und abends sowie an zwei weiteren Tagen nur
  abends
- die Verteilung soll möglichst aufeinanderfolgende Tage und wenige Kochvorgänge
  begünstigen
- für alle sieben Tage gelten zunächst dieselben Nährwertziele
- nicht vorbereitete Mahlzeiten dürfen sich wiederholen oder variieren
- Planung und Ergebnis sind bei identischen Eingaben reproduzierbar

Snacks, mehrere Personen, unterschiedliche Tagesziele, Benutzerkonten und
wochenübergreifende Reste gehören nicht in den ersten V5-MVP.

## Fachliches Datenmodell

V5 verwendet weiterhin eine PostgreSQL-Datenbank. „Lebensmittel“ und „Rezepte“
sind getrennte Tabellen innerhalb derselben Datenbank, damit Beziehungen,
Transaktionen und Migrationen konsistent bleiben.

### `foods`

Ein Datensatz beschreibt ein Lebensmittel und seine Nährwerte für eine feste
Bezugsmenge.

- `id`
- `name`
- `reference_amount`, im MVP normalerweise `100`
- `base_unit`, im MVP `g` oder `ml`
- `calories_kcal`
- `protein_g`
- `carbohydrates_g`
- `fat_g`
- optionale weitere Nährwerte erst bei konkretem Bedarf
- Zeitstempel

Beispiel: Mais enthält seine Nährwerte einmal pro 100 g. Alle Rezepte, die Mais
verwenden, beziehen ihre Berechnung auf diesen Datensatz.

### `recipes`

- `id`
- `title`
- `servings` als positive ganze Rezeptausbeute
- `is_meal_prep`
- geeignete Mahlzeitenrollen
- Zubereitungsschritte
- optionale Vorbereitungs- und Kochzeit
- Zeitstempel

Nährwerte werden nicht manuell am Rezept gespeichert. Sie werden aus den
Lebensmitteln und Zutatenmengen für das gesamte Rezept berechnet und durch
`servings` geteilt, um die Werte einer Portion zu erhalten.

### `recipe_ingredients`

Die Zuordnung enthält nur die rezeptbezogenen Angaben:

- `recipe_id`
- `food_id`
- `amount`
- `unit`
- `position`

Sie enthält keine eigenen Nährwerte. Im MVP muss `unit` zur Basiseinheit des
Lebensmittels passen, damit die Berechnung eindeutig bleibt.

### `weekly_plans` und `meal_assignments`

Ein Wochenplan speichert die Zielwerte und den Zeitraum. Eine Belegung ordnet
einem der sieben Tage und einer Mahlzeitenrolle genau ein Rezept und eine
Portion zu. Die konkrete Tabellenform wird erst eingeführt, wenn Pläne dauerhaft
gespeichert werden; der Planer kann zunächst mit denselben Strukturen als
API-Ein- und Ausgabe arbeiten.

## Nährwertberechnung

Für jede Zutat wird der Anteil an der Bezugsmenge berechnet:

```text
Zutatennährwert = Lebensmittelwert * Zutatenmenge / Bezugsmenge
Rezeptgesamtwert = Summe aller Zutatennährwerte
Portionswert = Rezeptgesamtwert / Rezeptausbeute
```

Ungültige oder unvollständige Zutaten verhindern eine als vollständig
berechnet gekennzeichnete Rezeptportion. Es gibt keine stillen Ersatzwerte.

## Meal-Prep-Regeln

Harte Bedingungen:

1. Jeder Mahlzeitenplatz enthält höchstens ein Rezept.
2. Jede Belegung verbraucht genau eine Portion.
3. Ein ausgewählter Meal-Prep-Batch wird genau einmal gekocht.
4. Seine Anzahl Belegungen entspricht exakt der Rezeptausbeute.
5. Alle Portionen liegen innerhalb der gewählten sieben Tage.
6. Eine Portion wird nie doppelt verwendet.
7. Das Rezept muss für die jeweilige Mahlzeitenrolle geeignet sein.

Weiche Ziele:

- Nährwertziele möglichst gut treffen
- wenige verschiedene Kochvorgänge benötigen
- Portionen eines Batches auf möglichst zusammenhängende Tage konzentrieren
- unvorbereitete Mahlzeiten bei gleichwertigen Lösungen etwas variieren

Die genaue Gewichtung von Nährwerttreue und Kochaufwand ist noch keine
Produktentscheidung. Vor Implementierung der automatischen Optimierung wird sie
an wenigen realistischen Beispielwochen festgelegt. Bis dahin werden beide
Werte getrennt ausgegeben, damit keine willkürliche Gewichtung im Code
verschwindet.

## Spätere Mengenumrechnungen

Alltagsgrößen wie `1 Dose`, `1 Stück` oder `1 Packung` sind sinnvoll, aber nicht
Teil des ersten MVP. Eine spätere Tabelle `food_portions` kann pro Lebensmittel
eine Bezeichnung und die entsprechende Menge in der Basiseinheit speichern.

Beispiel:

```text
Mais: Nährwerte pro 100 g
Portionsdefinition: 1 Dose = 265 g
Rezeptangabe: 1 Dose
Berechnung: 265 g Mais
```

Dadurch bleibt die Nährwertquelle am Lebensmittel, während Rezepte bequemere
Einheiten verwenden können.

## Umsetzung in klaren Abschnitten

### 0. V4 abschließen

- aktuellen persönlichen-Rezepte-Branch prüfen, pushen und regulär mergen
- alte, nicht gemergte Experimente ohne Übernahme ihres Dateistands archivieren
- `prototype-v4` auf dem dadurch abgeschlossenen `main` setzen
- alten Branchbestand anschließend aufräumen

### 1. V5-Grundlage

- `rewrite/v5-foundation` vom aktualisierten `main` erstellen
- alte Fachlogik, Migrationen und Oberflächen konsequent entfernen
- React/Vite, FastAPI, PostgreSQL und Alembic als bewährte technische Grundlage
  sauber neu aufsetzen und lokale Startbefehle dokumentieren
- Healthcheck und leeren Anwendungszustand testen

### 2. Lebensmittelkatalog

- Schema und Migration für `foods`
- API zum Anlegen, Anzeigen, Bearbeiten und Löschen
- Frontend mit verständlichen numerischen Nährwertfeldern
- Validierung positiver Mengen und zulässiger Einheiten

### 3. Rezeptverwaltung

- `recipes` und `recipe_ingredients` relational modellieren
- Zutaten im Frontend aus dem Lebensmittelkatalog auswählen
- Portionenzahl und `is_meal_prep` erfassen
- Nährwerte des gesamten Rezepts und pro Portion sichtbar berechnen
- Änderungen an Lebensmitteln konsistent in Rezeptberechnungen übernehmen

### 4. Wochenmodell

- feste Woche mit sieben Tagen und den drei Mahlzeitenrollen abbilden
- zunächst Wochenpläne aus konkreten Testrezepten deterministisch erzeugen
- Verbrauch jeder Batch-Portion nachvollziehbar anzeigen
- unmögliche Wochen mit konkretem Grund ablehnen

### 5. Planungsoptimierung

- realistische Beispielwochen gemeinsam bewerten
- Priorität zwischen Nährwerttreue und Kocheffizienz festlegen
- Such- oder Optimierungsverfahren mit reproduzierbarem Ergebnis umsetzen
- Abweichungen und Kochentscheidungen im Frontend erklären

### 6. Abnahme

- Backend-, Frontend- und Browsertests
- Migration einer leeren Datenbank testen
- dokumentierte lokale Start- und Stoppbefehle auf Windows prüfen
- eine Beispielwoche mit einem Meal-Prep-Rezept über mehrere Mittag- und
  Abendessen vollständig durchspielen

## Akzeptanzbeispiel für den Kern

Ein Rezept ergibt sechs Portionen und ist für Mittag- und Abendessen geeignet.
Wird es als Meal-Prep-Gericht für die Woche gewählt, zeigt PrepPilot genau sechs
Belegungen. Zulässig wäre beispielsweise:

- Montag: Mittagessen und Abendessen
- Dienstag: Mittagessen und Abendessen
- Mittwoch: Abendessen
- Donnerstag: Abendessen

Nach Donnerstag sind alle sechs Portionen verbraucht. Es entsteht weder eine
unsichtbare siebte Portion noch ein Rest für die nächste Woche. Eine alternative
Verteilung über drei Tage mit jeweils Mittag- und Abendessen ist ebenfalls
zulässig, wenn sie zu den übrigen Wochenzielen passt.

## Bewusst außerhalb des ersten MVP

- externe Rezept- oder Lebensmitteldatenquellen
- automatische Einheitenerkennung und Packungsgrößen
- Einkaufsliste
- Vorratshaltung
- Allergene und Ernährungsformen
- Favoriten, Ausschlüsse und manueller Rezepttausch
- null bis zwei Snacks
- mehrere Personen und Haushalte
- mehrere Wochen oder Reste über Wochengrenzen
- unterschiedliche Ziele je Wochentag

## Definition of Done für V5-MVP

V5 ist als MVP abgeschlossen, wenn eine Person Lebensmittel und Rezepte selbst
pflegen, daraus eine reproduzierbare Sieben-Tage-Woche erzeugen und im Frontend
für jede Mahlzeit erkennen kann, welches Rezept und welche Batch-Portion
verwendet wird. Die angezeigten Nährwerte müssen vollständig aus den gemeinsam
genutzten Lebensmitteldaten berechnet werden, und jeder eingeplante
Meal-Prep-Batch muss innerhalb der Woche ohne verlorene oder doppelt verwendete
Portionen aufgehen.
