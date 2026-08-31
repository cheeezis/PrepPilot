# Produkt- und Entwicklungs-Roadmap

Stand: 31. August 2026

Diese Roadmap führt PrepPilot von der Produktidee zu einem technisch vollständigen
Minimum Viable Product (MVP), also der kleinsten sinnvoll nutzbaren
Produktversion. Die
Phasen bauen aufeinander auf. Eine Phase gilt erst als abgeschlossen, wenn ihr
überprüfbares Abnahmekriterium erfüllt ist. Noch nicht priorisierte Ideen nach
dem MVP stehen getrennt in `docs/product-backlog.md`.

Der technische MVP umfasst die Phasen 0 bis 5. Externe Nutzertests bleiben eine
sinnvolle spätere Validierung, sind aber keine künstliche Voraussetzung für den
Abschluss dieser Roadmap. Als erster Post-MVP-Schwerpunkt ist Phase 6A aus dem
Backlog priorisiert. Weitere Produktentwicklung wird weiterhin bewusst erst vor
Beginn des jeweiligen Abschnitts festgelegt.

## Aktueller Stand

| Phase | Ergebnis | Status |
| --- | --- | --- |
| 0 | Produkt klar ausgerichtet | abgeschlossen |
| 1 | Regeln für einen guten Tagesplan festgelegt | abgeschlossen |
| 2 | Technisches Grundgerüst lauffähig | abgeschlossen |
| 3 | Lebensmittel- und Mahlzeitendaten verfügbar | abgeschlossen |
| 4 | Tagesplaner nutzbar | abgeschlossen |
| 5 | Wochenplan und Einkaufsliste nutzbar | abgeschlossen |
| 6A | Externe Rezepte sicher aufnehmen und normalisieren | abgeschlossen |
| 6B | Normalisierte Rezepte kontrolliert veröffentlichen | abgeschlossen |

## Phase 0: Produkt ausrichten

**Ziel:** Es ist eindeutig, für wen PrepPilot welches Problem löst und was der
erste Produktumfang bewusst nicht leistet.

**Umfang:**

- Problemstatement, Zielgruppe und Produktversprechen festlegen
- primären Nutzerfluss definieren
- MVP und bewusste Nicht-Ziele abgrenzen
- messbare Erfolgskriterien formulieren

**Abnahme:** Die Produktdefinition in `docs/product.md` ist gemeinsam bestätigt.

**Status:** abgeschlossen

## Phase 1: Regeln für einen guten Tagesplan festlegen

**Ziel:** Vor der technischen Umsetzung ist verständlich, wann ein Tagesplan
gültig, praktikabel oder nur eine Annäherung ist.

**Umfang:**

- ein reales Referenzprofil mit Tageszielen und Mahlzeitenanzahl definieren
- Referenzprofile für drei bis sechs Mahlzeiten definieren
- harte und weiche Regeln für Kalorien und Makronährstoffe unterscheiden
- grundlegende Mahlzeitenrollen beschreiben
- grundlegende Portionsskalierung und Größenordnung der Mahlzeiten festlegen
- Priorität von Protein, Kalorien, Fett und Kohlenhydraten festlegen
- zulässige Annäherungen, Ausschlussgrenzen und ihre Reihenfolge festlegen
- Rundungs- und Transparenzregeln bestimmen

**Abnahme:** Nährwertsummen und Mahlzeitenstrukturen können anhand von
`docs/planning-rules.md` eindeutig als gültig, Annäherung oder unbrauchbar
bewertet und nachvollziehbar geordnet werden. Die Regeln reichen aus, um
Datenmodell und Planungslogik zu entwickeln. Datenabhängige Details dürfen in
den dafür vorgesehenen Entwicklungsphasen überprüft und angepasst werden.

**Status:** abgeschlossen

Konkrete Grundportionen und Katalogkategorien folgen in Phase 3. Weitere
Zielprofile und Grenzfälle werden zusammen mit der Planungslogik in Phase 4
getestet.

## Phase 2: Technisches Grundgerüst aufbauen

**Ziel:** Frontend, Backend und Datenbank bilden ein reproduzierbares, testbares
Fundament, ohne bereits Produktfunktionen vorwegzunehmen.

**Umfang:**

