import { describe, expect, it } from "vitest";

import { areUnitsCompatible, convertQuantity } from "./measurement";

describe("areUnitsCompatible", () => {
  it("recognizes units from the same dimension", () => {
    expect(areUnitsCompatible("kg", "g")).toBe(true);
    expect(areUnitsCompatible("tbsp", "ml")).toBe(true);
  });

  it("keeps mass, volume and count separate", () => {
    expect(areUnitsCompatible("g", "ml")).toBe(false);
    expect(areUnitsCompatible("piece", "g")).toBe(false);
  });
});

describe("convertQuantity", () => {
  it("converts kilograms to grams", () => {
    expect(convertQuantity({ amount: 1.5, unit: "kg" }, "g")).toEqual({
      amount: 1_500,
      unit: "g",
    });
  });

  it("converts kitchen volume units to millilitres", () => {
    expect(convertQuantity({ amount: 2, unit: "tbsp" }, "ml")).toEqual({
      amount: 30,
      unit: "ml",
    });
  });

  it("returns null for incompatible units", () => {
    expect(convertQuantity({ amount: 100, unit: "g" }, "ml")).toBeNull();
  });
});

