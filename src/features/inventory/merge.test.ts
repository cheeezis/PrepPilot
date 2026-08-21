import { describe, expect, it } from "vitest";

import { combineInventoryAmounts } from "./merge";

describe("combineInventoryAmounts", () => {
  it("addiert Mengen mit derselben Einheit", () => {
    expect(
      combineInventoryAmounts(
        { amount: 300, unit: "g" },
        { amount: 200, unit: "g" },
      ),
    ).toEqual({ amount: 500, unit: "g" });
  });

  it("rechnet kompatible Einheiten vor dem Addieren um", () => {
    expect(
      combineInventoryAmounts(
        { amount: 500, unit: "g" },
        { amount: 1, unit: "kg" },
      ),
    ).toEqual({ amount: 1500, unit: "g" });
  });

  it("lehnt inkompatible Einheiten ab", () => {
    expect(
      combineInventoryAmounts(
        { amount: 500, unit: "g" },
        { amount: 1, unit: "l" },
      ),
    ).toBeNull();
  });
});
