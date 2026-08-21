import { sql } from "drizzle-orm";
import {
  check,
  index,
  integer,
  real,
  sqliteTable,
  text,
  uniqueIndex,
} from "drizzle-orm/sqlite-core";

import type {
  Allergen,
  DietaryTag,
  FoodCategory,
  PriceSourceType,
  StorageLocation,
  Unit,
} from "@/domain";

const timestamps = {
  createdAt: integer("created_at", { mode: "timestamp_ms" })
    .notNull()
    .default(sql`(unixepoch() * 1000)`),
  updatedAt: integer("updated_at", { mode: "timestamp_ms" })
    .notNull()
    .default(sql`(unixepoch() * 1000)`),
};

export const foods = sqliteTable(
  "foods",
  {
    id: text("id").primaryKey(),
    name: text("name").notNull(),
    normalizedName: text("normalized_name").notNull(),
    aliases: text("aliases", { mode: "json" }).$type<string[]>().notNull(),
    category: text("category").$type<FoodCategory>().notNull(),
    defaultUnit: text("default_unit").$type<Unit>().notNull(),
    allergens: text("allergens", { mode: "json" })
      .$type<Allergen[]>()
      .notNull(),
    ...timestamps,
  },
  (table) => [
    uniqueIndex("foods_normalized_name_unique").on(table.normalizedName),
  ],
);

export const foodNutrition = sqliteTable(
  "food_nutrition",
  {
    foodId: text("food_id")
      .primaryKey()
      .references(() => foods.id, { onDelete: "cascade" }),
    referenceAmount: real("reference_amount").notNull(),
    referenceUnit: text("reference_unit").$type<Unit>().notNull(),
    caloriesKcal: real("calories_kcal").notNull(),
    proteinGrams: real("protein_grams").notNull(),
    carbohydratesGrams: real("carbohydrates_grams").notNull(),
    fatGrams: real("fat_grams").notNull(),
    sourceProvider: text("source_provider").notNull(),
    sourceExternalId: text("source_external_id").notNull(),
    sourceUrl: text("source_url").notNull(),
    sourceRetrievedAt: integer("source_retrieved_at", {
      mode: "timestamp_ms",
    }).notNull(),
    ...timestamps,
  },
  (table) => [
    check("food_nutrition_reference_positive", sql`${table.referenceAmount} > 0`),
    check("food_nutrition_calories_non_negative", sql`${table.caloriesKcal} >= 0`),
    check("food_nutrition_protein_non_negative", sql`${table.proteinGrams} >= 0`),
    check("food_nutrition_carbs_non_negative", sql`${table.carbohydratesGrams} >= 0`),
    check("food_nutrition_fat_non_negative", sql`${table.fatGrams} >= 0`),
  ],
);

export const foodPackageOffers = sqliteTable(
  "food_package_offers",
  {
    id: text("id").primaryKey(),
    foodId: text("food_id")
      .notNull()
      .references(() => foods.id, { onDelete: "cascade" }),
    label: text("label").notNull(),
    amount: real("amount").notNull(),
    unit: text("unit").$type<Unit>().notNull(),
    priceCents: integer("price_cents").notNull(),
    currency: text("currency").$type<"EUR">().notNull().default("EUR"),
    sourceType: text("source_type").$type<PriceSourceType>().notNull(),
    sourceProvider: text("source_provider"),
    sourceUrl: text("source_url"),
    priceObservedAt: integer("price_observed_at", {
      mode: "timestamp_ms",
    }).notNull(),
    ...timestamps,
  },
  (table) => [
    index("food_package_offers_food_id_idx").on(table.foodId),
    check("food_package_offers_amount_positive", sql`${table.amount} > 0`),
    check("food_package_offers_price_positive", sql`${table.priceCents} > 0`),
  ],
);

export const inventoryItems = sqliteTable(
  "inventory_items",
  {
    id: text("id").primaryKey(),
    foodId: text("food_id")
      .notNull()
      .references(() => foods.id, { onDelete: "restrict" }),
    amount: real("amount").notNull(),
    unit: text("unit").$type<Unit>().notNull(),
    storageLocation: text("storage_location")
      .$type<StorageLocation>()
      .notNull(),
    expiresAt: integer("expires_at", { mode: "timestamp_ms" }),
    openedAt: integer("opened_at", { mode: "timestamp_ms" }),
    ...timestamps,
  },
  (table) => [
    index("inventory_items_food_id_idx").on(table.foodId),
    index("inventory_items_expires_at_idx").on(table.expiresAt),
    check("inventory_items_amount_positive", sql`${table.amount} > 0`),
  ],
);

