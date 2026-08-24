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

## Bewertungsgrundsätze

- Sobald das Protein-Mindestziel erreicht ist, wird zusätzliches Protein nicht
  automatisch besser bewertet.
- Praktikable Portionsmengen sind wichtiger als das exakte Treffen eines
  einzelnen Zielwerts.
- Eine Verletzung des Kohlenhydratbereichs darf einen Vorschlag nicht allein
  ausschließen, muss aber sichtbar sein.
- Das Testprofil bewertet die Planungsqualität, nicht die gesundheitliche
  Eignung der eingegebenen Ernährungsziele.

## Noch offen

- Priorisierung mehrerer ansonsten gültiger Tagespläne
- Verhalten, wenn kein Tagesplan alle harten Regeln erfüllt
- Mahlzeitentypen und ihre Verteilung bei fünf Mahlzeiten
- erlaubte Portionsvarianten je Mahlzeit
- weitere Testprofile und unterstützte Zielbereiche
