import Link from "next/link";

import {
  getExpiringSoonCount,
  getFoodOptions,
  getInventory,
} from "@/features/inventory/queries";
import { getRankedRecipes } from "@/features/recipes/queries";
import { InventoryForm } from "./inventory-form";
import { InventoryItemActions } from "./inventory-item-actions";

const storageLabels = {
  pantry: "Vorratsschrank",
  fridge: "Kühlschrank",
  freezer: "Gefrierschrank",
} as const;

const unitLabels = {
  g: "g",
  kg: "kg",
  ml: "ml",
  l: "l",
  piece: "Stück",
  tsp: "TL",
  tbsp: "EL",
} as const;

export const dynamic = "force-dynamic";

export default async function Home() {
  const [foodOptions, inventory, expiringSoon, rankedRecipes] = await Promise.all([
    getFoodOptions(),
    getInventory(),
    getExpiringSoonCount(),
    getRankedRecipes(),
  ]);

  return (
    <main className="min-h-screen bg-[#f3f1e8] text-[#1f2921]">
      <header className="border-b border-black/5 bg-[#fffdf7]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5 sm:px-8">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-2xl bg-[#d9e7cf] text-xl">
              ◒
            </div>
            <div>
              <p className="text-lg font-bold tracking-tight">PrepPilot</p>
              <p className="text-xs text-[#6e776a]">Kochen, was schon da ist.</p>
            </div>
          </div>
          <nav className="flex items-center gap-2 text-sm font-medium text-[#52604e]">
            <Link href="/" className="rounded-xl px-3 py-2 hover:bg-[#eef2e8]">
              Übersicht
            </Link>
            <Link
              href="/shopping-list"
              className="rounded-xl px-3 py-2 hover:bg-[#eef2e8]"
            >
              Einkaufsliste
            </Link>
          </nav>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8">
        <div className="mb-8 max-w-2xl">
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-[#6d805f]">
            Dein Vorrat
          </p>
          <h1 className="text-4xl font-bold tracking-[-0.04em] sm:text-5xl">
            Was ist gerade zu Hause?
          </h1>
          <p className="mt-4 max-w-xl text-base leading-7 text-[#697064]">
            Erfasse deine Lebensmittel. PrepPilot nutzt sie später, um passende
            Rezepte zu finden und angebrochene Vorräte rechtzeitig aufzubrauchen.
          </p>
        </div>

        <section className="mb-8 grid gap-4 sm:grid-cols-3">
          <Metric label="Lebensmittel" value={inventory.length.toString()} />
          <Metric label="Bald verbrauchen" value={expiringSoon.toString()} />
          <Metric
            label="Ohne Verbrauchsdatum"
            value={inventory
              .filter((item) => item.expiresAt === null)
              .length.toString()}
          />
        </section>

        <section className="mb-10">
          <div className="mb-5 flex items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#78846f]">
                Deine besten Matches
              </p>
              <h2 className="mt-1 text-2xl font-bold tracking-tight">
                Was kannst du daraus kochen?
              </h2>
            </div>
            <span className="hidden text-sm text-[#788076] sm:block">
              Score aus Vorrat und Haltbarkeit
            </span>
          </div>
          {rankedRecipes.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-[#cbd2c4] bg-[#fffdf7]/70 p-6 text-sm text-[#727a6f]">
              Noch keine Rezepte vorhanden. Führe einmal den Seed-Befehl aus.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {rankedRecipes.map((recipe, index) => (
                <Link
                  key={recipe.id}
                  href={`/recipes/${recipe.id}`}
                  className="group rounded-[1.5rem] bg-[#fffdf7] p-5 shadow-[0_12px_40px_rgba(44,58,39,0.06)] transition hover:-translate-y-0.5 hover:shadow-[0_16px_46px_rgba(44,58,39,0.1)]"
                >
                  <div className="flex items-start justify-between gap-4">
                    <span className="text-xs font-semibold text-[#7c8676]">
                      #{index + 1} · {recipe.prepMinutes + recipe.cookMinutes} Min.
                    </span>
                    <span className="grid size-12 place-items-center rounded-full bg-[#dfead8] text-sm font-bold text-[#315c3b]">
                      {recipe.score}%
                    </span>
                  </div>
                  <h3 className="mt-3 text-lg font-bold tracking-tight group-hover:text-[#315c3b]">
                    {recipe.title}
                  </h3>
                  <p className="mt-2 line-clamp-2 text-sm leading-6 text-[#70776d]">
                    {recipe.description}
                  </p>
                  <p className="mt-4 text-sm font-medium text-[#53664e]">
                    {recipe.canCook
                      ? "Alle Pflichtzutaten vorhanden"
                      : `${recipe.missingRequiredCount} Pflichtzutat${recipe.missingRequiredCount === 1 ? "" : "en"} fehlt`}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </section>

        <div className="grid items-start gap-7 lg:grid-cols-[22rem_1fr]">
          <section className="rounded-[1.75rem] bg-[#fffdf7] p-6 shadow-[0_18px_60px_rgba(44,58,39,0.08)]">
            <div className="mb-6">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#78846f]">
                Neuer Eintrag
              </p>
              <h2 className="mt-1 text-2xl font-bold tracking-tight">
                Vorrat hinzufügen
              </h2>
            </div>
            <InventoryForm foods={foodOptions} />
          </section>

          <section className="rounded-[1.75rem] bg-[#fffdf7] p-6 shadow-[0_18px_60px_rgba(44,58,39,0.08)] sm:p-8">
            <div className="mb-6 flex items-end justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#78846f]">
                  Übersicht
                </p>
                <h2 className="mt-1 text-2xl font-bold tracking-tight">
                  Vorhandene Lebensmittel
                </h2>
              </div>
              <span className="text-sm text-[#788076]">
                {inventory.length} Einträge
              </span>
            </div>

            {inventory.length === 0 ? (
              <div className="grid min-h-72 place-items-center rounded-3xl border border-dashed border-[#cbd2c4] bg-[#f7f7f1] p-8 text-center">
                <div>
                  <div className="mx-auto mb-4 grid size-14 place-items-center rounded-full bg-[#e4ecdd] text-2xl">
                    ⌁
                  </div>
                  <h3 className="font-semibold">Noch ist dein Vorrat leer.</h3>
                  <p className="mt-2 max-w-sm text-sm leading-6 text-[#727a6f]">
                    Füge links dein erstes Lebensmittel hinzu. Die Liste wird
                    anschließend automatisch aktualisiert.
                  </p>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-[#ecece4]">
                {inventory.map((item) => {
                  return (
                    <article
                      key={item.id}
                      className="py-4 first:pt-0 last:pb-0"
                    >
                      <div className="grid grid-cols-[auto_1fr_auto] items-center gap-4">
                        <div className="grid size-11 shrink-0 place-items-center rounded-2xl bg-[#e6eddc] font-semibold text-[#486044]">
                          {item.foodName.slice(0, 1).toUpperCase()}
                        </div>
                        <div className="min-w-0 flex-1">
                          <h3 className="font-semibold">{item.foodName}</h3>
                          <p className="mt-1 text-sm text-[#737a70]">
                            {item.amount} {unitLabels[item.unit]} ·{" "}
                            {storageLabels[item.storageLocation]}
                            {item.expiresAt
                              ? ` · bis ${formatDate(item.expiresAt)}`
                              : ""}
                          </p>
                        </div>
                        <InventoryItemActions
                          id={item.id}
                          foodName={item.foodName}
                          amount={item.amount}
                          unit={item.unit}
                          storageLocation={item.storageLocation}
                          expiresAt={toDateInputValue(item.expiresAt)}
                          openedAt={toDateInputValue(item.openedAt)}
                        />
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-black/5 bg-[#fffdf7]/80 px-5 py-4">
      <p className="text-2xl font-bold tracking-tight">{value}</p>
      <p className="mt-1 text-sm text-[#70776d]">{label}</p>
    </div>
  );
}

function formatDate(value: Date) {
  return new Intl.DateTimeFormat("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(value);
}

function toDateInputValue(value: Date | null) {
  return value?.toISOString().slice(0, 10) ?? null;
}
