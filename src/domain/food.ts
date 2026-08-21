export const FOOD_CATEGORIES = [
  "vegetable",
  "fruit",
  "grain",
  "legume",
  "dairy",
  "egg",
  "meat",
  "fish",
  "oil",
  "spice",
  "condiment",
  "other",
] as const;

export type FoodCategory = (typeof FOOD_CATEGORIES)[number];

export const ALLERGENS = [
  "celery",
  "crustaceans",
  "eggs",
  "fish",
  "gluten",
  "lupin",
  "milk",
  "molluscs",
  "mustard",
  "peanuts",
  "sesame",
  "soy",
  "sulphites",
  "tree-nuts",
] as const;

export type Allergen = (typeof ALLERGENS)[number];

export type Food = {
  id: string;
  name: string;
  aliases: string[];
  category: FoodCategory;
  defaultUnit: Unit;
  allergens: Allergen[];
};

export const UNITS = [
  "g",
  "kg",
  "ml",
  "l",
  "piece",
  "tsp",
  "tbsp",
] as const;

export type Unit = (typeof UNITS)[number];

export type Quantity = {
  amount: number;
  unit: Unit;
};