- ergänzende Entwicklungswerkzeuge und unterstützte Versionen auswählen
- minimale Monorepo-Struktur für Frontend und Backend festlegen
- React-/TypeScript-Frontend lokal starten
- FastAPI-Backend lokal starten
- PostgreSQL lokal bereitstellen und mit dem Backend verbinden
- einen einfachen Systemcheck zwischen Frontend, Backend und Datenbank einrichten
- grundlegende Formatierung, Typprüfung und Tests ausführbar machen
- lokale Einrichtung nachvollziehbar dokumentieren

**Abnahme:** Nach einer frischen Einrichtung lassen sich alle drei
Anwendungsteile starten. Das Frontend erreicht den Backend-Systemcheck, das
Backend erreicht PostgreSQL und alle grundlegenden Qualitätsprüfungen bestehen.

**Status:** abgeschlossen

Bestätigte Architekturentscheidungen stehen in `docs/architecture.md`.

## Phase 3: Daten- und Kataloggrundlage schaffen

**Ziel:** PrepPilot besitzt einen kleinen, verlässlichen internen Datenbestand,
aus dem sich realistische Tagespläne bilden lassen.

**Umfang:**

- Lebensmittel, Nährwerte, Mahlzeiten und normalisierte Zutatenmengen
  modellieren
- Datenbanktabellen und nachvollziehbare Migrationen anlegen
- generische und markenspezifische Lebensmittel unterscheiden
- Anforderungen an Datenqualität, Einheiten, Herkunft und Freigabe festlegen
- externe Datenquellen fachlich und rechtlich bewerten
- geeignete Lebensmittel und Nährwerte nachvollziehbar aus FoodData Central,
  Open Food Facts oder Herstellerangaben auswählen
- sämtliche Zutatenmengen des freigegebenen Katalogs direkt in Gramm oder
  Millilitern kuratieren
- den versionierten Katalog reproduzierbar in die Datenbank laden
- einen kleinen Katalog aus einfachen Mahlzeiten, Snacks und Hauptgerichten
  bereitstellen
- passende Katalogkategorien, Grundportionen und erlaubte Portionsfaktoren
  festlegen
- konkrete Mahlzeiten für alle Rollen einschließlich des späten Snacks
  bereitstellen
- Katalogdaten gegen mehrere repräsentative Zielprofile prüfen

**Abnahme:** Die Datenbank kann reproduzierbar neu aufgebaut werden. Der
freigegebene Katalog enthält vollständige, nachvollziehbare Daten und ermöglicht
für jedes unterstützte Testprofil manuell mindestens zwei praktikable
Tagespläne. Die Planung benötigt keine Live-Verbindung zu einer externen
Lebensmittel-API und keine Verarbeitung externer Rezeptmaße.

**Status:** abgeschlossen

Das bestätigte MVP-Datenmodell steht in `docs/data-model.md`.

## Phase 4: Tagesplaner umsetzen

**Ziel:** Ein Nutzer erhält aus seinen Tageszielen zwei bis drei
nachvollziehbare Tagespläne und kann einen davon auswählen.

**Umfang:**

- Kalorien, Protein, Fett, Kohlenhydrate und Mahlzeitenanzahl erfassen
- Mahlzeiten und praktikable Portionen zu Tagesplänen kombinieren
- gültige Pläne und transparente Annäherungen bewerten
- zwei bis drei reproduzierbare Vorschläge anzeigen
- Nährwerte je Mahlzeit und für den gesamten Tag darstellen
- festgelegte Ausschlussgrenzen und Bewertungslogik anhand weiterer
  Zielprofile und realer Katalogdaten überprüfen
- Planungslogik und zentrale Grenzfälle automatisiert testen

**Abnahme:** Alle unterstützten Testprofile liefern reproduzierbare und fachlich
erklärbare Ergebnisse. Ein Nutzer kann ohne zusätzliche Berechnung einen
Tagesplan auswählen und jede relevante Zielabweichung erkennen.

**Status:** abgeschlossen

## Phase 5: Wochenplan und Einkaufsliste umsetzen

**Ziel:** Aus dem ausgewählten Tagesplan entsteht ein praktisch verwendbarer
Plan samt Einkauf für sieben Tage.

**Umfang:**

