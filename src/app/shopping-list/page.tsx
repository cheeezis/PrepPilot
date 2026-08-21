import Link from "next/link";

import { getShoppingList } from "@/features/shopping-list/queries";
import { ShoppingListItem } from "./shopping-list-item";

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
                return (
                  <ShoppingListItem
                    key={item.id}
                    id={item.id}
                    foodName={item.foodName}
                    amount={item.amount}
                    unit={item.unit}
                    checked={item.checked}
                  />
                );
              })}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
