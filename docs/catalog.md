# Katalog

Stand: 24. August 2026

Dieses Dokument sammelt die ersten fachlichen Referenzeinträge für den
Lebensmittel- und Mahlzeitenkatalog. Es ist noch kein Datenbankschema und kein
Seed-Datensatz.

## Prüfstatus

- **Vorläufig:** Die Werte wurden online plausibilisiert, aber noch nicht mit
  der konkret verwendeten Verpackung abgeglichen.
- **Verifiziert:** Die Werte wurden mit einer primären Quelle, insbesondere der
  Produktverpackung, abgeglichen.

Nur verifizierte Einträge sollen später ohne Hinweis produktiv verwendet
werden. Vorläufige Einträge dürfen bereits als fachliche Testdaten dienen.

## Lebensmittel

### Gutes Land H-Milch 0,3 %

Status: vorläufig

Bezugsgröße: `100 ml`

| Nährwert | Wert |
| --- | ---: |
| Energie | 38 kcal |
| Protein | 3,6 g |
| Kohlenhydrate | 5,1 g |
| Fett | 0,3 g |

Produktkennung aus der Quelle: EAN `4316268668934`

Quellen:

- [FDDB](https://fddb.info/db/de/lebensmittel/gutes_land_milch_0_3prozent_0_3/index.html)
- [FatSecret](https://www.fatsecret.de/Kalorien-Ern%C3%A4hrung/gutes-land/03-h-milch/100ml)

Beide Quellen nennen dieselben vier Hauptwerte. Es liegt noch keine offizielle
Herstellerquelle vor; ein Verpackungsabgleich bleibt erforderlich.

### MyProtein Impact Whey Protein, Chocolate Brownie

Status: vorläufig

Bezugsgröße: `100 g`

| Nährwert | Wert |
| --- | ---: |
| Energie | 390 kcal |
| Protein | 71 g |
| Kohlenhydrate | 7,9 g |
| Fett | 7,5 g |

Quelle:

- [MyProtein Österreich](https://www.myprotein.at/p/sporternahrung/myprotein-impact-whey-protein-chocolate-brownie/12207742/)

Die Quelle ist eine offizielle Produktseite für die konkrete Geschmacksrichtung.
Da Rezepturen je Markt oder Charge abweichen können, bleibt der Eintrag bis zum
Verpackungsabgleich vorläufig.

## Feste Mahlzeiten

### Proteinshake

Rolle: einfacher Protein-Snack

Portionsregel: feste, nicht automatisch skalierbare Portion

| Lebensmittel | Menge |
| --- | ---: |
| Gutes Land H-Milch 0,3 % | 500 ml |
| MyProtein Impact Whey Protein, Chocolate Brownie | 45 g |

Exaktes rechnerisches Ergebnis:

| Nährwert | Wert |
| --- | ---: |
| Energie | 365,50 kcal |
| Protein | 49,95 g |
| Kohlenhydrate | 29,055 g |
| Fett | 4,875 g |

Anzeige nach Rundung:

| Nährwert | Wert |
| --- | ---: |
| Energie | 366 kcal |
| Protein | 50 g |
| Kohlenhydrate | 29 g |
| Fett | 5 g |

Bei einer täglichen Einplanung über sieben Tage benötigt die Einkaufsliste
`3,5 l` Milch und `315 g` Whey.
