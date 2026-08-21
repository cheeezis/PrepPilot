# PrepPilot

PrepPilot ist ein smarter Meal-Prep-Planer, der vorhandene Vorräte mit passenden Rezepten abgleicht und dabei Zeit, Budget, Ernährungsziele und Lebensmittelverwertung berücksichtigt.

> Sag PrepPilot, was du zu Hause hast – und finde heraus, was du daraus am besten kochen kannst.

## Produktkern

PrepPilot verbindet drei Bereiche:

1. eine strukturierte Rezeptdatenbank,
2. den persönlichen Vorrat des Nutzers,
3. eine erklärbare Matching-Engine.

Die App zeigt nicht nur mögliche Rezepte, sondern bewertet und erklärt, warum ein Rezept gerade gut passt: vorhandene Zutaten, bald ablaufende Lebensmittel, fehlende Einkäufe, Zeitaufwand und Ernährungsziele.

## MVP-Nutzerfluss

1. Nutzer erfasst seine Vorräte.
2. PrepPilot zeigt passende Rezepte als Ranking.
3. Jede Empfehlung nennt vorhandene und fehlende Zutaten.
4. Nutzer wählt ein Rezept aus.
5. Verwendete Mengen werden vom Vorrat abgezogen.
6. Fehlende Zutaten können auf die Einkaufsliste gesetzt werden.

## MVP-Abgrenzung

Die erste Version umfasst bewusst noch keine automatische Bilderkennung, Supermarktpreise, Kalenderintegration oder vollständig optimierte Wochenplanung. Diese Funktionen bauen später auf demselben Datenmodell auf.

Den aktuellen Entwicklungsplan findest du in [TODO.md](./TODO.md).

## Lokale Entwicklung

Voraussetzung ist Node.js 24 LTS. Anschließend:

```powershell
npm install
Copy-Item .env.example .env
npm run db:migrate
npm run db:seed
npm run dev
```

Die lokale SQLite-Datenbank wird standardmäßig unter `data/preppilot.db`
angelegt und nicht in Git eingecheckt. Neue Schemaänderungen werden mit
`npm run db:generate` als nachvollziehbare SQL-Migration erzeugt.

## Rezept-Matching

Der erste Match-Score bleibt bewusst einfach und erklärbar:

- 80 Prozent: Abdeckung der benötigten Mengen aller Pflichtzutaten
- 10 Prozent: Abdeckung optionaler Zutaten
- 10 Prozent: Bonus für vorhandene Zutaten, die innerhalb von drei Tagen ablaufen

Bei gleichem Score werden Rezepte mit weniger fehlenden Pflichtzutaten und
anschließend mit kürzerer Gesamtzeit zuerst angezeigt.
