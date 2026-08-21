"use server";

import { eq } from "drizzle-orm";
import { revalidatePath } from "next/cache";
import { z } from "zod";

import { db } from "@/db";
import { shoppingListItems } from "@/db/schema";

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
