# Planungsregeln

Stand: 25. August 2026

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
| Protein | mindestens 220 g | mindestens 220 g | hart |
| Fett | höchstens 71 g | 57–71 g (80–100 %) | hart |
| Kohlenhydrate | 233 g | 186–280 g (80–120 %) | weich |
| Mahlzeiten | 5 | genau 5 | hart |

Die intern berechnete Fettuntergrenze beträgt `56,8 g`. Für die Anzeige wird
sie auf `57 g` gerundet. Fachliche Vergleiche verwenden grundsätzlich den
ungerundeten Wert.

## Bedeutung der Eingaben

- **Kalorienziel:** Der eingegebene Wert ist die Mitte des harten Bereichs von
  `±5 %`.
- **Protein mindestens:** Der eingegebene Wert ist eine harte Untergrenze.
- **Fett höchstens:** Der eingegebene Wert ist die harte Obergrenze. Die harte
  Untergrenze liegt automatisch bei `80 %` dieses Werts.
- **Kohlenhydratziel:** Der eingegebene Wert ist die Mitte des weichen Bereichs
  von `±20 %`.

Die Anwendung zeigt diese unterschiedliche Bedeutung bereits bei der Eingabe
und nicht erst bei den fertigen Vorschlägen.

## Referenzprofile für die Mahlzeitenanzahl

Die Profile B bis D übernehmen zunächst sämtliche Nährwertregeln aus
Testprofil A. Nur die gewählte Mahlzeitenanzahl ändert sich. Dadurch lässt sich
die Rollen- und Portionslogik unabhängig von anderen Zielwerten prüfen.

| Profil | Mahlzeiten | Enthaltene Struktur |
| --- | ---: | --- |
| B | 3 | Basisstruktur |
| C | 4 | Basisstruktur plus ein Protein-Snack |
| A | 5 | Basisstruktur plus zwei Protein-Snacks |
| D | 6 | Fünf-Mahlzeiten-Struktur plus kleiner später Snack |

Profile mit abweichenden Nährwertzielen werden anschließend getrennt ergänzt.

## Mahlzeitenstruktur von Testprofil A

Die fünf Mahlzeitenslots orientieren sich an einem realen Tagesablauf. Die
genannten Lebensmittel sind Beispiele und keine fest vorgegebenen Inhalte.

| Slot | Rolle | Beispiele |
| --- | --- | --- |
| 1 | einfache erste Mahlzeit | Brot mit Hähnchenbrust oder Schinken |
| 2 | einfacher Protein-Snack | Skyr |
| 3 | schnelle einfache Mittagsmahlzeit | beispielsweise Rührei oder Instantnudeln |
| 4 | einfacher Protein-Snack | Proteinriegel oder Shake |
| 5 | vorbereitetes Hauptgericht | gekochtes Meal-Prep-Gericht |

## Mahlzeitenanzahl und Rollen

Der Nutzer wählt im MVP zwischen drei und sechs Mahlzeiten. Ausgangspunkt sind
drei feste Rollen; zusätzliche Mahlzeiten ergänzen diese Struktur schrittweise:

| Anzahl | Enthaltene Mahlzeitenrollen |
| ---: | --- |
| 3 | erste Mahlzeit, schnelle einfache Mittagsmahlzeit, Hauptgericht |
| 4 | Basisstruktur plus ein Protein-Snack |
| 5 | Basisstruktur plus zwei Protein-Snacks |
| 6 | Fünf-Mahlzeiten-Struktur plus ein kleiner später Snack |

Jede enthaltene Mahlzeit wird konkret geplant und bei den Nährwerten sowie der
Einkaufsliste berücksichtigt. Ein unbestimmter flexibler Mahlzeitenslot gehört
nicht zum MVP.

Die schnelle einfache Mittagsmahlzeit benötigt höchstens 15 Minuten gesamte
Zubereitungszeit. Herd, Mikrowelle und Wasserkocher dürfen verwendet werden. Die
Mahlzeit besteht aus wenigen Zutaten und einfachen Zubereitungsschritten. Sie
soll sättigender und größer als ein Snack sein, aber kleiner als das
vorbereitete Hauptgericht. Beispiele sind Rührei, gekochte Eier, Instantnudeln,
belegte Brote oder Wraps. Konkrete Größenverhältnisse werden anhand von
Beispielplänen festgelegt.

Bei sechs gewählten Mahlzeiten kommt ein zusätzlicher kleiner später Snack
hinzu, beispielsweise Linsenwaffeln. Seine konkreten Portionsregeln sind noch
offen.

## Portionsskalierung

Jede Mahlzeit besitzt eine fachlich sinnvolle Grundportion. Der Planer darf die
gesamte Mahlzeit mit einem der Faktoren `0,5`, `1,0`, `1,5` oder `2,0`
skalieren. Dabei werden alle Zutaten proportional verändert; einzelne Zutaten
werden nicht unabhängig voneinander optimiert.

Ein Shake mit einer Grundportion aus `500 ml` Milch und `45 g` Whey besteht bei
einer halben Portion entsprechend aus `250 ml` Milch und `22,5 g` Whey. Das
Mischverhältnis bleibt dadurch erhalten. Einzelne Mahlzeiten dürfen später
engere Grenzen erhalten, wenn bestimmte Faktoren unpraktikabel sind.

