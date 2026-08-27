# Datenmodell

Stand: 27. August 2026

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

Für einen späteren automatischen Rezeptimport gelten folgende bewusst
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
konkreten Lebensmittels. Eine spätere Importfunktion kann dafür ein kleines
Modell wie `food_measure_defaults` ergänzen; es gehört nicht zum MVP-Schema.

## Datenquellen und Qualität

FoodData Central ist die bevorzugte Recherche- und Übernahmequelle für
generische Lebensmittel und, soweit vorhanden, für übliche Stückgewichte. Open
Food Facts kann ergänzend für konkrete Markenprodukte dienen. Bei wenigen
markenspezifischen MVP-Einträgen dürfen stattdessen die Angaben des
Herstelleretiketts übernommen werden.

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

## Grenze zum späteren Rezeptimport

Ein späterer Importbereich bewahrt externe Rezeptdaten zunächst unverändert
auf und normalisiert Zutaten und Mengen getrennt vom produktiven Katalog. Nur
vollständig auf interne Lebensmittel sowie Gramm oder Milliliter abgebildete
Rezepte dürfen als Mahlzeiten freigegeben werden.

Fehlt eine Zutatenzuordnung oder eine benötigte Stückumrechnung, wird kein
generischer Gewichts-Fallback verwendet. Das gesamte Rezept wird zur manuellen
Prüfung zurückgestellt. Dort kann ein wiederverwendbarer Lebensmittelstandard
ergänzt, eine rezeptbezogene Menge festgelegt oder das Rezept verworfen werden.
Eine spätere LLM-Unterstützung darf Vorschläge für diese Prüfung liefern, aber
keine unvollständigen Rezepte am Katalog vorbei freigeben.

## Bewusste Grenzen des MVP

Nicht zum MVP-Datenmodell gehören:

- Rohimporte und eine Prüfwarteschlange für externe Rezepte
- Lebensmittel-Aliase für externe Zutatenbezeichnungen
- lebensmittelspezifische Sammlungen konkurrierender Portionsgrößen
- Dichteberechnungen und allgemeines Parsing freier Mengenangaben
- Preise, Packungsgrößen und Vorräte
- Bilder, Allergene, Zucker, Ballaststoffe und Salz
