"use server";

import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { z } from "zod";

import { db } from "@/db";
import {
  inventoryItems,
  shoppingListItems,
} from "@/db/schema";
import { combineInventoryAmounts } from "@/features/inventory/merge";
import { planInventoryConsumption } from "@/features/inventory/consume";
import { getRecipeMatch } from "@/features/recipes/queries";
import type { RecipeActionState } from "./recipe-action-state";

const recipeIdSchema = z.string().regex(/^[a-z0-9-]+$/);

export async function addMissingIngredients(
  recipeId: string,
  _previousState: RecipeActionState,
): Promise<RecipeActionState> {
  void _previousState;
  if (!recipeIdSchema.safeParse(recipeId).success) {
    return errorState("Das Rezept ist ungültig.");
  }

  const match = await getRecipeMatch(recipeId);
  if (!match) return errorState("Das Rezept wurde nicht gefunden.");

  const missing = match.ingredientMatches.filter(
    (ingredient) =>
      ingredient.requirement === "required" && ingredient.missingAmount > 0,
  );
  if (missing.length === 0) {
    return { status: "success", message: "Du hast bereits alle Pflichtzutaten." };
  }

  await db.transaction(async (tx) => {
    for (const ingredient of missing) {
      const [existing] = await tx
        .select({
          id: shoppingListItems.id,
          amount: shoppingListItems.amount,
          unit: shoppingListItems.unit,
        })
        .from(shoppingListItems)
        .where(eq(shoppingListItems.foodId, ingredient.foodId))
        .limit(1);

      if (existing) {
        const combined = combineInventoryAmounts(
          { amount: existing.amount, unit: existing.unit },
          { amount: ingredient.missingAmount, unit: ingredient.unit },
        );
        if (!combined) throw new Error("Inkompatible Einkaufsmengen");
        await tx
          .update(shoppingListItems)
          .set({ amount: combined.amount, checked: false, updatedAt: new Date() })
          .where(eq(shoppingListItems.id, existing.id));
      } else {
        await tx.insert(shoppingListItems).values({
          id: crypto.randomUUID(),
          foodId: ingredient.foodId,
          amount: ingredient.missingAmount,
          unit: ingredient.unit,
        });
      }
    }
  });

  revalidatePath("/shopping-list");
  revalidatePath(`/recipes/${recipeId}`);
  return {
    status: "success",
    message: `${missing.length} fehlende Zutat${missing.length === 1 ? "" : "en"} wurde${missing.length === 1 ? "" : "n"} ergänzt.`,
  };
}

export async function cookRecipe(
  recipeId: string,
  _previousState: RecipeActionState,
): Promise<RecipeActionState> {
  void _previousState;
  if (!recipeIdSchema.safeParse(recipeId).success) {
    return errorState("Das Rezept ist ungültig.");
  }

  const match = await getRecipeMatch(recipeId);
  if (!match) return errorState("Das Rezept wurde nicht gefunden.");
  if (!match.canCook) {
    return errorState("Zum Kochen fehlen noch Pflichtzutaten.");
  }

  try {
    await db.transaction(async (tx) => {
      const ingredients = match.ingredientMatches.filter(
        (ingredient) =>
          ingredient.requirement === "required" ||
          ingredient.status === "available",
      );
      const items = await tx.select().from(inventoryItems);
      const consumption = planInventoryConsumption(ingredients, items);
      if (!consumption) throw new Error("Nicht genügend Bestand");

      for (const item of consumption) {
        if (item.remainingAmount <= 0.000_001) {
          await tx.delete(inventoryItems).where(eq(inventoryItems.id, item.id));
        } else {
          await tx
            .update(inventoryItems)
            .set({ amount: item.remainingAmount, updatedAt: new Date() })
            .where(eq(inventoryItems.id, item.id));
        }
      }
    });
  } catch {
    return errorState(
      "Der Bestand hat sich geändert. Bitte lade die Seite neu und prüfe die Mengen.",
    );
  }

  revalidatePath("/");
  revalidatePath(`/recipes/${recipeId}`);
  return {
    status: "success",
    message: "Guten Appetit! Die verwendeten Mengen wurden abgezogen.",
  };
}

function errorState(message: string): RecipeActionState {
  return { status: "error", message };
}
