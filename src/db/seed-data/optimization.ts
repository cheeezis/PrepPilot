import type { FoodPackageOffer, NutritionProfile } from "@/domain";

const retrievedAt = "2026-08-21";

export const referenceNutritionProfiles: NutritionProfile[] = [
  {
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
    sourceRetrievedAt: retrievedAt,
  },
  {
    foodId: "chicken-breast",
    referenceAmount: 100,
    referenceUnit: "g",
    caloriesKcal: 112.2,
    proteinGrams: 22.5,
    carbohydratesGrams: 0,
    fatGrams: 1.93,
    sourceProvider: "USDA FoodData Central",
    sourceExternalId: "2646170",
    sourceUrl: "https://fdc.nal.usda.gov/fdc-app.html#/food-details/2646170/nutrients",
    sourceRetrievedAt: retrievedAt,
  },
  {
    foodId: "broccoli",
    referenceAmount: 100,
    referenceUnit: "g",
    caloriesKcal: 34,
    proteinGrams: 2.82,
    carbohydratesGrams: 6.64,
    fatGrams: 0.37,
    sourceProvider: "USDA FoodData Central",
    sourceExternalId: "170379",
    sourceUrl: "https://fdc.nal.usda.gov/fdc-app.html#/food-details/170379/nutrients",
    sourceRetrievedAt: retrievedAt,
  },
  {
    foodId: "carrot",
    referenceAmount: 100,
    referenceUnit: "g",
    caloriesKcal: 41,
    proteinGrams: 0.93,
    carbohydratesGrams: 9.58,
    fatGrams: 0.24,
    sourceProvider: "USDA FoodData Central",
    sourceExternalId: "170393",
    sourceUrl: "https://fdc.nal.usda.gov/fdc-app.html#/food-details/170393/nutrients",
    sourceRetrievedAt: retrievedAt,
  },
  {
    foodId: "yogurt",
    referenceAmount: 100,
    referenceUnit: "g",
    caloriesKcal: 61,
    proteinGrams: 3.47,
    carbohydratesGrams: 4.66,
    fatGrams: 3.25,
    sourceProvider: "USDA FoodData Central",
    sourceExternalId: "171284",
    sourceUrl: "https://fdc.nal.usda.gov/fdc-app.html#/food-details/171284/nutrients",
    sourceRetrievedAt: retrievedAt,
  },
];

export const referencePackageOffers: FoodPackageOffer[] = [
  estimate("rice", "Reis, 1-kg-Packung", 1000, 249),
  estimate("chicken-breast", "Hähnchenbrust, 600-g-Packung", 600, 699),
  estimate("broccoli", "Brokkoli, 500-g-Packung", 500, 249),
  estimate("carrot", "Karotten, 1-kg-Packung", 1000, 149),
  estimate("yogurt", "Naturjoghurt, 500-g-Becher", 500, 129),
];

function estimate(
  foodId: string,
  label: string,
  amount: number,
  priceCents: number,
): FoodPackageOffer {
  return {
    id: `${foodId}-mvp-estimate`,
    foodId,
    label,
    amount,
    unit: "g",
    priceCents,
    currency: "EUR",
    sourceType: "estimate",
    sourceProvider: "PrepPilot MVP-Schätzwert",
    sourceUrl: null,
    priceObservedAt: retrievedAt,
  };
}
