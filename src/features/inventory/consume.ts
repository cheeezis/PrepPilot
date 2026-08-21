import { convertQuantity, type Unit } from "@/domain";

export type ConsumptionIngredient = {
  foodId: string;
  amount: number;
  unit: Unit;
};

export type ConsumableInventoryItem = {
  id: string;
  foodId: string;
  amount: number;
  unit: Unit;
  expiresAt: Date | null;
};

export type InventoryConsumption = {
  id: string;
  remainingAmount: number;
};

export function planInventoryConsumption(
  ingredients: ConsumptionIngredient[],
  inventory: ConsumableInventoryItem[],
): InventoryConsumption[] | null {
  const workingInventory = inventory.map((item) => ({ ...item }));
  const changedIds = new Set<string>();

  for (const ingredient of ingredients) {
    const candidates = workingInventory
      .filter((item) => item.foodId === ingredient.foodId && item.amount > 0)
      .sort(
        (first, second) =>
          (first.expiresAt?.getTime() ?? Number.POSITIVE_INFINITY) -
          (second.expiresAt?.getTime() ?? Number.POSITIVE_INFINITY),
      );
    let remaining = ingredient.amount;

    for (const item of candidates) {
      if (remaining <= 0.000_001) break;
      const available = convertQuantity(
        { amount: item.amount, unit: item.unit },
        ingredient.unit,
      );
      if (!available) continue;

      const usedIngredientAmount = Math.min(remaining, available.amount);
      const usedInItemUnit = convertQuantity(
        { amount: usedIngredientAmount, unit: ingredient.unit },
        item.unit,
      );
      if (!usedInItemUnit) continue;

      item.amount = Math.max(item.amount - usedInItemUnit.amount, 0);
      changedIds.add(item.id);
      remaining -= usedIngredientAmount;
    }

    if (remaining > 0.000_001) return null;
  }

  return workingInventory
    .filter((item) => changedIds.has(item.id))
    .map((item) => ({ id: item.id, remainingAmount: item.amount }));
}
