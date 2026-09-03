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
Rezept mit einer oder zwei ganzen Portionen eingeplant. Dasselbe Rezept wird
auch bei mehreren Quellkategorien höchstens einmal verwendet. Die Ausgabe ist
bei unverändertem Rezeptbestand und denselben Eingaben reproduzierbar.

Bis zu drei Mahlzeiten werden vollständig durchsucht. Für vier Mahlzeiten wählt
der Planer je Rolle zuerst reproduzierbar die 24 nährwertlich passendsten
Rezept-Portionsvarianten aus. So bleibt die Berechnung interaktiv; das Ergebnis
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

## Meal-Prep-Plan

Für den Wochenmodus wählt der Nutzer drei bis sieben Tage. Tagesziele und
Mahlzeitenrollen gelten zunächst für jeden Tag gleich. PrepPilot erstellt einen
einzigen reproduzierbaren Wochenvorschlag aus Blöcken von ein bis drei Tagen:

- Innerhalb eines Blocks wird derselbe vollständige Tagesplan wiederholt.
- Danach werden neue Rezepte für den nächsten Block gewählt.
- Kein Rezept erscheint öfter als dreimal innerhalb des Wochenplans.
- Unter ernährungsphysiologisch geeigneten Plänen werden Kombinationen mit
  möglichst wenig Restportionen bevorzugt.

Diese Wiederholung ist beabsichtigt: Die Gerichte eines Blocks können gemeinsam
vorbereitet werden. Die Anzeige rechnet Tagesportionen, Blocklänge, vollständige
NHS-Rezeptmengen und verbleibende Portionen zusammen. Die Zutatenliste selbst
wird weiterhin nicht skaliert oder zu einer Einkaufsliste zusammengeführt.