- ausgewählten Tagesplan für sieben Tage darstellen
- Zutatenmengen über alle Mahlzeiten und Tage korrekt aggregieren
- Einheiten und Mengen verständlich ausgeben
- Einkaufsliste auf mobilen und größeren Bildschirmen nutzbar machen
- vollständigen Nutzerfluss automatisiert testen

**Abnahme:** Der vollständige Ablauf von der Zieleingabe bis zur Einkaufsliste
ist ohne externe Berechnung durchführbar. Nährwerte und Einkaufsmengen stimmen
rechnerisch mit dem gewählten Plan überein.

**Status:** abgeschlossen

## Phase 6A: Import-Inbox und Zutaten-Normalisierung

**Ziel:** PrepPilot kann strukturierte externe Rezepte verlustfrei in einem
getrennten Importbereich von PostgreSQL aufnehmen und reproduzierbar
normalisieren. Ein Import endet entweder als vollständig normalisierter
Kandidat oder mit konkreten, manuell bearbeitbaren Prüfgründen. Importdaten
gelangen in dieser Phase noch nicht in den produktiven Mahlzeitenkatalog.

**Fachliche Datenobjekte:**

- `recipe_imports` bewahrt Quelle, externe Kennung, Abrufzeitpunkt,
  unveränderte Rohdaten, Inhalts-Hash, deklarierte Portionenzahl und den
  Rezeptstatus auf.
- `recipe_import_ingredients` bewahrt jede originale Zutatenzeile sowie das
  Parsing-Ergebnis, eine mögliche Lebensmittelzuordnung, die normalisierte
  Menge und einen möglichen Prüfgrund auf.
- `food_aliases` ordnet ausdrücklich bestätigte externe Bezeichnungen einem
  internen Lebensmittel zu. Unscharfe Suchtreffer werden nicht selbstständig
  als Alias gespeichert.
- `food_measure_defaults` hält nachvollziehbare, wiederverwendbare
  lebensmittelspezifische Standardmengen für Stück, Ei, Zehe, Scheibe und
  ähnliche Maße fest.
- Prüfentscheidungen halten fest, ob eine Zuordnung korrigiert, ein Alias oder
  Standard ergänzt, eine rezeptbezogene Menge verwendet, eine fachlich
  irrelevante Zeile ausgenommen oder das Rezept verworfen wurde.

Die genauen Tabellenspalten und technischen Namen werden bei der Umsetzung
festgelegt. Verbindlich ist die Trennung von unveränderten Quelldaten,
abgeleiteten Normalisierungsergebnissen und manuellen Entscheidungen.

**Statusfluss:**

1. Ein idempotent aufgenommener Import beginnt als `received`.
2. Die deterministische Verarbeitung führt entweder zu
   `ready_for_catalog_review` oder `needs_review`.
3. Eine Zutatenzeile ist dabei `normalized`, `needs_review` oder nach einer
   ausdrücklichen manuellen Entscheidung `excluded`.
4. Nach einer Korrektur wird ein Import vollständig erneut verarbeitet und
   endet wieder als `ready_for_catalog_review` oder `needs_review`.
5. Ein Bearbeiter kann ein Rezept endgültig als `rejected` markieren.

`ready_for_catalog_review` bedeutet ausschließlich, dass alle benötigten
Lebensmittel und Mengen normalisiert sind. Es ist keine Freigabe für den
Planer. Mahlzeitenrolle, Grundportion, Portionsfaktoren, Zubereitungszeit und
Anleitung bleiben Gegenstand einer späteren Katalogprüfung.

**Normalisierungsregeln:**

- Originalbezeichnungen und Originalmengen bleiben immer erhalten.
- Eine automatische Lebensmittelzuordnung benötigt einen eindeutigen internen
  Namen oder einen bestätigten Alias. Fuzzy Matching darf nur Vorschläge für
  die manuelle Prüfung liefern.
- `g`, `kg`, `ml` und `l` werden direkt in die Basiseinheit des zugeordneten
  Lebensmittels umgerechnet.
- Teelöffel und Esslöffel verwenden zunächst die bestehenden globalen
  PrepPilot-Regeln von `5 g` beziehungsweise `5 ml` und `15 g`
  beziehungsweise `15 ml`, abhängig von der Basiseinheit des Lebensmittels.
