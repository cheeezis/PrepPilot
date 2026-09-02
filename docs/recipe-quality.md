# Qualität des ersten Rezeptbestands

Stand: 2. September 2026

## Was „Rezeptqualität“ im MVP bedeutet

Ein Rezept ist für PrepPilot verwendbar, wenn es vollständig importiert werden
kann und im Frontend verständlich dargestellt wird. Dafür braucht es:

- einen Titel und eine belastbare Portionszahl
- Kalorien, Protein, Kohlenhydrate und Fett pro Portion
- mindestens eine Zutat
- mindestens einen Zubereitungsschritt
- Quell-URL, Lizenz und Attribution

Das ist keine Geschmacksbewertung und kein Sterne-Rating.

## Ergebnis der technischen Prüfung

Der kontrollierte Importlauf vom 2. September 2026 hat alle zehn freigegebenen
NHS-Rezepte ohne Ablehnung verarbeitet. Nach der verbesserten Aufbereitung
besitzen sie jeweils 4 bis 6 sichtbare Methodenschritte statt eines einzigen
zusammengeklebten Textblocks. Zutaten, Portionszahl, vier Makronährwerte und
Quellenangaben sind bei allen zehn Rezepten vorhanden.

Der zweite identische Lauf meldet zehn unveränderte Rezepte. Damit bleibt der
Import idempotent und erzeugt keine Duplikate.

## Wie die Schritte entstehen

Der Importer übernimmt vorrangig die nummerierte Methodenliste, die auf der
NHS-Seite sichtbar ist. Darin enthaltene Hinweise bleiben beim zugehörigen
Schritt. Falls eine Seite diese Liste nicht liefert, verwendet der Importer die
strukturierten `recipeInstructions` als Rückfall.

Eine freie Zerlegung an Satzzeichen findet nicht statt. Nur bereits getrennte
Einträge, Zeilen oder eindeutige Nummernmarker werden als Schrittgrenzen
verwendet.

## Transparente Ablehnungen

Unvollständige Rezepte werden weiterhin nicht in `recipes` gespeichert. Der
Importbericht zeigt im Frontend jetzt zusätzlich die betroffene Quellseite und
einen konkreten Grund, zum Beispiel ein fehlendes Pflichtfeld.

## Bewusste Grenzen

- Die Rezepte und Zubereitungsschritte bleiben in der Quellsprache Englisch.
- Optionale NHS-Hinweise bleiben Bestandteil des zugehörigen Schritts.
- Zutaten werden noch nicht normalisiert oder in Lebensmittel zerlegt.
- Eine Verständlichkeitsprüfung mit weiteren Nutzern steht noch aus.
