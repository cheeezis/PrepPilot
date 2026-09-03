# Datenmodell

PrepPilot verwendet derzeit eine fachliche PostgreSQL-Tabelle: `recipes`.

Ein Rezept speichert:

- Titel und eine oder mehrere Mahlzeitenkategorien
- Anzahl der Portionen des vollständigen Rezepts
- Kalorien, Protein, Kohlenhydrate und Fett pro Portion
- optionale Werte für Zucker, gesättigte Fettsäuren, Ballaststoffe und Salz
- Zutaten und Zubereitungsschritte als geordnete Listen
- optionale Vorbereitungszeit, Kochzeit und Quellen-URL

Die Zutaten bleiben bewusst quellnaher beziehungsweise nutzereigener Text. Eine
Normalisierung in Lebensmittel, Mengen und Einheiten wird erst eingeführt, wenn
Einkaufslisten oder Zutatenfilter sie tatsächlich benötigen.

Es gibt noch keine Tabellen für Benutzer, gespeicherte Pläne, Favoriten oder
Einkaufslisten.
