"use server";

import { and, eq, isNull } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { z } from "zod";

import { db } from "@/db";
import { foods, inventoryItems } from "@/db/schema";
import { areUnitsCompatible } from "@/domain";
import { combineInventoryAmounts } from "@/features/inventory/merge";
import {
  inventoryFormSchema,
  type InventoryFormState,
  inventoryUpdateFormSchema,
} from "@/features/inventory/schema";

export async function createInventoryItem(
  _previousState: InventoryFormState,
  formData: FormData,
): Promise<InventoryFormState> {
  const parsed = inventoryFormSchema.safeParse({
    foodId: formData.get("foodId"),
    ...getSharedFormValues(formData),
  });

  if (!parsed.success) return validationError(parsed.error);

  const [food] = await db
    .select({ defaultUnit: foods.defaultUnit })
    .from(foods)
    .where(eq(foods.id, parsed.data.foodId))
    .limit(1);

  if (!food) return formError("Das ausgewählte Lebensmittel wurde nicht gefunden.");
  if (!areUnitsCompatible(food.defaultUnit, parsed.data.unit)) {
    return formError("Die Einheit passt nicht zum ausgewählten Lebensmittel.");
  }

  const [existingItem] = await db
    .select({
      id: inventoryItems.id,
      amount: inventoryItems.amount,
      unit: inventoryItems.unit,
    })
    .from(inventoryItems)
    .where(
      and(
        eq(inventoryItems.foodId, parsed.data.foodId),
        eq(inventoryItems.storageLocation, parsed.data.storageLocation),
        parsed.data.expiresAt
          ? eq(inventoryItems.expiresAt, parsed.data.expiresAt)
          : isNull(inventoryItems.expiresAt),
        parsed.data.openedAt
          ? eq(inventoryItems.openedAt, parsed.data.openedAt)
          : isNull(inventoryItems.openedAt),
      ),
    )
    .limit(1);

  if (existingItem) {
    const combined = combineInventoryAmounts(
      { amount: existingItem.amount, unit: existingItem.unit },
      { amount: parsed.data.amount, unit: parsed.data.unit },
    );

    if (!combined) {
      return formError(
        "Die vorhandenen Mengen lassen sich nicht zusammenführen.",
      );
    }

    await db
      .update(inventoryItems)
      .set({
        amount: combined.amount,
        updatedAt: new Date(),
      })
      .where(eq(inventoryItems.id, existingItem.id));

    revalidatePath("/");
    return {
      status: "success",
      message: "Menge wurde zum vorhandenen Vorrat addiert.",
    };
  }

  await db.insert(inventoryItems).values({
    id: crypto.randomUUID(),
    foodId: parsed.data.foodId,
    amount: parsed.data.amount,
    unit: parsed.data.unit,
    storageLocation: parsed.data.storageLocation,
    expiresAt: parsed.data.expiresAt,
    openedAt: parsed.data.openedAt,
  });

  revalidatePath("/");
  return { status: "success", message: "Vorrat wurde hinzugefügt." };
}

export async function updateInventoryItem(
  id: string,
  _previousState: InventoryFormState,
  formData: FormData,
): Promise<InventoryFormState> {
  const parsedId = z.uuid().safeParse(id);
  if (!parsedId.success) return formError("Der Vorratseintrag ist ungültig.");

  const parsed = inventoryUpdateFormSchema.safeParse(getSharedFormValues(formData));
  if (!parsed.success) return validationError(parsed.error);

  const [item] = await db
    .select({ defaultUnit: foods.defaultUnit })
    .from(inventoryItems)
    .innerJoin(foods, eq(inventoryItems.foodId, foods.id))
    .where(eq(inventoryItems.id, parsedId.data))
    .limit(1);

  if (!item) return formError("Der Vorratseintrag wurde nicht gefunden.");
  if (!areUnitsCompatible(item.defaultUnit, parsed.data.unit)) {
    return formError("Die Einheit passt nicht zum Lebensmittel.");
  }

  await db
    .update(inventoryItems)
    .set({
      amount: parsed.data.amount,
      unit: parsed.data.unit,
      storageLocation: parsed.data.storageLocation,
      expiresAt: parsed.data.expiresAt,
      openedAt: parsed.data.openedAt,
      updatedAt: new Date(),
    })
    .where(eq(inventoryItems.id, parsedId.data));

  revalidatePath("/");
  return { status: "success", message: "Änderungen wurden gespeichert." };
}

export async function deleteInventoryItem(id: string): Promise<void> {
  const parsedId = z.uuid().safeParse(id);
  if (!parsedId.success) return;

  await db.delete(inventoryItems).where(eq(inventoryItems.id, parsedId.data));
  revalidatePath("/");
}

function getSharedFormValues(formData: FormData) {
  return {
    amount: formData.get("amount"),
    unit: formData.get("unit"),
    storageLocation: formData.get("storageLocation"),
    expiresAt: formData.get("expiresAt"),
    openedAt: formData.get("openedAt"),
  };
}

function validationError(error: z.ZodError): InventoryFormState {
  return {
    status: "error",
    message: "Bitte überprüfe deine Eingaben.",
    errors: z.flattenError(error).fieldErrors,
  };
}

function formError(message: string): InventoryFormState {
  return { status: "error", message };
}
