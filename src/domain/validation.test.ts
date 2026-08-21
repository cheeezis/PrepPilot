import { describe, expect, it } from "vitest";

import type { InventoryItem } from "./inventory";
import type { FoodPackageOffer, NutritionProfile } from "./nutrition";
import type { Recipe } from "./recipe";
import {
  validateInventoryItem,
  validateFoodPackageOffer,
  validateNutritionProfile,
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

const validNutritionProfile: NutritionProfile = {
  foodId: "rice",
  referenceAmount: 100,
  referenceUnit: "g",
  caloriesKcal: 365,
  proteinGrams: 7.13,
  carbohydratesGrams: 80,
  fatGrams: 0.66,
  sourceProvider: "USDA FoodData Central",
  sourceExternalId: "169756",
  sourceUrl: "https://fdc.nal.usda.gov/fdc-app.html#/food-details/169756/nutrients",
  sourceRetrievedAt: "2026-08-21",
};

const validPackageOffer: FoodPackageOffer = {
  id: "rice-mvp-package",
  foodId: "rice",
  label: "MVP-Schätzwert 1 kg",
  amount: 1000,
  unit: "g",
  priceCents: 249,
  currency: "EUR",
  sourceType: "estimate",
  sourceProvider: null,
  sourceUrl: null,
  priceObservedAt: "2026-08-21",
};

describe("validateNutritionProfile", () => {
  it("accepts a sourced non-negative nutrition profile", () => {
    expect(validateNutritionProfile(validNutritionProfile)).toEqual({ valid: true });
  });

  it("rejects negative nutrients and missing source metadata", () => {
    const result = validateNutritionProfile({
      ...validNutritionProfile,
      proteinGrams: -1,
      sourceProvider: "",
      sourceUrl: "not-a-url",
    });

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.errors).toContain("Protein cannot be negative.");
      expect(result.errors).toContain("Nutrition profile requires a source provider.");
      expect(result.errors).toContain("Nutrition profile requires a valid source URL.");
    }
  });
});

describe("validateFoodPackageOffer", () => {
  it("accepts a clearly marked MVP estimate", () => {
    expect(validateFoodPackageOffer(validPackageOffer)).toEqual({ valid: true });
  });

  it("rejects invalid amounts and fractional cents", () => {
    const result = validateFoodPackageOffer({
      ...validPackageOffer,
      amount: 0,
      priceCents: 249.5,
    });

    expect(result.valid).toBe(false);
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