export const recipes = sqliteTable(
  "recipes",
  {
    id: text("id").primaryKey(),
    title: text("title").notNull(),
    description: text("description").notNull(),
    servings: integer("servings").notNull(),
    prepMinutes: integer("prep_minutes").notNull(),
    cookMinutes: integer("cook_minutes").notNull(),
    instructions: text("instructions", { mode: "json" })
      .$type<string[]>()
      .notNull(),
    caloriesKcal: real("calories_kcal"),
    proteinGrams: real("protein_grams"),
    carbohydratesGrams: real("carbohydrates_grams"),
    fatGrams: real("fat_grams"),
    dietaryTags: text("dietary_tags", { mode: "json" })
      .$type<DietaryTag[]>()
      .notNull(),
    sourceType: text("source_type")
      .$type<"original" | "api" | "user">()
      .notNull(),
    sourceProvider: text("source_provider"),
    sourceExternalId: text("source_external_id"),
    sourceUrl: text("source_url"),
    sourceLicense: text("source_license"),
    sourceAttribution: text("source_attribution"),
    ...timestamps,
  },
  (table) => [
    check("recipes_servings_positive", sql`${table.servings} > 0`),
    check("recipes_prep_minutes_non_negative", sql`${table.prepMinutes} >= 0`),
    check("recipes_cook_minutes_non_negative", sql`${table.cookMinutes} >= 0`),
  ],
);

export const recipeIngredients = sqliteTable(
  "recipe_ingredients",
  {
    id: text("id").primaryKey(),
    recipeId: text("recipe_id")
      .notNull()
      .references(() => recipes.id, { onDelete: "cascade" }),
    foodId: text("food_id")
      .notNull()
      .references(() => foods.id, { onDelete: "restrict" }),
    amount: real("amount").notNull(),
    unit: text("unit").$type<Unit>().notNull(),
    requirement: text("requirement")
      .$type<"required" | "optional">()
      .notNull(),
    preparation: text("preparation"),
    position: integer("position").notNull(),
  },
  (table) => [
    index("recipe_ingredients_recipe_id_idx").on(table.recipeId),
    index("recipe_ingredients_food_id_idx").on(table.foodId),
    uniqueIndex("recipe_ingredients_recipe_position_unique").on(
      table.recipeId,
      table.position,
    ),
    check("recipe_ingredients_amount_positive", sql`${table.amount} > 0`),
    check("recipe_ingredients_position_non_negative", sql`${table.position} >= 0`),
  ],
);

export const ingredientSubstitutes = sqliteTable(
  "ingredient_substitutes",
  {
    id: text("id").primaryKey(),
    recipeIngredientId: text("recipe_ingredient_id")
      .notNull()
      .references(() => recipeIngredients.id, { onDelete: "cascade" }),
    foodId: text("food_id")
      .notNull()
      .references(() => foods.id, { onDelete: "restrict" }),
    amount: real("amount").notNull(),
    unit: text("unit").$type<Unit>().notNull(),
  },
  (table) => [
    index("ingredient_substitutes_ingredient_id_idx").on(
      table.recipeIngredientId,
    ),
    check("ingredient_substitutes_amount_positive", sql`${table.amount} > 0`),
  ],
);

export const shoppingListItems = sqliteTable(
  "shopping_list_items",
  {
    id: text("id").primaryKey(),
    foodId: text("food_id")
      .notNull()
      .references(() => foods.id, { onDelete: "restrict" }),
    amount: real("amount").notNull(),
    unit: text("unit").$type<Unit>().notNull(),
    checked: integer("checked", { mode: "boolean" })
      .notNull()
      .default(false),
    ...timestamps,
  },
  (table) => [
    uniqueIndex("shopping_list_items_food_id_unique").on(table.foodId),
    check("shopping_list_items_amount_positive", sql`${table.amount} > 0`),
  ],
);