- Stückangaben benötigen einen passenden Eintrag in
  `food_measure_defaults`. Einen generischen Gewichts-Fallback gibt es nicht.
- Zwischen Masse und Volumen wird ohne ausdrücklich hinterlegte Regel nicht
  umgerechnet.
- Roh, gegart, trocken, zubereitet und abgetropft werden als fachlich
  relevante Zustände behandelt und nicht durch Textbereinigung entfernt.
- Die deklarierte Portionenzahl muss positiv und eindeutig sein. Erst danach
  werden Gesamtmengen auf eine Grundportion bezogen.
- Eine Zutatenzeile darf nur manuell als `excluded` markiert werden, wenn sie
  für Nährwertberechnung und Einkauf fachlich nicht relevant ist. Die
  Originalzeile bleibt weiterhin erhalten.

Typische maschinenlesbare Prüfgründe sind `unknown_food`, `ambiguous_food`,
`unsupported_unit`, `missing_measure_default`, `invalid_or_ranged_quantity`,
`incompatible_measurement` und `missing_serving_count`.

**Umfang:**

- genau ein klar definiertes Eingangsformat hinter einer austauschbaren
  Quellenschnittstelle
- mehrere versionierte Beispiel-Payloads mit erfolgreichen und bewusst
  unvollständigen Importfällen
- Rohdaten, Herkunft und Normalisierungsergebnisse in PostgreSQL speichern
- deterministische, unabhängig von einer Live-API testbare Verarbeitung
- eine kleine interne Backend-Schnittstelle zum Lesen der Prüfwarteschlange,
  Speichern der festgelegten Prüfentscheidungen und erneuten Verarbeiten
- FoodData Central zunächst nur als optionale Recherchequelle für manuell
  bestätigte Lebensmittel- oder Portionsstandards behandeln

**Bewusste Nicht-Ziele:**

- Live-Anbindung an einen konkreten Rezeptanbieter
- mehrere Quellenadapter
- automatische Anlage neuer Lebensmittel
- Veröffentlichung normalisierter Kandidaten in `meals`
- Nutzung importierter Rezepte durch den Planer
- öffentliche Importfunktion oder ausgearbeitete Admin-Oberfläche
- automatische Ableitung von Mahlzeitenrollen oder Portionsfaktoren
- LLM-basierte Entscheidungen oder automatische Freigaben

**Abnahme:**

- Derselbe externe Datensatz kann mehrfach verarbeitet werden, ohne doppelte
  Importdatensätze zu erzeugen.
- Rohdaten, Quelle und sämtliche manuellen Entscheidungen bleiben
  nachvollziehbar.
- Mindestens zwei kontrollierte Beispielrezepte erreichen vollständig
  `ready_for_catalog_review`.
- Weitere Beispiele landen mit unterschiedlichen konkreten Gründen in
  `needs_review`.
- Ein bestätigter Alias, ein Stückstandard und eine rezeptbezogene Korrektur
  können jeweils gespeichert werden und führen nach erneuter Verarbeitung zum
  erwarteten Ergebnis.
- Kein unvollständiger oder nur normalisierter Import erscheint in `foods`,
  `meals` oder in der Planungslogik.
- Sämtliche automatisierten Prüfungen funktionieren ohne erreichbare externe
  API.

**Status:** abgeschlossen

## Phase 6B: Normalisierte Rezepte kontrolliert veröffentlichen

**Ziel:** Ein vollständig normalisierter Rezeptimport kann nach ausdrücklicher
fachlicher Bestätigung als produktive Mahlzeit veröffentlicht und anschließend
vom Planer verwendet werden. Seed-Mahlzeiten und importierte Mahlzeiten bleiben
dabei dauerhaft unterscheidbar.

**Umfang:**

- Mahlzeitenherkunft `curated_seed` oder `recipe_import` speichern
- importierte Mahlzeiten eindeutig mit ihrem Rezeptimport verbinden
- Name, stabile Katalogkennung, Zubereitungszeit, Anleitung, Rollen und erlaubte
  Portionsfaktoren bei der Freigabe ausdrücklich bestätigen
