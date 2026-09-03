# Planungsregeln

Der Planer verwendet nur Nährwerte, die pro Portion am gespeicherten Rezept
stehen. Zutaten werden nicht für die Makroberechnung ausgewertet.

Eingaben:

- Kalorienziel
- Proteinminimum
- Fettmaximum
- Kohlenhydratziel

Jeder Plan enthält genau ein Frühstück, ein Mittagessen und ein Abendessen.
Jedes gewählte Rezept wird mit einer oder zwei ganzen Portionen eingeplant. Die
Ausgabe ist bei unverändertem Rezeptbestand und denselben Eingaben reproduzierbar.

Harte Regeln:

- Kalorien innerhalb von ±5 Prozent
- Protein mindestens am Ziel
- Fett zwischen 80 Prozent und 100 Prozent des Maximums

Kohlenhydrate innerhalb von ±20 Prozent sind eine weiche Regel. Kandidaten in
einem etwas weiteren äußeren Bereich können als transparente Annäherung
erscheinen. Das Scoring gewichtet Protein mit 40, Kalorien mit 30, Fett mit 20
und Kohlenhydrate mit 10 Prozent.
