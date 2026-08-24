# Planungsregeln

Stand: 24. August 2026

Dieses Dokument sammelt die fachlichen Regeln, anhand derer PrepPilot später
Tagespläne erzeugt und bewertet. Die Regeln werden zunächst mit konkreten
Testprofilen entwickelt. Sie beschreiben noch keine technische Umsetzung.

## Begriffe

Eine harte Regel muss erfüllt sein. Verletzt ein Tagesplan eine harte Regel,
gilt er für das betreffende Profil als ungültig.

Eine weiche Regel darf verletzt werden. Eine Abweichung verschlechtert die
Bewertung des Tagesplans und muss dem Nutzer verständlich angezeigt werden.

## Testprofil A

Das erste Referenzprofil orientiert sich an einem realen Nutzungsszenario mit
fünf Mahlzeiten pro Tag.

| Wert | Eingabe | Planungsregel | Art |
| --- | ---: | ---: | --- |
| Kalorien | 2.500 kcal | 2.375–2.625 kcal (±5 %) | hart |
| Protein | 223 g | mindestens 220 g | hart |
| Fett | 71 g | 57–71 g (80–100 %) | hart |
| Kohlenhydrate | 233 g | 186–280 g (80–120 %) | weich |
| Mahlzeiten | 5 | genau 5 | hart |

Die intern berechnete Fettuntergrenze beträgt `56,8 g`. Für die Anzeige wird
sie auf `57 g` gerundet. Fachliche Vergleiche verwenden grundsätzlich den
ungerundeten Wert.

## Mahlzeitenstruktur von Testprofil A

Die fünf Mahlzeitenslots orientieren sich an einem realen Tagesablauf. Die
genannten Lebensmittel sind Beispiele und keine fest vorgegebenen Inhalte.

| Slot | Rolle | Beispiele |
| --- | --- | --- |
| 1 | einfache erste Mahlzeit | Brot mit Hähnchenbrust oder Schinken |
| 2 | einfacher Protein-Snack | Skyr |
| 3 | konkret geplante leichte Mittagsmahlzeit | noch festzulegen |
| 4 | einfacher Protein-Snack | Proteinriegel oder Shake |
| 5 | vorbereitetes Hauptgericht | gekochtes Meal-Prep-Gericht |

Das Mittagessen wird im MVP konkret geplant und in der Einkaufsliste
berücksichtigt. Ein nicht konkret verplanter, flexibler Mahlzeitenslot ist eine
spätere Erweiterung.

Die leichte Mittagsmahlzeit wird kalt und ohne Kochen in höchstens fünf Minuten
zusammengestellt. Sie soll sättigender und größer als ein Snack sein, aber
kleiner als das vorbereitete Hauptgericht. Konkrete Kaloriengrenzen pro
Mahlzeitenrolle werden erst anhand von Beispielplänen festgelegt.

Bei sechs gewählten Mahlzeiten kann später ein zusätzlicher kleiner Snack
hinzukommen, beispielsweise Linsenwaffeln. Die genaue Regel dafür ist noch
offen.

## Bewertungsgrundsätze

- Sobald das Protein-Mindestziel erreicht ist, wird zusätzliches Protein nicht
  automatisch besser bewertet.
- Nährwerte werden intern mit ihren ungerundeten Dezimalwerten berechnet und
  summiert. Gerundet wird ausschließlich für die Anzeige.
- Praktikable Portionsmengen sind wichtiger als das exakte Treffen eines
  einzelnen Zielwerts.
- Eine Verletzung des Kohlenhydratbereichs darf einen Vorschlag nicht allein
  ausschließen, muss aber sichtbar sein.
- Das Testprofil bewertet die Planungsqualität, nicht die gesundheitliche
  Eignung der eingegebenen Ernährungsziele.

## Vorschläge und Annäherungen

PrepPilot zeigt bis zu drei Tagespläne. Vollständig gültige Pläne werden immer
vor Annäherungen angezeigt.

Existieren weniger als drei gültige Pläne, darf die Ergebnisliste mit den
besten noch praktikablen Annäherungen aufgefüllt werden. Existiert kein gültiger
Plan, wird dies ausdrücklich erklärt und PrepPilot zeigt bis zu drei
Annäherungen. Jede verletzte Regel und die zugehörige Abweichung müssen sichtbar
sein; eine Annäherung darf nicht als gültiger Plan erscheinen.

Annäherungen werden in dieser fachlichen Priorität bewertet:

1. Protein
2. Kalorien
3. Fett
4. Kohlenhydrate

Vor dieser Sortierung werden Kandidaten mit unbrauchbar großen Abweichungen
ausgeschlossen. Die konkreten Ausschlussgrenzen und die genaue Berechnung des
Scores sind noch festzulegen.

Bei unveränderten Eingaben und Katalogdaten liefert das MVP reproduzierbar
dieselbe Reihenfolge. Weitere Vorschläge, Nutzungshistorie und automatische
Abwechslung werden erst nach dem MVP betrachtet.

## Noch offen

- genaue Ausschlussgrenzen und Bewertung von Annäherungen
- erlaubte Portionsvarianten je Mahlzeit
- genaue Katalogkategorien für die fünf Mahlzeitenrollen
- konkrete Größenverhältnisse der Mahlzeitenrollen
- Regel für einen optionalen sechsten Snack
- weitere Testprofile und unterstützte Zielbereiche
