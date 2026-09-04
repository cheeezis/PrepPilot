# Datenmodell

PrepPilot verwendet derzeit eine fachliche PostgreSQL-Tabelle: `recipes`.

Ein Rezept speichert:

- Titel und eine oder mehrere Mahlzeitenkategorien
- Anzahl der Portionen des vollständigen Rezepts
- Kalorien, Protein, Kohlenhydrate und Fett pro Portion
- optionale Werte für Zucker, gesättigte Fettsäuren, Ballaststoffe und Salz
- Zutaten mit numerischer Menge, Einheit und Bezeichnung
- Zubereitungsschritte als geordnete Liste
- optionale Vorbereitungszeit, Kochzeit und Quellen-URL

Die Zutatenmengen gelten für das vollständige Rezept. Die strukturierte
Erfassung ermöglicht der späteren Wochenplanung, benötigte Kochmengen und eine
zusammengeführte Einkaufsliste zu berechnen.

Es gibt noch keine Tabellen für Benutzer, gespeicherte Pläne, Favoriten oder
Einkaufslisten.