- ausschließlich Importe mit `ready_for_catalog_review` freigeben
- normalisierte Zutaten einer Grundportion transaktional in den produktiven
  Katalog übernehmen; mehrfach vorkommende Lebensmittel zusammenfassen
- wiederholte Freigabe desselben Imports ohne Duplikat beantworten
- Katalog-Seed so begrenzen, dass nur versionierte Seed-Mahlzeiten ersetzt und
  importierte Mahlzeiten erhalten bleiben
- freigegebene Mahlzeiten über den bestehenden Datenbankkatalog für die
  Planungslogik verfügbar machen

**Bewusste Nicht-Ziele:**

- nachträgliches Bearbeiten oder Zurückziehen veröffentlichter Mahlzeiten
- automatische Ableitung von Rollen oder Portionsfaktoren
- automatische Freigabe durch eine externe API oder ein LLM
- öffentliche oder ausgearbeitete Administrationsoberfläche
- Live-Anbindung an einen Rezeptanbieter

**Abnahme:**

- Ein unvollständiger Import kann nicht veröffentlicht werden.
- Ein vollständiger Import erzeugt genau eine Mahlzeit mit vollständigen
  Zutaten, Rollen und Portionsfaktoren.
- Eine wiederholte identische Freigabe erzeugt kein Duplikat.
- Ein erneuter Seed erhält die importierte Mahlzeit und ihre Zuordnungen.
- Der bestehende Datenbankkatalog liefert die importierte Mahlzeit an die
  Planungslogik aus.
- Migration, Freigabe und erneuter Seed sind gegen PostgreSQL geprüft.

**Status:** abgeschlossen

## Phase 6C: Erster Live-Quellenadapter

**Ziel:** Ein einzelnes Rezept kann anhand seiner stabilen externen Kennung
kontrolliert von TheMealDB abgerufen und über dieselbe deterministische Pipeline
in die Import-Inbox aufgenommen werden. Die externe Quelle bleibt vollständig
von Katalog und Planer getrennt.

**Umfang:**

- genau ein TheMealDB-Adapter mit konfigurierbarem API-Schlüssel, Basis-URL und
  Abruf-Timeout
- interner Endpunkt zum Abruf genau eines Rezepts anhand seiner numerischen
  TheMealDB-ID
- unverändertes TheMealDB-Rezeptobjekt als Rohdaten und daraus getrennt
  abgeleitete interne Zutatenzeilen speichern
- bis zu 20 Zutaten-/Maßpaare übernehmen; einfache ganze, dezimale und
  gebrochene Mengen deterministisch lesen
- unbekannte Zutaten, nicht sicher interpretierbare Maße und die bei TheMealDB
  fehlende Portionenzahl wie bisher in die Prüfwarteschlange leiten
- identische erneut abgerufene Inhalte über Quelle, externe Kennung und
  Inhalts-Hash ohne Duplikat beantworten
- Nicht-vorhanden-, ungültige-Antwort- und Nicht-erreichbar-Fälle getrennt
  behandeln
- Adaptertests vollständig ohne Live-Netzwerk ausführen und einen echten Abruf
  zusätzlich gegen die lokale PostgreSQL-Inbox prüfen

**Bewusste Nicht-Ziele:**

- Suche, Zufallsauswahl, Kategorien oder Massenimport von TheMealDB
- regelmäßiger oder automatischer Hintergrundabruf
- weitere Rezeptquellen
- automatische Anlage unbekannter Lebensmittel oder unsichere Umrechnungen
- automatische Katalogfreigabe, Rollenwahl oder Portionsfaktoren
- TheMealDB als Laufzeitabhängigkeit des Planers

**Abnahme:**

- Eine numerische TheMealDB-ID erzeugt einen nachvollziehbaren Import mit der
  Quelle `themealdb` und der externen ID.
- Die empfangenen Quelldaten bleiben erhalten; der Adapter erzeugt daraus das
  bestehende interne Inbox-Format.
- Ein wiederholter Abruf desselben unveränderten Rezepts erzeugt keinen zweiten
  Importdatensatz.
- Unvollständige Angaben landen mit konkreten Prüfgründen in `needs_review` und
  nicht im produktiven Katalog.
