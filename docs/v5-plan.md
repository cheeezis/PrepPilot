# PrepPilot V5

Stand: 4. September 2026

## Umsetzungsstand

- Abschnitt 0 ist abgeschlossen; der V4-Stand ist mit `prototype-v4` markiert.
- Abschnitt 1 ist auf `rewrite/v5-foundation` umgesetzt und automatisiert
  geprüft. Der echte lokale Start mit Docker steht noch aus.
- Abschnitt 2 ist auf `feature/food-catalog` umgesetzt und automatisiert
  geprüft. Der echte Migrationstest mit PostgreSQL steht noch aus.
- Abschnitt 3 ist auf `feature/recipe-management` umgesetzt und automatisiert
  geprüft. Der echte Migrationstest mit PostgreSQL steht noch aus.
- Als Nächstes folgt Abschnitt 4, das persistente Wochenmodell.

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
- frei wählbares Startdatum; das Enddatum liegt genau sechs Tage später
- Frühstück, Mittagessen und Abendessen als feste tägliche Mahlzeitenplätze
- der Nutzer wählt für den gesamten Plan null bis drei Snacks pro Tag; dieselbe
  Anzahl gilt an allen sieben Tagen
- persönliche Lebensmittel und persönliche Rezepte
- Meal-Prep-Rezepte können für Frühstück, Mittagessen, Abendessen und Snacks
  geeignet sein
- ein Rezept speichert seine gesamte Rezeptausbeute als Portionenzahl
- genau eine Portion kennzeichnet ein normales Einzelgericht; ab zwei Portionen
  handelt es sich automatisch um einen Meal-Prep-Batch
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
- erzeugte Wochenpläne werden mit Start- und Enddatum dauerhaft gespeichert
- ein gespeicherter Wochenplan bleibt nach einem Neustart wieder aufrufbar
- für denselben Sieben-Tage-Zeitraum gibt es genau einen gespeicherten Plan
- gespeicherte Pläne dürfen sich zeitlich nicht überschneiden
- erneutes Erzeugen ersetzt den bestehenden Plan erst nach Bestätigung

Mehrere Personen, unterschiedliche Tagesziele, Benutzerkonten und
wochenübergreifende Reste gehören nicht in den ersten V5-MVP.

## Fachliches Datenmodell

V5 verwendet weiterhin eine PostgreSQL-Datenbank. „Lebensmittel“ und „Rezepte“
sind getrennte Tabellen innerhalb derselben Datenbank, damit Beziehungen,
Transaktionen und Migrationen konsistent bleiben.

### `foods`

Ein Datensatz beschreibt ein Lebensmittel und seine Nährwerte pro `100 g` oder
`100 ml`.

- `id`
- `name`, ohne Beachtung der Groß-/Kleinschreibung eindeutig
- `base_unit`, im MVP `g` oder `ml`
- `calories_kcal`
- `protein_g`
- `carbohydrates_g`
- `fat_g`
- Zeitstempel

Alle vier Nährwertangaben sind im MVP verpflichtend und dürfen null, aber nicht
negativ sein. Weitere Nährwerte werden erst bei einem konkreten Bedarf ergänzt.

Beispiel: Mais enthält seine Nährwerte einmal pro 100 g. Alle Rezepte, die Mais
verwenden, beziehen ihre Berechnung auf diesen Datensatz.

Ein eigenes Marken- oder Produktfeld ist nicht Teil des MVP. Falls Varianten
unterschieden werden müssen, wird die Konkretisierung zunächst in den Namen
aufgenommen.

Ein Lebensmittel, das bereits als Zutat eines Rezepts verwendet wird, darf
nicht gelöscht werden. Die API und das Frontend erklären in diesem Fall,
welche Abhängigkeit das Löschen verhindert.

### `recipes`

- `id`
- `title`
- `servings` als positive ganze Rezeptausbeute; `1` bedeutet Einzelgericht und
  jeder größere Wert einen Meal-Prep-Batch
- geeignete Mahlzeitenrollen
- mindestens ein geordneter, nicht leerer Zubereitungsschritt
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

Ein Wochenplan wird im MVP dauerhaft gespeichert. Er enthält seine Zielwerte,
die gemeinsame Anzahl täglicher Snack-Plätze, ein frei wählbares Startdatum und
ein Enddatum genau sechs Tage später. Eine Belegung ordnet einem der sieben Tage
und einem Mahlzeitenplatz genau ein Rezept und eine Portion zu. Frühstück,
Mittagessen und Abendessen kommen jeweils einmal vor; null bis drei Snack-Plätze
werden als `Snack 1`, `Snack 2` und `Snack 3` unterschieden. Gespeicherte Pläne
bleiben nach einem Neustart wieder aufrufbar. Ihre Zeiträume dürfen sich nicht
überschneiden; Lücken zwischen zwei Plänen sind erlaubt. Für denselben Zeitraum
existiert höchstens ein gespeicherter Plan. Eine erneute Erzeugung ersetzt ihn
erst nach ausdrücklicher Bestätigung.

Eine komfortable Historienansicht, Auswertungen über mehrere Wochen und die
parallele Auswahl zwischen mehreren Planvorschlägen sind nicht Teil des ersten
MVP.

## Nährwertberechnung

Für alle sieben Tage gelten im MVP dieselben vier Eingaben:

- Kalorienziel
- Proteinminimum
- Kohlenhydratziel
- Fettmaximum

Ernährungsmodi oder automatisch berechnete Ziele sind nicht Teil des ersten
MVP.

Für jede Zutat wird der Anteil an 100 Basiseinheiten berechnet:

```text
Zutatennährwert = Lebensmittelwert pro 100 g/ml * Zutatenmenge / 100
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

Wenn kein Plan die Nährwertziele exakt erreicht, wird der beste Plan angezeigt,
der alle harten Bedingungen erfüllt. Seine Abweichungen werden konkret
erklärt. Die Planung wird nur abgelehnt, wenn keine Belegung sämtliche harten
Bedingungen erfüllen kann.

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
  sauber neu aufsetzen
- Healthcheck und leeren Anwendungszustand testen

### 2. Lebensmittelkatalog

- Schema und Migration für `foods`
- API zum Anlegen, Anzeigen, Bearbeiten und Löschen
- Frontend mit verständlichen numerischen Nährwertfeldern
- Validierung nichtnegativer Nährwerte und der Einheiten `g` und `ml`

### 3. Rezeptverwaltung

- `recipes` und `recipe_ingredients` relational modellieren
- Zutaten im Frontend aus dem Lebensmittelkatalog auswählen
- Portionenzahl erfassen und Meal Prep daraus eindeutig ableiten
- Nährwerte des gesamten Rezepts und pro Portion sichtbar berechnen
- Änderungen an Lebensmitteln konsistent in Rezeptberechnungen übernehmen
- Löschen verwendeter Lebensmittel verhindern und verständlich erklären

### 4. Wochenmodell

- feste Woche mit sieben Tagen, drei Hauptmahlzeiten und null bis drei
  nummerierten Snack-Plätzen pro Tag abbilden
- beliebiges Startdatum zulassen und überschneidende Pläne ablehnen
- zunächst Wochenpläne aus konkreten Testrezepten deterministisch erzeugen
- erzeugte Pläne mit Start- und Enddatum dauerhaft speichern und wieder laden
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
- lokalen Start und Stopp auf Windows prüfen
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
Portionen aufgehen. Der erzeugte Plan muss mit seinem Zeitraum gespeichert und
nach einem Neustart wieder aufrufbar sein.
