# MVP-Validierung

Stand: 28. August 2026

## Ziel

Der Test soll zeigen, ob Personen aus der Zielgruppe PrepPilot ohne Erklärung
bedienen, einen vollständigen Wochenplan erstellen und dessen Ergebnis als
praktisch einschätzen können. Er bewertet den bestehenden MVP und dient nicht
dazu, den Testpersonen geplante Funktionen zu erklären.

## Testgruppe

Getestet wird mit drei Personen, die:

- ihre Ernährung anhand von Kalorien oder Makronährstoffen planen,
- mehrere Mahlzeiten am Tag essen oder für mehrere Tage vorbereiten,
- keine Ernährungsform oder Allergie benötigen, die der MVP noch nicht
  unterstützt,
- PrepPilot bisher nicht verwendet haben.

Die Personen werden nur als `P1`, `P2` und `P3` dokumentiert. Namen oder andere
persönliche Angaben werden nicht festgehalten.

## Vorbereitung

- PostgreSQL, Backend und Frontend nach `docs/development.md` starten.
- Prüfen, dass die Oberfläche `System bereit` anzeigt.
- Einen Browser ohne bereits erzeugten Plan öffnen.
- Stoppuhr und das Protokoll am Ende dieses Dokuments bereithalten.
- Während der Aufgabe keine Funktionen erklären und keine Bedienhinweise geben.

## Aufgabe für die Testperson

Folgender Text wird jeder Person unverändert vorgelesen oder gezeigt:

> Du möchtest für eine Woche jeden Tag denselben Ernährungsplan verwenden. Gib
> deine üblichen täglichen Kalorien- und Makronährstoffziele ein, wähle eine für
> dich passende Anzahl an Mahlzeiten und erstelle einen Wochenplan samt
> Einkaufsliste. Sage Bescheid, sobald du die Liste zum Einkaufen verwenden
> könntest.

Die Zeit beginnt nach dem Lesen der Aufgabe und endet, sobald die Person ihre
Einkaufsliste als fertig bezeichnet. Nach drei Minuten darf sie weiterarbeiten;
das Zeitkriterium gilt dann jedoch als nicht erfüllt.

## Beobachtung während der Nutzung

Ohne einzugreifen werden festgehalten:

- benötigte Zeit bis zur Einkaufsliste,
- Stellen, an denen die Person zögert oder zurückgeht,
- Fragen, die sie während der Nutzung stellt,
- Fehlversuche oder Abbruch,
- sichtbare Unsicherheit bei Zielwerten, Abweichungen oder Mengen,
- manuelle Rechnungen oder andere Hilfsmittel,
- gewünschte Änderungen am erzeugten Plan.

Technische Fehler werden mit dem sichtbaren Verhalten und den verwendeten
Eingaben notiert. Die Sitzung darf nur fortgesetzt werden, wenn ein Neustart
keinen Teil der Bedienaufgabe erklärt oder vorwegnimmt.

## Fragen nach der Aufgabe

1. Was zeigt dir der ausgewählte Plan?
2. Welche Zielabweichungen hast du erkannt?
3. Würdest du den Plan und die Einkaufsmengen ohne weitere Berechnung verwenden?
4. Wäre dieser Plan praktisch genug für einen echten Wochenversuch? Warum oder
   warum nicht?
5. Was müsstest du vor der Verwendung unbedingt ändern?

## Protokoll je Testperson

| Merkmal | Ergebnis |
| --- | --- |
| Kennung | P1 / P2 / P3 |
| Datum | |
| Gerät und Bildschirmgröße | |
| Verwendete Zielwerte und Mahlzeitenanzahl | |
| Einkaufsliste erreicht | ja / nein |
| Zeit bis zur Einkaufsliste | |
| Ohne Hilfestellung abgeschlossen | ja / nein |
| Zusätzliche Rechnung verwendet | ja / nein |
| Erkannte Abweichungen | |
| Rückfragen, Zögern oder Fehlversuche | |
| Gewünschte manuelle Änderungen | |
| Für echten Wochenversuch praktisch | ja / nein |
| Wichtigste Begründung | |

## Auswertung und Abnahme

Phase 6 ist abgeschlossen, wenn:

- alle drei Personen den primären Nutzerfluss ohne Hilfestellung abschließen,
- alle drei die Einkaufsliste ohne externen Rechner verstehen können,
- mindestens zwei Personen die Einkaufsliste innerhalb von drei Minuten
  erreichen,
- mindestens eine Person den erzeugten Plan als praktisch genug für einen
  echten Wochenversuch bewertet,
- keine ungeklärten Rechenfehler bestehen,
- blockierende Bedienprobleme vor weiteren Produktfunktionen behoben sind.

Nicht blockierende Wünsche werden getrennt von beobachteten Problemen erfasst
und erst nach der Auswertung gegen das Produkt-Backlog priorisiert.
