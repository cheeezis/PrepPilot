import { convertQuantity, type Quantity } from "@/domain";

export function combineInventoryAmounts(
  existing: Quantity,
  addition: Quantity,
): Quantity | null {
  const converted = convertQuantity(addition, existing.unit);

  if (!converted) return null;

  return {
    amount: existing.amount + converted.amount,
    unit: existing.unit,
  };
}
