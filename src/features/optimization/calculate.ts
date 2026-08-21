import {
  convertQuantity,
  type FoodPackageOffer,
  type NutritionProfile,
  type Quantity,
} from "@/domain";

export type NutritionTotals = {
  caloriesKcal: number;
  proteinGrams: number;
  carbohydratesGrams: number;
  fatGrams: number;
};

export type NutritionCalculation = {
  total: NutritionTotals;
  perServing: NutritionTotals;
};

export type PackageRequirement = {
  packages: number;
  purchasedAmount: number;
  purchasedUnit: FoodPackageOffer["unit"];
  totalPriceCents: number;
  proportionalCostCents: number;
};

export function calculateNutritionForQuantity(
  quantity: Quantity,
  profile: NutritionProfile,
): NutritionTotals | null {
  const converted = convertQuantity(quantity, profile.referenceUnit);
  if (!converted) return null;

  const factor = converted.amount / profile.referenceAmount;
  return {
    caloriesKcal: profile.caloriesKcal * factor,
    proteinGrams: profile.proteinGrams * factor,
    carbohydratesGrams: profile.carbohydratesGrams * factor,
    fatGrams: profile.fatGrams * factor,
  };
}

export function calculateMealNutrition(
  ingredients: Array<{ quantity: Quantity; profile: NutritionProfile }>,
  servings: number,
): NutritionCalculation | null {
  if (!Number.isInteger(servings) || servings <= 0) return null;

  const total = emptyNutrition();
  for (const ingredient of ingredients) {
    const nutrition = calculateNutritionForQuantity(
      ingredient.quantity,
      ingredient.profile,
    );
    if (!nutrition) return null;
    addNutrition(total, nutrition);
  }

  return {
    total,
    perServing: mapNutrition(total, (value) => value / servings),
  };
}

export function calculatePackageRequirement(
  quantity: Quantity,
  offer: FoodPackageOffer,
): PackageRequirement | null {
  const converted = convertQuantity(quantity, offer.unit);
  if (!converted) return null;

  const packages = Math.ceil(converted.amount / offer.amount);
  return {
    packages,
    purchasedAmount: packages * offer.amount,
    purchasedUnit: offer.unit,
    totalPriceCents: packages * offer.priceCents,
    proportionalCostCents:
      (converted.amount / offer.amount) * offer.priceCents,
  };
}

function emptyNutrition(): NutritionTotals {
  return {
    caloriesKcal: 0,
    proteinGrams: 0,
    carbohydratesGrams: 0,
    fatGrams: 0,
  };
}

function addNutrition(target: NutritionTotals, value: NutritionTotals) {
  target.caloriesKcal += value.caloriesKcal;
  target.proteinGrams += value.proteinGrams;
  target.carbohydratesGrams += value.carbohydratesGrams;
  target.fatGrams += value.fatGrams;
}

function mapNutrition(
  nutrition: NutritionTotals,
  transform: (value: number) => number,
): NutritionTotals {
  return {
    caloriesKcal: transform(nutrition.caloriesKcal),
    proteinGrams: transform(nutrition.proteinGrams),
    carbohydratesGrams: transform(nutrition.carbohydratesGrams),
    fatGrams: transform(nutrition.fatGrams),
  };
}
