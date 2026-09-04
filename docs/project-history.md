# Projektgeschichte

Die Versionsnamen in diesem Dokument bezeichnen Produktphasen, keine
veröffentlichten Releases. Sie wurden rückblickend vergeben, damit die
Entscheidungen und Neustarts im bestehenden Repository nachvollziehbar bleiben.

## V1 – Haushalts- und Einkaufsassistent

Der erste Prototyp basierte auf Next.js und SQLite. Er verband Vorräte,
Rezepte, Einkauf und Packungsgrößen mit einer ersten Nährwertoptimierung.

**Ergebnis:** Der Ansatz zeigte, dass gleichzeitig Vorratshaltung,
Produktempfehlungen, Einkauf und Ernährungsplanung für einen ersten
funktionsfähigen Produktkern zu breit waren.

**Git-Markierung:** `prototype-v1`

## V2 – Tages- und Wochenplanung

Mit dem Commit `4988c9b` wurde das Projekt technisch neu aufgesetzt. React mit
Vite, FastAPI und PostgreSQL ersetzten den ersten Prototyp. Ein kuratierter
Lebensmittelbestand, Tagesplanung, Wochenplanung und eine Einkaufsliste bildeten
den neuen Schwerpunkt.

**Ergebnis:** Die technische Grundlage funktionierte, aber die Pläne waren ohne
realistische persönliche Rezepte und eine klare Meal-Prep-Logik im Alltag noch
nicht überzeugend.

## V3 – Automatisierte Lebensmittel- und Rezeptimporte

Die nächste Phase ergänzte eine Import-Inbox, TheMealDB, FoodData Central,
normalisierte Lebensmittel und eine automatische Importverarbeitung. Ein
weiterer Versuch mit Wikibooks und wiederverwendbaren Lebensmittelkonzepten
blieb bewusst außerhalb von `main`.

**Ergebnis:** Die Import- und Normalisierungsarchitektur war für den damaligen
MVP zu umfangreich. Externe Daten waren außerdem nicht verlässlich genug, um
persönlich realistische Wochenpläne zu erzeugen.

## V4 – Rezeptorientierter Planer

V4 reduzierte das Modell zunächst auf vollständige NHS-Rezepte mit Nährwerten
pro Portion. Darauf entstanden ein durchsuchbarer Rezeptkatalog und ein
flexibler Tagesplaner. Der NHS-Ansatz wurde anschließend durch selbst gepflegte
Rezepte ersetzt. Strukturierte Zutaten, Rezeptausbeute und genau eine verzehrte
Portion pro Mahlzeitenplatz bilden den letzten Stand dieser Phase.

Parallel entstanden Versuche zur wochenweisen Verteilung von Meal-Prep-Gerichten.
Sie beruhten noch auf Annahmen, die später korrigiert wurden, und wurden deshalb
nicht regulär in `main` übernommen.

**Ergebnis:** Persönliche Rezepte sind die richtige Grundlage. Meal Prep muss
jedoch von Beginn an als Wochenproblem betrachtet werden: Ein Rezept erzeugt
mehrere Portionen, jede Belegung verbraucht eine Portion und der gesamte
zubereitete Batch soll innerhalb derselben Woche sinnvoll verteilt werden.

## V5 – Persönlicher Lebensmittelkatalog und Meal-Prep-Woche

V5 ist der saubere Neustart innerhalb desselben Repositorys. Die Anwendung wird
für eine Person und genau sieben Tage entworfen. Nährwerte
gehören zu Lebensmitteln und werden von Rezepten über ihre Zutaten bezogen.
Meal-Prep-Rezepte erzeugen einen Batch, dessen Portionen vollständig auf
Mittag- und Abendessen der Woche verteilt werden.

Der verbindliche fachliche und technische Plan steht in
[`v5-plan.md`](v5-plan.md).

## Übergang von V4 zu V5

Der Code aus überholten Experimenten darf nicht erneut in die aktuelle
Anwendung gelangen. Ihre Commits sollten trotzdem in der Historie erhalten
bleiben. Der Übergang wurde deshalb so abgeschlossen:

1. `feature/custom-recipes` wurde regulär per Pull Request gemergt.
2. Die nicht gemergten Experimente wurden danach auf einem eigenen
   Archivierungsbranch mit Git-Merges der Strategie `ours` historisch
   verknüpft. Dadurch werden ihre Commits Vorfahren von `main`, während der
   Dateistand von `main` unverändert bleibt.
3. Der abgeschlossene Stand wurde nach dem Archivierungs-PR mit dem annotierten
   Tag `prototype-v4` markiert.
4. `rewrite/v5-foundation` wurde anschließend vom aktualisierten `main`
   erstellt.

Archiviert wurden:

- `docs/mvp-validation`
- `feature/food-concepts`
- `feature/weekly-prep`
- `backup/custom-recipes-before-rewrite`

Bereits gemergte Branches benötigen keinen zusätzlichen Archivierungsmerge.
Nach der Verknüpfung können die alten Branch-Referenzen entfernt werden, ohne
dass ihre Commits verloren gehen.
