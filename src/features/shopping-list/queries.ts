import { asc, eq } from "drizzle-orm";

import { db } from "@/db";
import { foods, shoppingListItems } from "@/db/schema";

export function getShoppingList() {
  return db
    .select({
      id: shoppingListItems.id,
      foodName: foods.name,
      amount: shoppingListItems.amount,
      unit: shoppingListItems.unit,
      checked: shoppingListItems.checked,
    })
    .from(shoppingListItems)
    .innerJoin(foods, eq(shoppingListItems.foodId, foods.id))
    .orderBy(asc(shoppingListItems.checked), asc(foods.name));
}
