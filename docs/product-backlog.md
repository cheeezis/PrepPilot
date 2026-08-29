# Produkt-Backlog

Stand: 29. August 2026

Dieses Backlog sammelt interessante Produktideen, die noch nicht Teil der
beschlossenen MVP-Roadmap sind. Ein Eintrag ist keine Umsetzungszusage. Bevor
eine Idee in die Roadmap wandert, klären wir kurz das Nutzerproblem, den Nutzen,
den kleinsten sinnvollen Umfang und den passenden Zeitpunkt.

## Produktvalidierung

### MVP mit geeigneten Zielnutzern testen

Sobald tatsächlich geeignete Personen aus der Zielgruppe verfügbar sind, soll
geprüft werden, ob sie ohne Erklärung einen Wochenplan samt Einkaufsliste
erstellen und das Ergebnis als praktisch einschätzen. Zahl, Ablauf und
Erfolgskriterien werden erst dann passend zur erreichbaren Testgruppe
festgelegt. Für den technischen MVP werden keine beliebigen Personen als
stellvertretende Testnutzer verpflichtet.

## Katalog und Datenimport

### Externe Rezepte automatisch importieren

Eine spätere Importpipeline könnte Zutatenbezeichnungen und Mengen externer
Rezepte automatisch auf den internen Lebensmittelkatalog sowie Gramm oder
Milliliter abbilden. Direkte metrische Angaben werden übernommen. Für Teelöffel
und Esslöffel gelten einfache globale PrepPilot-Regeln; nichtmetrische
Stückangaben verwenden bevorzugt einen aus FoodData Central übernommenen oder
intern festgelegten Lebensmittelstandard.

Nur vollständig normalisierte Rezepte dürfen in den produktiven Katalog
gelangen. Der Planer bleibt dadurch unabhängig von Rezeptquellen,
Haushaltsmaßen und Importfehlern.

### Unvollständige Importe manuell prüfen

Kann eine relevante Zutat oder Menge nicht sicher normalisiert werden, wird das
gesamte Rezept in einer Prüfwarteschlange zurückgestellt. Die Prüfung soll den
konkreten Grund zeigen, beispielsweise eine unbekannte Zutat, eine nicht
erkannte Einheit oder ein fehlendes Stückgewicht.

In der Prüfung kann eine Zutatenzuordnung korrigiert, ein wiederverwendbarer
Lebensmittelstandard ergänzt, eine rezeptbezogene Menge festgelegt oder das
Rezept verworfen werden. Nach einer wiederverwendbaren Ergänzung sollen alle
betroffenen Importe erneut verarbeitet werden können. Einen generischen
Gewichts-Fallback für relevante Zutaten gibt es nicht.

### Rezepte durch Nutzer importieren

Nutzer könnten eigene Rezeptquellen angeben und daraus Mahlzeiten samt
angenäherten Nährwerten anlegen. Diese Funktion baut auf der getrennten
Importpipeline und Prüfwarteschlange auf und gehört nicht zum MVP.

### KI-unterstützte Katalogpflege

Ein LLM könnte in der Prüfwarteschlange Zutatenzuordnungen, passende
FoodData-Central-Portionen oder plausible Standardgewichte vorschlagen und die
Vorschläge begründen. Deterministische Validierung und die Freigabegrenze zum
produktiven Katalog bleiben davon getrennt; ein LLM-Vorschlag darf ein
unvollständiges Rezept nicht selbstständig freigeben.

## Flexiblere Planung

- unterschiedliche Tagespläne innerhalb einer Woche
- steuerbare Wiederholung und Abwechslung
- einzelne Mahlzeiten austauschen
- flexible Mahlzeiten- oder Snack-Slots
- Nutzungshistorie bei neuen Vorschlägen berücksichtigen
- Einkaufsliste für gemischte Wochenpläne aktualisieren

## Personalisierung

- Ernährungsformen, Ausschlüsse und Favoriten
- eigene Mahlzeiten, Vorlagen und gespeicherte Pläne
- Benutzerkonten und geräteübergreifende Nutzung

## Weitere Produktdaten

- Zucker, Ballaststoffe und Salz
- Allergendaten und darauf aufbauende Filter
- Preise, Packungsgrößen und Budget
- Produkt- und Mahlzeitenbilder

## Einkauf und Vorräte

- vorhandene Vorräte berücksichtigen
- Einkaufsmengen auf Packungsgrößen aufrunden
- Einkaufskosten schätzen und Budgets berücksichtigen
