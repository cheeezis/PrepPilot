# Datenmodell

Das MVP verwendet ein gemeinsames Modell für einfache Lebensmittel, Snacks,
Shakes und gekochte Gerichte. Eine Mahlzeit besteht aus einem oder mehreren
Lebensmitteln und kann in mehreren Rollen eines Tagesplans verwendet werden.

## Tabellen

- `foods`: Lebensmittel mit optionaler Marke, Bezugsgröße `g` oder `ml`, den
  vier MVP-Nährwerten pro 100 Einheiten und Angaben zur Datenherkunft
- `food_aliases`: bestätigte Zuordnungen externer Zutatenbezeichnungen zu
  internen Lebensmitteln
- `food_portions`: quellengestützte Umrechnung von Haushaltsmaßen oder
  Stückzahlen eines Lebensmittels in Gramm
- `meals`: Mahlzeiten mit Name, Zubereitungszeit, kurzer Anleitung, optionaler
  Portionszahl des Quellrezepts und Angaben zur Datenherkunft
- `meal_ingredients`: Rechenmenge eines Lebensmittels in der Grundportion einer
  Mahlzeit sowie optional die ursprüngliche Mengenangabe des Quellrezepts
- `meal_roles`: mögliche Rollen einer Mahlzeit im Tagesplan

Die Rollen sind erste Mahlzeit, leichte Mittagsmahlzeit, Protein-Snack,
Hauptgericht und später Snack. Nährwerte einer Mahlzeit werden immer aus ihren
Zutaten berechnet und nicht zusätzlich gespeichert.

Bei importierten Rezepten bleibt beispielsweise `1 chopped` als Quellenangabe
erhalten. Für die Nährwertberechnung wird sie anhand der zum Lebensmittel
gespeicherten Portionen in Gramm umgerechnet. Externe Portionsangaben werden
übernommen; fehlende Kochannahmen liegen als nachvollziehbare Katalogdaten vor.

## Bewusste Grenzen

Generische und markenspezifische Lebensmittel nutzen dieselbe Struktur; eine
fehlende Marke kennzeichnet ein generisches Lebensmittel. Preise,
Packungsgrößen, Bilder, Allergene sowie Zucker, Ballaststoffe und Salz gehören
nicht zum MVP-Datenmodell.

Jede Mahlzeit besitzt zunächst genau eine Grundportion. Der Planer darf diese
später mit den Faktoren `0.5`, `1.0`, `1.5` oder `2.0` skalieren.

## Datenqualität

Importierte Lebensmittel werden lokal gespeichert und behalten Quelle,
Quellenreferenz und Abrufzeitpunkt. Akzeptierte Quellen werden automatisiert
validiert; eine manuelle Prüfung ist nur für markenspezifische Sonderfälle,
Auffälligkeiten und Stichproben vorgesehen.

Ein Lebensmittel-Alias ist innerhalb seiner Quelle über den normalisierten
Namen eindeutig. Die Originalbezeichnung bleibt zur Nachvollziehbarkeit
erhalten. Nur erfolgreiche Zuordnungen werden gespeichert; unbekannte oder
unsichere Zutaten erzeugen im MVP keinen unvollständigen Alias.