- Adapter, HTTP-Endpunkt und Fehlerfälle sind ohne externe API testbar.
- Der echte Abruf des TheMealDB-Rezepts `52771` wurde am 31. August 2026 gegen
  die lokale PostgreSQL-Inbox geprüft.

**Status:** abgeschlossen

## Phase 6D: Reale Imports und Normalisierung härten

**Ziel:** Die Importpipeline wird anhand einer kleinen, gemischten Stichprobe
echter TheMealDB-Rezepte praktisch geprüft. Wiederkehrende sichere Zuordnungen
werden reproduzierbar, fachlich relevante Lücken bleiben sichtbar, und ein
geeigneter realer Kandidat durchläuft den vollständigen Weg bis zum Planer.

**Umfang:**

- insgesamt acht reale TheMealDB-Rezepte mit 81 Zutatenzeilen kontrolliert in
  die lokale PostgreSQL-Inbox aufnehmen
- Prüfgründe je Rezept auswerten, ohne unbekannte Zutaten automatisch anzulegen
  oder unsichere Begriffe zu erraten
- bestätigte Aliase und belegte lebensmittelspezifische Maße im versionierten
  Katalog hinterlegen und beim Seed idempotent in PostgreSQL übernehmen
- manuell angelegte Aliase und Maße bei einem Seed weiterhin erhalten
- Pflanzenöl, Pekannüsse und Himbeeren mit nachvollziehbaren Nährwertquellen zum
  kleinen Lebensmittelkatalog ergänzen
- Banana Pancakes aus TheMealDB anhand der Originalquelle auf zwei Portionen
  festlegen; nur Backpulver und Vanille als ernährungsseitig unerhebliche
  Zutaten ausdrücklich ausschließen
- den vollständig normalisierten Kandidaten als Frühstück veröffentlichen und
  anschließend Seed, Datenbankkatalog und Nährwertberechnung prüfen

**Bewusste Nicht-Ziele:**

- alle Zutaten der Stichprobe in den Lebensmittelkatalog aufnehmen
- generische Begriffe wie `Chicken`, `Bread` oder konkrete Reisarten auf einen
  nur ungefähr passenden vorhandenen Katalogeintrag abbilden
- relevante Saucen, Nüsse, Früchte oder Öle aus der Nährwertberechnung
  ausschließen, nur um ein Rezept freigeben zu können
- automatische Freigabe weiterer Stichprobenrezepte
- Massenimport, Zeitplan oder weitere Quellenadapter

**Abnahme:**

- Alle acht Rezepte bleiben mit Rohdaten, externer ID und konkreten
  Prüfgründen nachvollziehbar.
- Der erneute Seed erzeugt bestätigte Katalog-Aliase und Maße reproduzierbar,
  löscht aber keine manuell geprüften Ergänzungen.
- Der Banana-Pancakes-Import normalisiert pro Portion Banane, Ei, Pflanzenöl,
  Pekannüsse und Himbeeren auf Gramm beziehungsweise Milliliter.
- Das veröffentlichte Rezept bleibt nach einem erneuten Seed erhalten und wird
  mit den übrigen Mahlzeiten aus dem produktiven Datenbankkatalog geladen.
- Der vollständige reale Ablauf ist zusätzlich als netzwerkunabhängiger Test
  mit einem versionierten TheMealDB-Payload abgesichert.

**Status:** abgeschlossen

## Phase 6E: FoodData-Central-Import für Lebensmittel

**Ziel:** Generische Lebensmittel können anhand einer stabilen FoodData-Central-
ID in einen getrennten Prüfbereich importiert und erst nach ausdrücklicher
Bestätigung in den produktiven Lebensmittelkatalog übernommen werden.

**Umfang:**

- eigene Tabelle `food_imports` für Quelle, externe ID, Abrufzeitpunkt,
  unveränderte Rohdaten, Inhalts-Hash, Kandidatenwerte und Prüfgründe
- genau ein FoodData-Central-Detailadapter für numerische FDC-IDs; keine
  automatische Suche oder Trefferauswahl
- zunächst ausschließlich `Foundation`- und `SR Legacy`-Datensätze als
  generische Lebensmittel akzeptieren
- Energie, Protein, Fett, Gesamt-Kohlenhydrate und Ballaststoffe anhand stabiler
  FDC-Nährstoffkennungen auslesen
