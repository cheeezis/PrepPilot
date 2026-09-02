# Produkt-Backlog

Stand: 2. September 2026

## Nächster Datenabschnitt

### Lebensmittelkonzepte von Nährwertprofilen trennen

Vor einem großen Rezeptimport benötigt PrepPilot stabile kanonische
Lebensmittelidentitäten. Eine Zutat wie „milk“ soll einmal dem Konzept „Milch“
zugeordnet werden. FDC, CoFID oder andere Quellen liefern dazu getrennte
Nährwertprofile und Zustände.

Der technische Grundschnitt ist umgesetzt:

- Konzept und externe Quellenidentität speichern
- konkrete Nährwertprofile direkt einem Konzept zuordnen
- bestehende `foods` über explizite allgemeine Konzeptschlüssel anbinden
- ungeklärte Konzepte einmalig statt pro Rezept prüfen

Eine automatische Wahl eines Standardprofils ist in diesem Abschnitt bewusst
nicht enthalten. Wenn ein Konzept mehrere Profile besitzt, muss die passende
Variante weiterhin explizit bestimmt werden.

### Offenen Rezeptbestand anbinden

Wikibooks Cookbook ist der bevorzugte erste Kandidat. Der erste Lauf bleibt ein
begrenzter Dry Run und prüft Portionen, Zutaten, Anleitung, Lizenzmetadaten und
kanonische Zutatenlinks. Nur vollständige Kandidaten gelangen in die bestehende
Rezept-Inbox.

USDA Team Nutrition kann später einen kleinen hochwertigen Zusatzbestand
liefern. Historische Public-Domain-Archive bleiben wegen fehlender Portionen und
uneinheitlicher Qualität zunächst in Quarantäne.

### Nutzerinitiierter URL-Import

Ein späterer Nutzer kann ein einzelnes Rezept aus einer URL in seine private
Sammlung übernehmen. Schema.org/JSON-LD und `recipe-scrapers` sind dafür
technisch geeignet. Diese Funktion ist von einem Bulk-Katalogimport zu trennen
und muss Quellrechte, Attribution und Bilder gesondert behandeln.

### Importbetrieb

Noch zu entscheiden ist, ob wiederholte Importläufe als Kommando, Hintergrundjob
oder Admin-Aktion gestartet werden. Die vorhandene lokale Importprüfung zeigt
den Zustand und erlaubt die einmalige Konzeptzuordnung; sie startet selbst keine
Importläufe. Temporäre quellspezifische HTTP-Endpunkte sollen nicht erneut
entstehen.

## Produktvalidierung

Der technische MVP soll mit geeigneten Personen aus der Zielgruppe geprüft
werden. Erfolgskriterien und Ablauf werden festgelegt, sobald eine passende
Testgruppe verfügbar ist.

## Spätere Produktfunktionen

- unterschiedliche Tagespläne innerhalb einer Woche
- Mahlzeiten austauschen und Wiederholungen steuern
- Ernährungsformen, Ausschlüsse und Favoriten
- eigene Mahlzeiten und gespeicherte Pläne
- Benutzerkonten und geräteübergreifende Nutzung
- Zucker, Ballaststoffe, Salz und Allergene
- Preise, Packungsgrößen, Budgets und Vorräte
- Produkt- und Mahlzeitenbilder
- KI-gestützte, aber niemals selbstständig freigebende Review-Vorschläge
