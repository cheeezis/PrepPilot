"use server";

import { and, eq, isNull } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { z } from "zod";

import { db } from "@/db";
import { inventoryItems, shoppingListItems } from "@/db/schema";
import { combineInventoryAmounts } from "@/features/inventory/merge";
import {
  purchasedItemFormSchema,
  type PurchasedItemFormState,
} from "@/features/shopping-list/schema";

export async function toggleShoppingItem(id: string, checked: boolean) {
  if (!z.uuid().safeParse(id).success) return;
  await db
    .update(shoppingListItems)
    .set({ checked, updatedAt: new Date() })
    .where(eq(shoppingListItems.id, id));
  revalidatePath("/shopping-list");
}

export async function deleteShoppingItem(id: string) {
  if (!z.uuid().safeParse(id).success) return;
  await db.delete(shoppingListItems).where(eq(shoppingListItems.id, id));
  revalidatePath("/shopping-list");
}

export async function movePurchasedItemToInventory(
  id: string,
  _previousState: PurchasedItemFormState,
  formData: FormData,
): Promise<PurchasedItemFormState> {
  void _previousState;
  const parsedId = z.uuid().safeParse(id);
  if (!parsedId.success) return errorState("Der Eintrag ist ungültig.");

  const parsed = purchasedItemFormSchema.safeParse({
    storageLocation: formData.get("storageLocation"),
    expiresAt: formData.get("expiresAt"),
  });
  if (!parsed.success) {
    return errorState("Bitte überprüfe Lagerort und Verbrauchsdatum.");
  }

  const result = await db.transaction(async (tx) => {
    const [shoppingItem] = await tx
      .select({
        id: shoppingListItems.id,
        foodId: shoppingListItems.foodId,
        amount: shoppingListItems.amount,
        unit: shoppingListItems.unit,
        checked: shoppingListItems.checked,
      })
      .from(shoppingListItems)
      .where(eq(shoppingListItems.id, parsedId.data))
      .limit(1);

    if (!shoppingItem) return "missing" as const;
    if (!shoppingItem.checked) return "unchecked" as const;

    const [existingItem] = await tx
      .select({
        id: inventoryItems.id,
        amount: inventoryItems.amount,
        unit: inventoryItems.unit,
      })
      .from(inventoryItems)
      .where(
        and(
          eq(inventoryItems.foodId, shoppingItem.foodId),
          eq(inventoryItems.storageLocation, parsed.data.storageLocation),
          parsed.data.expiresAt
            ? eq(inventoryItems.expiresAt, parsed.data.expiresAt)
            : isNull(inventoryItems.expiresAt),
          isNull(inventoryItems.openedAt),
        ),
      )
      .limit(1);

    if (existingItem) {
      const combined = combineInventoryAmounts(
        { amount: existingItem.amount, unit: existingItem.unit },
        { amount: shoppingItem.amount, unit: shoppingItem.unit },
      );
      if (!combined) return "incompatible" as const;
      await tx
        .update(inventoryItems)
        .set({ amount: combined.amount, updatedAt: new Date() })
        .where(eq(inventoryItems.id, existingItem.id));
    } else {
      await tx.insert(inventoryItems).values({
        id: crypto.randomUUID(),
        foodId: shoppingItem.foodId,
        amount: shoppingItem.amount,
        unit: shoppingItem.unit,
        storageLocation: parsed.data.storageLocation,
        expiresAt: parsed.data.expiresAt,
        openedAt: null,
      });
    }

    await tx
      .delete(shoppingListItems)
      .where(eq(shoppingListItems.id, shoppingItem.id));
    return "success" as const;
  });

  if (result === "missing") return errorState("Der Eintrag existiert nicht mehr.");
  if (result === "unchecked") {
    return errorState("Hake den Einkauf zuerst als erledigt ab.");
  }
  if (result === "incompatible") {
    return errorState("Die Einkaufsmenge passt nicht zum vorhandenen Bestand.");
  }

  revalidatePath("/");
  revalidatePath("/shopping-list");
  return { status: "success", message: "Einkauf wurde in den Vorrat übernommen." };
}

function errorState(message: string): PurchasedItemFormState {
  return { status: "error", message };
}
