import type { Unit } from "./food";

export type NutritionProfile = {
  foodId: string;
  referenceAmount: number;
  referenceUnit: Unit;
  caloriesKcal: number;
  proteinGrams: number;
  carbohydratesGrams: number;
  fatGrams: number;
  sourceProvider: string;
  sourceExternalId: string;
  sourceUrl: string;
  sourceRetrievedAt: string;
};

export type PriceSourceType = "estimate" | "retailer" | "user";

export type FoodPackageOffer = {
  id: string;
  foodId: string;
  label: string;
  amount: number;
  unit: Unit;
  priceCents: number;
  currency: "EUR";
  sourceType: PriceSourceType;
  sourceProvider: string | null;
  sourceUrl: string | null;
  priceObservedAt: string;
};
