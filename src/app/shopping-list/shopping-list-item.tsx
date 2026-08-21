"use client";

import { useActionState } from "react";

import type { Unit } from "@/domain";
import { initialPurchasedItemFormState } from "@/features/shopping-list/schema";
import {
  deleteShoppingItem,
  movePurchasedItemToInventory,
  toggleShoppingItem,
} from "./actions";

const unitLabels: Record<Unit, string> = {
  g: "g",
  kg: "kg",
  ml: "ml",
  l: "l",
  piece: "Stück",
  tsp: "TL",
  tbsp: "EL",
};

export function ShoppingListItem({
  id,
  foodName,
  amount,
  unit,
  checked,
}: {
  id: string;
  foodName: string;
  amount: number;
  unit: Unit;
  checked: boolean;
}) {
  const toggleAction = toggleShoppingItem.bind(null, id, !checked);
  const deleteAction = deleteShoppingItem.bind(null, id);
  const moveAction = movePurchasedItemToInventory.bind(null, id);
  const [state, formAction, pending] = useActionState(
    moveAction,
    initialPurchasedItemFormState,
  );

  return (
    <article className="py-4 first:pt-0 last:pb-0">
      <div className="flex items-center gap-4">
        <form action={toggleAction}>
          <button
            type="submit"
            aria-label={`${foodName} ${checked ? "als offen markieren" : "abhaken"}`}
            className={`grid size-9 place-items-center rounded-xl border text-sm font-bold ${
              checked
                ? "border-[#76906e] bg-[#dcebd5] text-[#315c3b]"
                : "border-[#cbd2c4] bg-white text-transparent"
            }`}
          >
            ✓
          </button>
        </form>
        <div className={`min-w-0 flex-1 ${checked ? "opacity-50" : ""}`}>
          <h2 className={`font-semibold ${checked ? "line-through" : ""}`}>
            {foodName}
          </h2>
          <p className="mt-1 text-sm text-[#737a70]">
            {Number(amount.toFixed(2))} {unitLabels[unit]}
          </p>
        </div>
        <form action={deleteAction}>
          <button
            type="submit"
            className="rounded-xl px-3 py-2 text-sm font-medium text-[#8a554f] hover:bg-[#f6e9e6]"
          >
            Löschen
          </button>
        </form>
      </div>

      {checked && (
        <form
          action={formAction}
          className="mt-4 rounded-2xl bg-[#f6f6ef] p-4 sm:ml-[3.25rem]"
        >
          <p className="mb-3 text-sm font-semibold text-[#465742]">
            Einkauf in den Vorrat einräumen
          </p>
          <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
            <label className="text-xs font-semibold text-[#5d6659]">
              Lagerort
              <select
                name="storageLocation"
                defaultValue=""
                required
                className="field-control mt-1"
              >
                <option value="" disabled>
                  Bitte wählen
                </option>
                <option value="pantry">Vorratsschrank</option>
                <option value="fridge">Kühlschrank</option>
                <option value="freezer">Gefrierschrank</option>
              </select>
            </label>
            <label className="text-xs font-semibold text-[#5d6659]">
              Verbrauchsdatum
              <input
                name="expiresAt"
                type="date"
                className="field-control mt-1"
              />
            </label>
            <button
              type="submit"
              disabled={pending}
              className="rounded-xl bg-[#315c3b] px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              {pending ? "Räumt ein …" : "In Vorrat"}
            </button>
          </div>
          {state.message && (
            <p
              aria-live="polite"
              className={`mt-3 text-sm ${
                state.status === "error" ? "text-red-700" : "text-[#315c3b]"
              }`}
            >
              {state.message}
            </p>
          )}
        </form>
      )}
    </article>
  );
}
