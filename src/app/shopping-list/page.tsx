import Link from "next/link";

import { getShoppingList } from "@/features/shopping-list/queries";
import { deleteShoppingItem, toggleShoppingItem } from "./actions";

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

export default async function ShoppingListPage() {
  const items = await getShoppingList();
  const openCount = items.filter((item) => !item.checked).length;

  return (
    <main className="min-h-screen bg-[#f3f1e8] px-5 py-8 text-[#1f2921] sm:px-8">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="inline-block rounded-xl px-3 py-2 text-sm font-medium text-[#52604e] hover:bg-white/60">
          ← Zur Übersicht
        </Link>
        <div className="mb-7 mt-7">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#6d805f]">Einkaufsliste</p>
          <h1 className="mt-2 text-4xl font-bold tracking-[-0.04em] sm:text-5xl">Was fehlt noch?</h1>
          <p className="mt-3 text-[#697064]">{openCount} offene Einträge · Fehlende Rezeptzutaten werden automatisch zusammengeführt.</p>
        </div>

        <section className="rounded-[1.75rem] bg-[#fffdf7] p-6 shadow-[0_18px_60px_rgba(44,58,39,0.08)] sm:p-8">
          {items.length === 0 ? (
            <div className="grid min-h-64 place-items-center text-center">
              <div><div className="mx-auto mb-4 grid size-14 place-items-center rounded-full bg-[#e4ecdd] text-2xl">✓</div><h2 className="font-semibold">Die Einkaufsliste ist leer.</h2><p className="mt-2 text-sm text-[#727a6f]">Öffne ein Rezept und übernimm die fehlenden Zutaten.</p></div>
            </div>
          ) : (
            <div className="divide-y divide-[#ecece4]">
              {items.map((item) => {
                const toggleAction = toggleShoppingItem.bind(null, item.id, !item.checked);
                const deleteAction = deleteShoppingItem.bind(null, item.id);
                return (
                  <article key={item.id} className="flex items-center gap-4 py-4 first:pt-0 last:pb-0">
                    <form action={toggleAction}>
                      <button type="submit" aria-label={`${item.foodName} ${item.checked ? "als offen markieren" : "abhaken"}`} className={`grid size-9 place-items-center rounded-xl border text-sm font-bold ${item.checked ? "border-[#76906e] bg-[#dcebd5] text-[#315c3b]" : "border-[#cbd2c4] bg-white text-transparent"}`}>✓</button>
                    </form>
                    <div className={`min-w-0 flex-1 ${item.checked ? "opacity-50" : ""}`}>
                      <h2 className={`font-semibold ${item.checked ? "line-through" : ""}`}>{item.foodName}</h2>
                      <p className="mt-1 text-sm text-[#737a70]">{Number(item.amount.toFixed(2))} {unitLabels[item.unit]}</p>
                    </div>
                    <form action={deleteAction}>
                      <button type="submit" className="rounded-xl px-3 py-2 text-sm font-medium text-[#8a554f] hover:bg-[#f6e9e6]">Löschen</button>
                    </form>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