Die konkrete Grundportion jeder Mahlzeit wird zusammen mit den Katalogdaten
festgelegt. Der Planer darf keine Faktoren außerhalb der für eine Mahlzeit
freigegebenen Auswahl erzeugen.

## Größenordnung der Mahlzeiten

Die eingegebenen Kalorien- und Makronährstoffziele gelten für den gesamten Tag.
Einzelne Mahlzeiten erhalten im MVP keine eigenen Nährstoffziele. Trotzdem muss
die Zusammenstellung folgende Größenordnung grundsätzlich erkennen lassen:

1. Das Hauptgericht ist normalerweise die größte Mahlzeit.
2. Die erste Mahlzeit und die schnelle einfache Mittagsmahlzeit bilden die
   mittlere Größenordnung.
3. Protein-Snacks sind kleiner als vollständige Mahlzeiten.
4. Der kleine späte Snack ist die kleinste Mahlzeitenrolle.

Diese Reihenfolge ist eine Plausibilitätsregel für alltagstaugliche Pläne. Die
konkrete Bewertung von Grenzfällen wird anhand der Referenzprofile festgelegt.

## Bewertungsgrundsätze

- Protein wird als Mindestwert eingegeben und ohne automatische Rundung in die
  Planungsregel übernommen.
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

Annäherungen werden mit einem gemeinsamen, gewichteten Abweichungsscore
bewertet. Die fachliche Reihenfolge bestimmt die Stärke der Gewichte:

1. Protein
2. Kalorien
3. Fett
4. Kohlenhydrate

Die Reihenfolge ist keine absolute Hierarchie. Ein kleiner Vorteil beim Protein
darf durch deutlich größere Abweichungen bei mehreren anderen Werten
aufgewogen werden. Dadurch kann ein insgesamt passenderer Plan vor einem Plan
mit lediglich einem geringfügig besseren Proteinwert liegen. Die Abweichungen
werden relativ zum jeweiligen Eingabewert normalisiert, damit Gramm und
Kilokalorien vergleichbar in den Score eingehen.

Der MVP verwendet zunächst folgende Gewichte:

| Wert | Gewicht |
| --- | ---: |
| Protein | 40 % |
| Kalorien | 30 % |
| Fett | 20 % |
| Kohlenhydrate | 10 % |

Für jeden Wert wird eine Abweichung zwischen `0` und `1` berechnet:

- Protein: relative Unterschreitung des Minimums, bezogen auf den äußersten
  erlaubten Spielraum von 10 %. Ab dem Minimum beträgt die Abweichung `0`.
- Kalorien: absoluter Abstand zum Ziel, bezogen auf den äußersten erlaubten
  Spielraum von 10 %.
- Fett: Abstand zum gültigen Bereich von 80–100 %, bezogen auf die jeweils
  weiteren 10 Prozentpunkte bis zur äußeren Grenze. Innerhalb des gültigen
  Bereichs beträgt die Abweichung `0`.
- Kohlenhydrate: absoluter Abstand zum Ziel, bezogen auf den äußersten erlaubten
  Spielraum von 50 %.

Der Gesamtscore ist die Summe der vier gewichteten Abweichungen. Ein niedrigerer
Score ist besser. Vollständig gültige Pläne werden unabhängig von ihrem Score
immer vor Annäherungen einsortiert. Bei identischem Score entscheidet eine
stabile technische Kennung, damit dieselben Eingaben reproduzierbar dieselbe
Reihenfolge liefern.

Vor dieser Sortierung werden Kandidaten mit unbrauchbar großen Abweichungen
ausgeschlossen. Eine Annäherung muss alle folgenden äußeren Grenzen einhalten:

| Wert | Äußere Grenze für Annäherungen |
| --- | --- |
| Protein | mindestens 90 % des eingegebenen Minimums |
| Kalorien | höchstens ±10 % vom eingegebenen Ziel |
| Fett | 70–110 % der eingegebenen Obergrenze |
| Kohlenhydrate | 50–150 % des eingegebenen Ziels |

Für Testprofil A ergeben sich daraus intern mindestens `198 g` Protein,
`2.250–2.750 kcal`, `49,7–78,1 g` Fett und `116,5–349,5 g`
Kohlenhydrate. Für die Anzeige werden die Grenzen auf ganze Einheiten gerundet.
Verletzt ein Kandidat mindestens eine äußere Grenze, ist er unbrauchbar und
wird nicht vorgeschlagen. Diese Grenzen sind eine testbare Produkthypothese und
keine Aussage über die gesundheitliche Eignung der Zielwerte.

Bei unveränderten Eingaben und Katalogdaten liefert das MVP reproduzierbar
dieselbe Reihenfolge. Weitere Vorschläge, Nutzungshistorie und automatische
Abwechslung werden erst nach dem MVP betrachtet.

## Entscheidungen in späteren Phasen

Folgende Details benötigen reale Katalogdaten oder eine laufende
Planungslogik. Sie sind deshalb keine Voraussetzung für den Abschluss der
fachlichen Grundregeln:

- Phase 3: konkrete Grundportionen und gegebenenfalls engere Portionsgrenzen
- Phase 3: Katalogkategorien und konkrete Mahlzeiten für alle Rollen
- Phase 4: Grenzfälle bei den Größenverhältnissen praktisch überprüfen
- Phase 4: weitere Zielprofile ergänzen und den zunächst zuverlässig
  unterstützten Bereich ermitteln
- Phase 4: Gewichte und äußere Grenzen anhand erzeugter Pläne überprüfen
