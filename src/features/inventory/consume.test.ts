import { describe, expect, it } from "vitest";

import { planInventoryConsumption } from "./consume";

describe("planInventoryConsumption", () => {
  it("verbraucht zuerst den frühesten Bestand", () => {
    const result = planInventoryConsumption(
      [{ foodId: "rice", amount: 300, unit: "g" }],
      [
        { id: "later", foodId: "rice", amount: 300, unit: "g", expiresAt: new Date("2026-09-10") },
        { id: "sooner", foodId: "rice", amount: 200, unit: "g", expiresAt: new Date("2026-08-25") },
      ],
    );

    expect(result).toEqual([
      { id: "later", remainingAmount: 200 },
      { id: "sooner", remainingAmount: 0 },
    ]);
  });

  it("rechnet beim Verbrauch zwischen Einheiten um", () => {
    const result = planInventoryConsumption(
      [{ foodId: "rice", amount: 500, unit: "g" }],
      [{ id: "rice", foodId: "rice", amount: 1, unit: "kg", expiresAt: null }],
    );

    expect(result).toEqual([{ id: "rice", remainingAmount: 0.5 }]);
  });

  it("ändert nichts, wenn der Gesamtbestand nicht reicht", () => {
    expect(
      planInventoryConsumption(
        [{ foodId: "rice", amount: 500, unit: "g" }],
        [{ id: "rice", foodId: "rice", amount: 200, unit: "g", expiresAt: null }],
      ),
    ).toBeNull();
  });
});