- europäische Kohlenhydrate reproduzierbar als Gesamt-Kohlenhydrate minus
  Ballaststoffe berechnen; fehlende oder widersprüchliche Werte zurückstellen
- vollständige Kandidaten ausdrücklich mit Katalogschlüssel und Anzeigename
  als gramm-basiertes Lebensmittel freigeben
- importierte und Seed-Lebensmittel dauerhaft unterscheiden; erneuter Seed darf
  importierte Lebensmittel nicht löschen
- interne Endpunkte zum Abruf der Food-Inbox, FDC-Import und Freigabe

**Bewusste Nicht-Ziele:**

- automatische Auswahl eines Suchtreffers anhand eines freien Zutatentexts
- Open Food Facts, Markenprodukte oder Barcode-Import
- Volumenlebensmittel ohne bestätigte Dichte
- automatisches Erzeugen von Aliasen oder Portionsstandards
- ungeprüftes Schreiben externer Daten direkt in `foods`
- Massenimport oder regelmäßige Synchronisierung

**Abnahme:**

- Ein FDC-Datensatz wird mit unveränderten Rohdaten idempotent in der Food-Inbox
  gespeichert.
- Fehlende Ballaststoffe oder andere Pflichtwerte führen zu `needs_review` und
  verhindern die Katalogfreigabe.
- Ein vollständiger Kandidat erzeugt bei Freigabe genau ein Lebensmittel mit
  nachvollziehbarer FDC-Referenz und europäischer Kohlenhydratdefinition.
- Wiederholter Import und wiederholte Freigabe erzeugen keine Duplikate.
- Das importierte Lebensmittel bleibt nach einem Seed erhalten und wird vom
  produktiven Datenbankkatalog geliefert.
- FDC `169230` wurde als `garlic` gegen die lokale PostgreSQL-Datenbank geprüft.

**Status:** abgeschlossen

## Phase 6F: Kontrollierter Ausbau des Datenbestands

**Ziel:** Die in Phase 6E geschaffene Food-Inbox wird mit einem ersten
größeren, weiterhin einzeln nachvollziehbaren Datenbatch praktisch genutzt.
Gleichzeitig wächst die Rezept-Inbox auf einen Bestand, an dem sich die
nächsten Normalisierungslücken belastbar priorisieren lassen.

**Umfang und Ergebnis:**

- 29 vorab geprüfte Foundation- oder SR-Legacy-Datensätze wurden anhand fester
  FDC-IDs importiert und ausdrücklich als generische Lebensmittel freigegeben.
- Der produktive Lebensmittelkatalog enthält damit 54 Einträge: 24 kuratierte
  Seed-Lebensmittel und 30 kontrollierte Food-Imports einschließlich des in
  Phase 6E übernommenen Knoblauchs.
- 31 fachlich eindeutige Aliase sowie der durch FDC 169230 belegte Standard
  `1 clove = 3 g` wurden ergänzt. Die unbekannten Zutaten in den ursprünglichen
  acht Rezepten sanken nach Wiederverarbeitung von 66 auf 21.
- Ein unvollständiger Coconut-Milk-Kandidat wurde wegen fehlender Ballaststoffe
  nicht übernommen; stattdessen wurde ein vollständiger generischer Datensatz
  ausgewählt.
- Zwölf weitere feste TheMealDB-IDs wurden in die getrennte Rezept-Inbox
  importiert. Diese enthält nun 20 reale Rezepte; der Batch erzeugte beim
  zweiten Abruf keine Duplikate.
- Ein erneuter Seed erhielt alle 30 importierten Lebensmittel und die bereits
  veröffentlichte importierte Mahlzeit.
- Die vollständige Auswahl einschließlich IDs, Katalogschlüsseln, Aliasen und
  verworfenem Kandidaten ist in `docs/import-batches/phase-6f.json` versioniert.

**Bewusste Grenze:** Die zwölf neuen Rezepte bleiben in der Prüfwarteschlange.
Fehlende Portionszahlen, Maße und echte Kataloglücken werden nicht automatisch
geschätzt; keines der Rezepte wird ungeprüft in den Planerkatalog übernommen.

**Status:** abgeschlossen

## Nächster Meilenstein

