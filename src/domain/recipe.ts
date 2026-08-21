import type { Quantity } from "./food";

export const DIETARY_TAGS = [
  "vegan",
  "vegetarian",
  "pescatarian",
  "gluten-free",
  "high-protein",
] as const;

export type DietaryTag = (typeof DIETARY_TAGS)[number];

export type IngredientRequirement = "required" | "optional";

export type IngredientSubstitute = {
  foodId: string;
  quantity: Quantity;
};

export type RecipeIngredient = {
  foodId: string;
  quantity: Quantity;
  requirement: IngredientRequirement;
  substitutes: IngredientSubstitute[];
  preparation: string | null;
};

export type Nutrition = {
  caloriesKcal: number;
  proteinGrams: number;
  carbohydratesGrams: number;
  fatGrams: number;
};

export type RecipeSource = {
  type: "original" | "api" | "user";
  provider: string | null;
  externalId: string | null;
  sourceUrl: string | null;
  license: string | null;
  attribution: string | null;
};

export type Recipe = {
  id: string;
  title: string;
  description: string;
  servings: number;
  prepMinutes: number;
  cookMinutes: number;
  ingredients: RecipeIngredient[];
  instructions: string[];
  nutritionPerServing: Nutrition | null;
  dietaryTags: DietaryTag[];
  source: RecipeSource;
};

