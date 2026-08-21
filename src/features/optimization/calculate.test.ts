import { describe, expect, it } from "vitest";

import type { FoodPackageOffer, NutritionProfile } from "@/domain";
import {
  referenceNutritionProfiles,
  referencePackageOffers,
} from "@/db/seed-data/optimization";
import {
  calculateMealNutrition,
  calculateNutritionForQuantity,
  calculatePackageRequirement,
} from "./calculate";

describe("calculateNutritionForQuantity", () => {
  it("scales a nutrition profile to the requested quantity", () => {
    const rice = nutrition("rice");
    const result = calculateNutritionForQuantity(
      { amount: 160, unit: "g" },
      rice,
    );

    expect(result?.caloriesKcal).toBeCloseTo(584);
    expect(result?.proteinGrams).toBeCloseTo(11.408);
  });

  it("supports compatible unit conversions", () => {
    const rice = nutrition("rice");
    const result = calculateNutritionForQuantity(
      { amount: 1, unit: "kg" },
      rice,
    );

    expect(result?.caloriesKcal).toBeCloseTo(3650);
  });
});

describe("calculateMealNutrition", () => {
  it("independently reproduces the reference recipe per serving", () => {
    const result = calculateMealNutrition(
      [
        ingredient("rice", 160),
        ingredient("chicken-breast", 350),
        ingredient("broccoli", 250),
        ingredient("carrot", 150),
        ingredient("yogurt", 100),
      ],
      2,
    );

    expect(result?.perServing.caloriesKcal).toBeCloseTo(592.1);
    expect(result?.perServing.proteinGrams).toBeCloseTo(51.04, 1);
    expect(result?.perServing.carbohydratesGrams).toBeCloseTo(81.82, 1);
    expect(result?.perServing.fatGrams).toBeCloseTo(6.17, 1);
  });

  it("rejects a non-positive serving count", () => {
    expect(calculateMealNutrition([], 0)).toBeNull();
  });
});

describe("calculatePackageRequirement", () => {
  it("rounds up to purchasable packages", () => {
    const result = calculatePackageRequirement(
      { amount: 1200, unit: "g" },
      offer("rice"),
    );

    expect(result).toEqual({
      packages: 2,
      purchasedAmount: 2000,
      purchasedUnit: "g",
      totalPriceCents: 498,
      proportionalCostCents: 298.8,
    });
  });
});

function nutrition(foodId: string): NutritionProfile {
  const profile = referenceNutritionProfiles.find(
    (item) => item.foodId === foodId,
  );
  if (!profile) throw new Error(`Missing nutrition profile for ${foodId}`);
  return profile;
}

function offer(foodId: string): FoodPackageOffer {
  const result = referencePackageOffers.find((item) => item.foodId === foodId);
  if (!result) throw new Error(`Missing package offer for ${foodId}`);
  return result;
}

function ingredient(foodId: string, amount: number) {
  return {
    quantity: { amount, unit: "g" as const },
    profile: nutrition(foodId),
  };
}
