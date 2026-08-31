# Datenmodell

Stand: 31. August 2026

## Ziel und Systemgrenze

Das MVP verwendet einen kleinen, kuratierten Lebensmittel- und
Mahlzeitenkatalog. Der Planer arbeitet ausschließlich mit vollständigen,
freigegebenen Katalogdaten. Jede Zutatenmenge liegt bereits in Gramm oder
Millilitern vor; externe Rezepttexte, Haushaltsmaße und unsichere Importe sind
nicht Teil des operativen MVP-Modells.

Eine Mahlzeit kann ein gekochtes Gericht, eine Brotmahlzeit, ein Shake oder ein
einfacher Snack sein. Ihre Nährwerte werden immer aus den hinterlegten
Lebensmitteln und Mengen berechnet und nicht zusätzlich gespeichert.

## Tabellen

- `foods`: Lebensmittel mit stabiler Katalogkennung, optionaler Marke,
  Basiseinheit `g` oder `ml`, den vier MVP-Nährwerten pro 100 Basiseinheiten
  sowie Quelle und Quellenreferenz
- `meals`: Mahlzeiten mit stabiler Katalogkennung, Name, Zubereitungszeit und
  kurzer Anleitung
- `meal_ingredients`: Lebensmittel und bereits normalisierte Menge in der
  Grundportion einer Mahlzeit
- `meal_portion_factors`: ausdrücklich erlaubte Skalierungsfaktoren einer
  Mahlzeit
- `meal_roles`: mögliche Rollen einer Mahlzeit im Tagesplan

Die Rollen sind erste Mahlzeit, leichte Mittagsmahlzeit, Protein-Snack,
Hauptgericht und später Snack. Generische und markenspezifische Lebensmittel
nutzen dieselbe Struktur; eine fehlende Marke kennzeichnet ein generisches
Lebensmittel.

Jede Mahlzeit besitzt genau eine kuratierte Grundportion. Für sie wird eine
Teilmenge der Faktoren `0.5`, `1.0`, `1.5` und `2.0` ausdrücklich freigegeben.
Dadurch können beispielsweise Hauptgerichte bei `1.5` und kleine späte Snacks
bei `1.0` begrenzt werden. Der Planer darf nur diese Faktoren verwenden;
einzelne Zutaten werden nicht unabhängig voneinander optimiert.

## Mengen und Näherungen

Gespeicherte Zutatenmengen verwenden ausschließlich die Basiseinheit des
zugeordneten Lebensmittels. Für das MVP werden diese Mengen direkt mit der
Mahlzeit kuratiert. Rechenlogik für Haushaltsmaße, Dichten oder Stückgewichte
wird dafür nicht benötigt.

Für den automatischen Rezeptimport gelten folgende bewusst
vereinfachte Normalisierungsregeln:

- `1 tsp` beziehungsweise ein Teelöffel entspricht `5 g` bei festen und `5 ml`
  bei flüssigen Lebensmitteln.
- `1 tbsp` beziehungsweise ein Esslöffel entspricht `15 g` bei festen und
  `15 ml` bei flüssigen Lebensmitteln.
- metrische Masse- und Volumeneinheiten werden direkt umgerechnet.
- Nichtmetrische Stückangaben wie Ei, Zwiebel, Knoblauchzehe oder Brotscheibe
  benötigen genau einen Standardwert für das betreffende Lebensmittel.

Solche Standardwerte sollen bevorzugt aus einer geeigneten Portion von
FoodData Central übernommen werden. Sie sind nachvollziehbare
PrepPilot-Näherungen und keine Zusage auf das tatsächliche Gewicht eines
konkreten Lebensmittels. Phase 6A speichert diese Werte in
`food_measure_defaults`; sie gehören weiterhin nicht zum abgeschlossenen
MVP-Schema.

## Datenquellen und Qualität

FoodData Central ist die bevorzugte Recherche- und Übernahmequelle für
generische Lebensmittel und, soweit vorhanden, für übliche Stückgewichte. Open
Food Facts kann ergänzend für konkrete Markenprodukte dienen. Bei wenigen
markenspezifischen MVP-Einträgen dürfen stattdessen die Angaben des
Herstelleretiketts übernommen werden.

FoodData-Central-Daten stehen unter CC0 und dürfen mit Quellenangabe in den
versionierten Katalog übernommen werden. Im MVP werden ergänzend nur einzelne,
öffentlich angegebene Hersteller-Nährwerte kuratiert und mit der konkreten
Produktseite referenziert. Open Food Facts wird aktuell nicht als Datenquelle
kopiert, weil der kleine Katalog damit keinen zusätzlichen Nutzen gewinnt und
eine spätere Übernahme die ODbL-Bedingungen gesondert berücksichtigen müsste.

Der Katalog wird versioniert im Repository gepflegt und reproduzierbar in die
Datenbank geladen. Jeder freigegebene Eintrag besitzt die vier benötigten
Nährwerte, eine Basiseinheit und eine nachvollziehbare Quelle. Die Planung
benötigt keine Live-Verbindung zu einer externen Datenquelle.

Stabile Katalogkennungen verbinden die versionierten Definitionen mit den
Datenbankeinträgen und ermöglichen eine reproduzierbare technische Sortierung.
Sie sind keine nutzerseitigen Bezeichnungen.

