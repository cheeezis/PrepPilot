import type { Quantity, Unit } from "./food";

export type UnitDimension = "mass" | "volume" | "count";

type UnitDefinition = {
  dimension: UnitDimension;
  toBaseUnitFactor: number;
};

const UNIT_DEFINITIONS: Record<Unit, UnitDefinition> = {
  g: { dimension: "mass", toBaseUnitFactor: 1 },
  kg: { dimension: "mass", toBaseUnitFactor: 1_000 },
  ml: { dimension: "volume", toBaseUnitFactor: 1 },
  l: { dimension: "volume", toBaseUnitFactor: 1_000 },
  tsp: { dimension: "volume", toBaseUnitFactor: 5 },
  tbsp: { dimension: "volume", toBaseUnitFactor: 15 },
  piece: { dimension: "count", toBaseUnitFactor: 1 },
};

export function areUnitsCompatible(first: Unit, second: Unit): boolean {
  return (
    UNIT_DEFINITIONS[first].dimension === UNIT_DEFINITIONS[second].dimension
  );
}

export function convertQuantity(
  quantity: Quantity,
  targetUnit: Unit,
): Quantity | null {
  if (!areUnitsCompatible(quantity.unit, targetUnit)) return null;

  const amountInBaseUnit =
    quantity.amount * UNIT_DEFINITIONS[quantity.unit].toBaseUnitFactor;
  const convertedAmount =
    amountInBaseUnit / UNIT_DEFINITIONS[targetUnit].toBaseUnitFactor;

  return { amount: convertedAmount, unit: targetUnit };
}