Phase 3 ist abgeschlossen. Der damals versionierte Arbeitskatalog enthielt 21
Lebensmittel und je zwei Mahlzeiten für alle fünf Rollen; Phase 6D ergänzt drei
weitere Lebensmittel für den ersten realen Importkandidaten. Sämtliche Nährwerte
sind gegen FoodData Central oder ein konkretes europäisches
Herstelleretikett geprüft und ihre Herkunft ist direkt am Katalogeintrag
festgehalten. Die Kohlenhydratwerte verwenden einheitlich die europäische
Definition ohne Ballaststoffe. Nach der erneuten Auswertung ermöglichen die
freigegebenen Portionsfaktoren für jede Referenzstruktur von drei bis sechs
Mahlzeiten mindestens zwei gültige Kombinationen.

Phase 4 ist abgeschlossen. Die Planungslogik erzeugt aus Tageszielen und
Mahlzeitenanzahl reproduzierbar bis zu drei gültige Tagespläne oder transparent
bewertete Annäherungen. Unbrauchbare Kandidaten und inhaltlich doppelte Pläne
werden ausgeschlossen. Der erste API-Endpunkt und eine einfache Oberfläche für
Eingabe, Nährwertübersicht und Mahlzeitendetails sind umgesetzt. Ein Vorschlag
kann ausgewählt und für den nächsten Schritt im Frontend vorgemerkt werden.
Die Bewertung zeigt für jeden Nährwert Ist-Wert, Zielbereich und eine konkrete
Unter- oder Überschreitung. Harte und weiche Abweichungen bleiben unterscheidbar.
Zusätzliche niedrige und hohe Zielprofile sowie der vollständige Ablauf von der
Eingabe bis zur Auswahl sind automatisiert geprüft.

Phase 5 ist abgeschlossen. Der ausgewählte Tagesplan wird für alle sieben
Wochentage dargestellt und aus seinen normalisierten Zutaten entsteht eine
aggregierte Einkaufsliste. Die Summenberechnung ist mit Unit-Tests abgesichert;
der vollständige Ablauf ist als Browser-Test abgedeckt und die Oberfläche wurde
auf Desktop- und Mobilgröße geprüft. Der Nutzerfluss wurde manuell abgenommen.
Der Planer lädt seinen freigegebenen Katalog nun tatsächlich aus PostgreSQL;
ohne erreichbare und befüllte Datenbank werden Systemcheck und Planung als nicht
verfügbar gemeldet.

Damit ist die technische MVP-Roadmap abgeschlossen. Phase 6A ist ebenfalls
abgeschlossen: Die getrennte Import-Inbox, deterministische Normalisierung,
Prüfentscheidungen und Wiederverarbeitung sind umgesetzt und gegen PostgreSQL
geprüft. Phase 6B ist ebenfalls abgeschlossen: Vollständig normalisierte
Kandidaten können kontrolliert veröffentlicht werden, bleiben bei einem Seed
erhalten und werden über den produktiven Katalog an die Planungslogik geliefert.
Phase 6C ist ebenfalls abgeschlossen: Ein einzelnes TheMealDB-Rezept kann per
externer ID live abgerufen werden, ohne dass Quelle oder unsichere Importdaten
die Planungslogik erreichen. Phase 6D ist ebenfalls abgeschlossen: Acht reale
Rezepte wurden ausgewertet, sichere Normalisierungsmetadaten versioniert und ein
fachlich geprüfter Kandidat bis in den produktiven Planerkatalog übernommen.
Phase 6E ist ebenfalls abgeschlossen: Der erste reale FoodData-Central-Datensatz
wurde kontrolliert importiert, freigegeben und bleibt beim Seed erhalten. Als
Phase 6F wurden 29 weitere Lebensmittel und zwölf weitere Rezepte kontrolliert
aufgenommen. Als Nächstes kann die Prüfwarteschlange priorisiert abgearbeitet
werden: zuerst sichere Alias- und Portionsentscheidungen für einfache Rezepte,
danach weitere echte Kataloglücken. Automatische Suche und Open Food Facts
bleiben getrennte Folgeschritte. Eine echte Nutzerprüfung bleibt im Backlog für
einen passenden Zeitpunkt festgehalten.