Nährwerte und Standardmengen sind Durchschnittswerte beziehungsweise bewusste
Näherungen. Das MVP optimiert auf konsistente und plausible Berechnungen, nicht
auf medizinische oder laborgenaue Aussagen.

`carbs_per_100` verwendet die Bedeutung der europäischen
Nährwertkennzeichnung: erfasst werden vom Menschen verwertbare Kohlenhydrate;
Ballaststoffe sind nicht enthalten. Das entspricht den Angaben, die Nutzer in
Deutschland auf Verpackungen sehen. FoodData Central weist Kohlenhydrate bei
vielen generischen Lebensmitteln dagegen „by difference“ einschließlich
Ballaststoffen aus. In diesen Fällen wird der veröffentlichte Ballaststoffwert
einmalig beim Kuratieren abgezogen und die Umrechnung in der Quellenreferenz
festgehalten. Zur Laufzeit findet keine solche Umrechnung statt.

Bei produktabhängigen generischen Katalogeinträgen darf ein konkretes
europäisches Herstelleretikett als repräsentativer Näherungswert dienen. Der
Katalog schreibt dadurch keine Marke für die spätere Einkaufsliste vor; die
Produktbezeichnung steht ausschließlich in der Quellenreferenz.

## Import-Inbox nach dem MVP

Der in Phase 6A ergänzte Importbereich bewahrt externe Rezeptdaten zunächst
unverändert auf und normalisiert Zutaten und Mengen getrennt vom produktiven
Katalog. Nur vollständig auf interne Lebensmittel sowie Gramm oder Milliliter
abgebildete Rezepte dürfen später als Mahlzeiten freigegeben werden.

Die Import-Inbox ergänzt folgende Tabellen:

- `recipe_imports` für Quelle, externe Kennung, Rohdaten, Inhalts-Hash,
  Portionen und Rezeptstatus
- `recipe_import_ingredients` für originale Zutatenzeilen, Parsing-Ergebnisse,
  Zuordnungen, normalisierte Mengen und Prüfgründe
- `food_aliases` für bestätigte wiederverwendbare Bezeichnungen
- `food_measure_defaults` für nachvollziehbare lebensmittelspezifische
  Stück- und Portionsstandards
- `import_review_decisions` für die Historie manueller Korrekturen

Ein Import ist `received`, `needs_review`, `ready_for_catalog_review` oder
`rejected`. `ready_for_catalog_review` ist ausdrücklich noch keine Freigabe für
den Planer oder den produktiven Mahlzeitenkatalog.

Beim manuellen quellenneutralen Eingang enthält `raw_payload` das interne
Eingangsformat. Beim TheMealDB-Adapter enthält es stattdessen das unveränderte
empfangene Rezeptobjekt; die daraus abgeleiteten Zutatenzeilen werden wie zuvor
separat in `recipe_import_ingredients` gespeichert. Der Inhalts-Hash wird über
diese Rohdaten gebildet. Dadurch erzeugt ein unveränderter erneuter Abruf kein
Duplikat, während eine tatsächlich geänderte Quellenversion als neuer,
nachvollziehbarer Import erhalten bleiben kann.

Phase 6B ergänzt `meals` um die Herkunft `curated_seed` oder `recipe_import`.
Eine importierte Mahlzeit verweist eindeutig auf genau einen vollständig
normalisierten Rezeptimport. Seed-Mahlzeiten besitzen keinen solchen Verweis.
Die bestehenden Tabellen für Zutaten, Rollen und Portionsfaktoren werden für
beide Herkunftsarten gemeinsam verwendet.

Fehlt eine Zutatenzuordnung oder eine benötigte Stückumrechnung, wird kein
generischer Gewichts-Fallback verwendet. Das gesamte Rezept wird zur manuellen
Prüfung zurückgestellt. Dort kann ein wiederverwendbarer Lebensmittelstandard
ergänzt, eine rezeptbezogene Menge festgelegt oder das Rezept verworfen werden.
Eine spätere LLM-Unterstützung darf Vorschläge für diese Prüfung liefern, aber
keine unvollständigen Rezepte am Katalog vorbei freigeben.

Phase 6D ergänzt die versionierte Katalogdefinition um optionale `aliases` und
`measure_defaults` je Lebensmittel. Diese erzeugen keine neuen automatischen
Entscheidungen: Jeder Eintrag ist eine bereits geprüfte, wiederverwendbare Regel
mit eindeutiger Lebensmittelzuordnung. Maßstandards tragen Menge, Quellenname
und Quellenreferenz. Katalogverwaltete und später manuell ergänzte Datensätze
bleiben beim Seed unterscheidbar, sodass der Seed nur seine eigenen veralteten
Regeln entfernt.

## Bewusste Grenzen des MVP

Nicht zum MVP-Datenmodell gehören:

- Rohimporte und eine Prüfwarteschlange für externe Rezepte
- Lebensmittel-Aliase für externe Zutatenbezeichnungen
- lebensmittelspezifische Sammlungen konkurrierender Portionsgrößen
- Dichteberechnungen und allgemeines Parsing freier Mengenangaben
- Preise, Packungsgrößen und Vorräte
- Bilder, Allergene, Zucker, Ballaststoffe und Salz
