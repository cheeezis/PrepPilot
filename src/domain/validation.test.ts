import { describe, expect, it } from "vitest";

import type { InventoryItem } from "./inventory";
import type { Recipe } from "./recipe";
import {
  validateInventoryItem,
  validateQuantity,
  validateRecipe,
} from "./validation";

const validRecipe: Recipe = {
  id: "chickpea-curry",
  title: "Chickpea curry",
  description: "A quick pantry-friendly curry.",
  servings: 2,
  prepMinutes: 10,
  cookMinutes: 20,
  ingredients: [
    {
      foodId: "chickpeas",
      quantity: { amount: 400, unit: "g" },
      requirement: "required",
      substitutes: [],
      preparation: "drained",
    },
  ],
  instructions: ["Simmer all ingredients until the sauce thickens."],
  nutritionPerServing: null,
  dietaryTags: ["vegan"],
  source: {
    type: "original",
    provider: null,
    externalId: null,
    sourceUrl: null,
    license: null,
    attribution: null,
  },
};

describe("validateQuantity", () => {
  it("accepts a positive amount", () => {
    expect(validateQuantity({ amount: 250, unit: "g" })).toEqual({
      valid: true,
    });
  });

  it("rejects zero and negative amounts", () => {
    expect(validateQuantity({ amount: 0, unit: "g" }).valid).toBe(false);
    expect(validateQuantity({ amount: -1, unit: "piece" }).valid).toBe(false);
  });
});

describe("validateInventoryItem", () => {
  it("requires a food reference and a positive quantity", () => {
    const item: InventoryItem = {
      id: "inventory-1",
      foodId: "",
      quantity: { amount: 0, unit: "g" },
      storageLocation: "pantry",
      expiresAt: null,
      openedAt: null,
    };

    expect(validateInventoryItem(item)).toEqual({
      valid: false,
      errors: [
        "Inventory item requires a food id.",
        "Quantity must be greater than zero.",
      ],
    });
  });
});

describe("validateRecipe", () => {
  it("accepts a complete recipe", () => {
    expect(validateRecipe(validRecipe)).toEqual({ valid: true });
  });

  it("rejects recipes without servings, ingredients or instructions", () => {
    const result = validateRecipe({
      ...validRecipe,
      servings: 0,
      ingredients: [],
      instructions: [],
    });

    expect(result).toEqual({
      valid: false,
      errors: [
        "Recipe servings must be a positive integer.",
        "Recipe requires at least one ingredient.",
        "Recipe requires at least one instruction.",
      ],
    });
  });
});
