import { and, asc, count, eq, gte, lte } from "drizzle-orm";

import { db } from "@/db";
import { foods, inventoryItems } from "@/db/schema";

export async function getFoodOptions() {
  return db
    .select({
      id: foods.id,
      name: foods.name,
      defaultUnit: foods.defaultUnit,
    })
    .from(foods)
    .orderBy(asc(foods.name));
}

export async function getInventory() {
  return db
    .select({
      id: inventoryItems.id,
      foodName: foods.name,
      amount: inventoryItems.amount,
      unit: inventoryItems.unit,
      storageLocation: inventoryItems.storageLocation,
      expiresAt: inventoryItems.expiresAt,
      openedAt: inventoryItems.openedAt,
    })
    .from(inventoryItems)
    .innerJoin(foods, eq(inventoryItems.foodId, foods.id))
    .orderBy(asc(foods.name));
}

export async function getExpiringSoonCount() {
  const now = new Date();
  const inThreeDays = new Date(now.getTime() + 3 * 86_400_000);
  const [result] = await db
    .select({ value: count() })
    .from(inventoryItems)
    .where(
      and(
        gte(inventoryItems.expiresAt, now),
        lte(inventoryItems.expiresAt, inThreeDays),
      ),
    );

  return result?.value ?? 0;
}
