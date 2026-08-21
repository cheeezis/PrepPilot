"use client";

import { useActionState } from "react";

import { addMissingIngredients, cookRecipe } from "./actions";
import { initialRecipeActionState } from "./recipe-action-state";

export function RecipeActions({
  recipeId,
  canCook,
  missingCount,
}: {
  recipeId: string;
  canCook: boolean;
  missingCount: number;
}) {
  const [shoppingState, shoppingAction, shoppingPending] = useActionState(
    addMissingIngredients.bind(null, recipeId),
    initialRecipeActionState,
  );
  const [cookState, cookAction, cookPending] = useActionState(
    cookRecipe.bind(null, recipeId),
    initialRecipeActionState,
  );
  const state = cookState.status !== "idle" ? cookState : shoppingState;

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-3 sm:flex-row">
        <form action={cookAction} className="flex-1">
          <button
            type="submit"
            disabled={!canCook || cookPending}
            className="w-full rounded-2xl bg-[#315c3b] px-5 py-3.5 font-semibold text-white transition hover:bg-[#274c30] disabled:cursor-not-allowed disabled:opacity-45"
          >
            {cookPending ? "Bestand wird aktualisiert …" : "Als gekocht markieren"}
          </button>
        </form>
        <form action={shoppingAction} className="flex-1">
          <button
            type="submit"
            disabled={missingCount === 0 || shoppingPending}
            className="w-full rounded-2xl border border-[#9aaa91] bg-white px-5 py-3.5 font-semibold text-[#315c3b] transition hover:bg-[#f1f5ed] disabled:cursor-not-allowed disabled:opacity-45"
          >
            {shoppingPending
              ? "Wird ergänzt …"
              : `${missingCount} fehlende auf Einkaufsliste`}
          </button>
        </form>
      </div>
      {state.message && (
        <p
          aria-live="polite"
          className={`text-sm ${state.status === "error" ? "text-red-700" : "text-[#315c3b]"}`}
        >
          {state.message}
        </p>
      )}
    </div>
  );
}
