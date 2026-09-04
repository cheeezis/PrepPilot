# Planungsregeln

Der Planer verwendet nur Nährwerte, die pro Portion am gespeicherten Rezept
stehen. Zutaten werden nicht für die Makroberechnung ausgewertet.

Eingaben:

- Kalorienziel
- Proteinminimum
- Fettmaximum
- Kohlenhydratziel

Der Nutzer wählt mindestens eine Mahlzeitenrolle aus. Standardmäßig enthält der
Plan ein Frühstück, ein Mittagessen und ein Abendessen; ein Snack kann ergänzt
und jede Hauptmahlzeit abgewählt werden. Pro ausgewählter Rolle wird genau ein
Rezept mit genau einer Portion eingeplant. Ein Rezept, das für mehrere Rollen
geeignet ist, darf beispielsweise mittags und abends jeweils einmal vorkommen.
Die Ausgabe ist bei unverändertem Rezeptbestand und denselben Eingaben
reproduzierbar.

Bis zu drei Mahlzeiten werden vollständig durchsucht. Für vier Mahlzeiten wählt
der Planer je Rolle zuerst reproduzierbar die 24 nährwertlich passendsten
Rezepte aus. So bleibt die Berechnung interaktiv; das Ergebnis
ist in diesem Fall die beste gefundene Kombination innerhalb dieser Vorauswahl
und kein Beweis für das globale Optimum des gesamten Katalogs.

Harte Regeln:

- Kalorien innerhalb von ±5 Prozent
- Protein mindestens am Ziel
- Fett zwischen 80 Prozent und 100 Prozent des Maximums

Kohlenhydrate innerhalb von ±20 Prozent sind eine weiche Regel. Kandidaten in
einem etwas weiteren äußeren Bereich können als transparente Annäherung
erscheinen. Das Scoring gewichtet Protein mit 40, Kalorien mit 30, Fett mit 20
und Kohlenhydrate mit 10 Prozent.
