import { convertQuantity, type DietaryTag, type Unit } from "@/domain";

export type MatchableIngredient = {
  foodId: string;
  foodName: string;
  amount: number;
  unit: Unit;
  requirement: "required" | "optional";
  preparation: string | null;
};

export type MatchableRecipe = {
  id: string;
  title: string;
  description: string;
  servings: number;
  prepMinutes: number;
  cookMinutes: number;
  instructions: string[];
  caloriesKcal: number | null;
  proteinGrams: number | null;
  carbohydratesGrams: number | null;
  fatGrams: number | null;
  dietaryTags: DietaryTag[];
  ingredients: MatchableIngredient[];
};

export type MatchableInventoryItem = {
  foodId: string;
  amount: number;
  unit: Unit;
  expiresAt: Date | null;
};

export type IngredientMatch = MatchableIngredient & {
  availableAmount: number;
  missingAmount: number;
  coverage: number;
  status: "available" | "partial" | "missing";
  expiresSoon: boolean;
};

export type RecipeMatch = MatchableRecipe & {
  score: number;
  canCook: boolean;
  requiredAvailable: number;
  requiredTotal: number;
  missingRequiredCount: number;
  ingredientMatches: IngredientMatch[];
  reasons: string[];
};

const THREE_DAYS = 3 * 86_400_000;

export function matchRecipe(
  recipe: MatchableRecipe,
  inventory: MatchableInventoryItem[],
  now = new Date(),
): RecipeMatch {
  const ingredientMatches = recipe.ingredients.map((ingredient) => {
    const matchingInventory = inventory.filter(
      (item) => item.foodId === ingredient.foodId,
    );
    const availableAmount = matchingInventory.reduce((total, item) => {
      const converted = convertQuantity(
        { amount: item.amount, unit: item.unit },
        ingredient.unit,
      );
      return total + (converted?.amount ?? 0);
    }, 0);
    const coverage = Math.min(availableAmount / ingredient.amount, 1);
    const missingAmount = Math.max(ingredient.amount - availableAmount, 0);
    const expiresSoon = matchingInventory.some(
      (item) =>
        item.expiresAt !== null &&
        item.expiresAt.getTime() >= now.getTime() &&
        item.expiresAt.getTime() <= now.getTime() + THREE_DAYS,
    );

    return {
      ...ingredient,
      availableAmount,
      missingAmount,
      coverage,
      status:
        coverage >= 1 ? "available" : coverage > 0 ? "partial" : "missing",
      expiresSoon,
    } satisfies IngredientMatch;
  });

  const required = ingredientMatches.filter(
    (ingredient) => ingredient.requirement === "required",
  );
  const optional = ingredientMatches.filter(
    (ingredient) => ingredient.requirement === "optional",
  );
  const requiredCoverage = average(required.map((item) => item.coverage));
  const optionalCoverage = optional.length
    ? average(optional.map((item) => item.coverage))
    : 1;
  const expiringCoverage = required.length
    ? required.filter((item) => item.coverage > 0 && item.expiresSoon).length /
      required.length
    : 0;
  const score = Math.round(
    Math.min(
      requiredCoverage * 80 + optionalCoverage * 10 + expiringCoverage * 10,
      100,
    ),
  );
  const requiredAvailable = required.filter(
    (ingredient) => ingredient.status === "available",
  ).length;
  const missingRequiredCount = required.length - requiredAvailable;
  const reasons = buildReasons(
    requiredAvailable,
    required.length,
    optional.filter((item) => item.status === "available").length,
    ingredientMatches.filter((item) => item.expiresSoon && item.coverage > 0)
      .length,
  );

  return {
    ...recipe,
    score,
    canCook: missingRequiredCount === 0,
    requiredAvailable,
    requiredTotal: required.length,
    missingRequiredCount,
    ingredientMatches,
    reasons,
  };
}

export function rankRecipes(
  recipes: MatchableRecipe[],
  inventory: MatchableInventoryItem[],
  now = new Date(),
) {
  return recipes
    .map((recipe) => matchRecipe(recipe, inventory, now))
    .sort(
      (first, second) =>
        second.score - first.score ||
        first.missingRequiredCount - second.missingRequiredCount ||
        first.prepMinutes + first.cookMinutes -
          (second.prepMinutes + second.cookMinutes),
    );
}

function average(values: number[]) {
  if (values.length === 0) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function buildReasons(
  available: number,
  total: number,
  optional: number,
  expiring: number,
) {
  const reasons = [`${available} von ${total} Pflichtzutaten vollständig vorhanden`];
  if (expiring > 0) {
    reasons.push(
      `${expiring} bald ablaufende Zutat${expiring === 1 ? "" : "en"} wird verwertet`,
    );
  }
  if (optional > 0) {
    reasons.push(
      `${optional} optionale Zutat${optional === 1 ? "" : "en"} vorhanden`,
    );
  }
  return reasons;
}
