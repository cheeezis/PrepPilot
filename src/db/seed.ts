import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";

import type { DietaryTag, Food, IngredientRequirement, Unit } from "../domain";
import {
  validateFoodPackageOffer,
  validateNutritionProfile,
} from "../domain";
import {
  foodNutrition,
  foodPackageOffers,
  foods,
  recipeIngredients,
  recipes,
} from "./schema";
import {
  referenceNutritionProfiles,
  referencePackageOffers,
} from "./seed-data/optimization";

const seedFoods: Food[] = [
  { id: "rice", name: "Reis", aliases: ["Langkornreis", "Basmatireis"], category: "grain", defaultUnit: "g", allergens: [] },
  { id: "pasta", name: "Nudeln", aliases: ["Pasta", "Spaghetti"], category: "grain", defaultUnit: "g", allergens: ["gluten"] },
  { id: "potato", name: "Kartoffel", aliases: ["Kartoffeln"], category: "vegetable", defaultUnit: "g", allergens: [] },
  { id: "onion", name: "Zwiebel", aliases: ["Zwiebeln"], category: "vegetable", defaultUnit: "piece", allergens: [] },
  { id: "garlic", name: "Knoblauch", aliases: ["Knoblauchzehe"], category: "vegetable", defaultUnit: "piece", allergens: [] },
  { id: "tomato", name: "Tomate", aliases: ["Tomaten", "Cherrytomaten"], category: "vegetable", defaultUnit: "g", allergens: [] },
  { id: "bell-pepper", name: "Paprika", aliases: ["Gemüsepaprika"], category: "vegetable", defaultUnit: "piece", allergens: [] },
  { id: "broccoli", name: "Brokkoli", aliases: [], category: "vegetable", defaultUnit: "g", allergens: [] },
  { id: "carrot", name: "Karotte", aliases: ["Möhre", "Möhren"], category: "vegetable", defaultUnit: "g", allergens: [] },
  { id: "chickpeas", name: "Kichererbsen", aliases: ["Kichererbse"], category: "legume", defaultUnit: "g", allergens: [] },
  { id: "kidney-beans", name: "Kidneybohnen", aliases: [], category: "legume", defaultUnit: "g", allergens: [] },
  { id: "coconut-milk", name: "Kokosmilch", aliases: [], category: "other", defaultUnit: "ml", allergens: [] },
  { id: "tofu", name: "Tofu", aliases: ["Naturtofu"], category: "other", defaultUnit: "g", allergens: ["soy"] },
  { id: "chicken-breast", name: "Hähnchenbrust", aliases: ["Hähnchenfilet"], category: "meat", defaultUnit: "g", allergens: [] },
  { id: "egg", name: "Ei", aliases: ["Eier"], category: "egg", defaultUnit: "piece", allergens: ["eggs"] },
  { id: "yogurt", name: "Joghurt", aliases: ["Naturjoghurt"], category: "dairy", defaultUnit: "g", allergens: ["milk"] },
  { id: "feta", name: "Feta", aliases: ["Hirtenkäse"], category: "dairy", defaultUnit: "g", allergens: ["milk"] },
  { id: "oats", name: "Haferflocken", aliases: ["Hafer"], category: "grain", defaultUnit: "g", allergens: ["gluten"] },
];

type SeedIngredient = readonly [
  foodId: string,
  amount: number,
  unit: Unit,
  requirement: IngredientRequirement,
  preparation: string | null,
];

type SeedRecipe = {
  id: string;
  title: string;
  description: string;
  servings: number;
  prepMinutes: number;
  cookMinutes: number;
  instructions: readonly string[];
  caloriesKcal: number;
  proteinGrams: number;
  carbohydratesGrams: number;
  fatGrams: number;
  dietaryTags: readonly DietaryTag[];
  ingredients: readonly SeedIngredient[];
};

const seedRecipes: SeedRecipe[] = [
  {
    id: "chili-sin-carne",
    title: "Chili sin Carne mit Reis",
    description: "Würziges Bohnen-Chili mit Paprika, Tomaten und Reis.",
    servings: 2,
    prepMinutes: 10,
    cookMinutes: 25,
    instructions: ["Reis nach Packungsangabe garen.", "Zwiebel, Knoblauch und Paprika klein schneiden und anbraten.", "Tomaten und Kidneybohnen zugeben und 15 Minuten köcheln lassen.", "Chili abschmecken und mit dem Reis servieren."],
    caloriesKcal: 610,
    proteinGrams: 22,
    carbohydratesGrams: 105,
    fatGrams: 8,
    dietaryTags: ["vegan", "vegetarian", "gluten-free"],
    ingredients: [["rice", 160, "g", "required", null], ["kidney-beans", 240, "g", "required", "abgetropft"], ["tomato", 400, "g", "required", "gewürfelt"], ["bell-pepper", 1, "piece", "required", "gewürfelt"], ["onion", 1, "piece", "required", "fein gehackt"], ["garlic", 1, "piece", "optional", "fein gehackt"]],
  },
  {
    id: "chickpea-coconut-curry",
    title: "Kichererbsen-Kokos-Curry",
    description: "Cremiges, veganes Curry mit Brokkoli und Reis.",
    servings: 2,
    prepMinutes: 10,
    cookMinutes: 20,
    instructions: ["Reis nach Packungsangabe garen.", "Zwiebel und Knoblauch anbraten.", "Brokkoli, Kichererbsen und Kokosmilch zugeben.", "Curry 15 Minuten sanft köcheln lassen und mit Reis servieren."],
    caloriesKcal: 720,
    proteinGrams: 24,
    carbohydratesGrams: 101,
    fatGrams: 24,
    dietaryTags: ["vegan", "vegetarian", "gluten-free"],
    ingredients: [["rice", 160, "g", "required", null], ["chickpeas", 240, "g", "required", "abgetropft"], ["coconut-milk", 300, "ml", "required", null], ["broccoli", 250, "g", "required", "in Röschen"], ["onion", 1, "piece", "required", "fein gehackt"], ["garlic", 1, "piece", "optional", "fein gehackt"]],
  },
  {
    id: "chicken-broccoli-rice",
    title: "Hähnchen-Brokkoli-Reis",
    description: "Proteinreiche Reispfanne mit Hähnchen und Gemüse.",
    servings: 2,
    prepMinutes: 10,
    cookMinutes: 25,
    instructions: ["Reis garen und beiseitestellen.", "Hähnchen würfeln und vollständig durchbraten.", "Brokkoli und Karotte zugeben und bissfest garen.", "Reis unterheben und die Pfanne abschmecken."],
    caloriesKcal: 590,
    proteinGrams: 52,
    carbohydratesGrams: 68,
    fatGrams: 11,
    dietaryTags: ["high-protein", "gluten-free"],
    ingredients: [["rice", 160, "g", "required", null], ["chicken-breast", 350, "g", "required", "gewürfelt"], ["broccoli", 250, "g", "required", "in Röschen"], ["carrot", 150, "g", "required", "in Scheiben"], ["yogurt", 100, "g", "optional", "als Dip"]],
  },
  {
    id: "tomato-feta-pasta",
    title: "Tomaten-Feta-Pasta",
    description: "Schnelle vegetarische Pasta mit geschmolzenem Feta.",
    servings: 2,
    prepMinutes: 8,
    cookMinutes: 20,
    instructions: ["Nudeln al dente kochen.", "Zwiebel und Knoblauch anbraten, Tomaten zugeben.", "Feta zerbröseln und in der Sauce schmelzen lassen.", "Nudeln mit der Sauce vermengen und servieren."],
    caloriesKcal: 690,
    proteinGrams: 29,
    carbohydratesGrams: 88,
    fatGrams: 24,
    dietaryTags: ["vegetarian"],
    ingredients: [["pasta", 200, "g", "required", null], ["tomato", 400, "g", "required", "gewürfelt"], ["feta", 180, "g", "required", "zerbröselt"], ["onion", 1, "piece", "required", "fein gehackt"], ["garlic", 1, "piece", "optional", "fein gehackt"]],
  },
  {
    id: "vegetable-fried-rice",
    title: "Gebratener Gemüsereis",
    description: "Schnelle Reispfanne mit Ei und knackigem Gemüse.",
    servings: 2,
    prepMinutes: 10,
    cookMinutes: 15,
    instructions: ["Reis garen oder bereits gekochten Reis verwenden.", "Zwiebel, Karotte und Brokkoli kräftig anbraten.", "Gemüse zur Seite schieben und Eier in der Pfanne stocken lassen.", "Reis zugeben, alles vermengen und abschmecken."],
    caloriesKcal: 540,
    proteinGrams: 21,
    carbohydratesGrams: 76,
    fatGrams: 16,
    dietaryTags: ["vegetarian", "gluten-free"],
    ingredients: [["rice", 180, "g", "required", null], ["egg", 3, "piece", "required", "verquirlt"], ["carrot", 150, "g", "required", "klein gewürfelt"], ["broccoli", 200, "g", "required", "klein geschnitten"], ["onion", 1, "piece", "required", "fein gehackt"], ["tofu", 150, "g", "optional", "gewürfelt"]],
  },
];

async function main() {
  const client = createClient({ url: process.env.DB_FILE_NAME ?? "file:data/preppilot.db" });
  const seedDb = drizzle(client);

  await seedDb.insert(foods).values(seedFoods.map((food) => ({ ...food, normalizedName: food.name.toLocaleLowerCase("de-DE") }))).onConflictDoNothing();

  for (const profile of referenceNutritionProfiles) {
    const validation = validateNutritionProfile(profile);
    if (!validation.valid) {
      throw new Error(validation.errors.join(" "));
    }
    const values = {
      ...profile,
      sourceRetrievedAt: new Date(`${profile.sourceRetrievedAt}T12:00:00Z`),
    };
    await seedDb
      .insert(foodNutrition)
      .values(values)
      .onConflictDoUpdate({
        target: foodNutrition.foodId,
        set: values,
      });
  }

  for (const offer of referencePackageOffers) {
    const validation = validateFoodPackageOffer(offer);
    if (!validation.valid) {
      throw new Error(validation.errors.join(" "));
    }
    const values = {
      ...offer,
      priceObservedAt: new Date(`${offer.priceObservedAt}T12:00:00Z`),
    };
    await seedDb
      .insert(foodPackageOffers)
      .values(values)
      .onConflictDoUpdate({
        target: foodPackageOffers.id,
        set: values,
      });
  }

  for (const recipe of seedRecipes) {
    await seedDb.insert(recipes).values({
      id: recipe.id,
      title: recipe.title,
      description: recipe.description,
      servings: recipe.servings,
      prepMinutes: recipe.prepMinutes,
      cookMinutes: recipe.cookMinutes,
      instructions: [...recipe.instructions],
      caloriesKcal: recipe.caloriesKcal,
      proteinGrams: recipe.proteinGrams,
      carbohydratesGrams: recipe.carbohydratesGrams,
      fatGrams: recipe.fatGrams,
      dietaryTags: [...recipe.dietaryTags],
      sourceType: "original",
    }).onConflictDoNothing();

    await seedDb.insert(recipeIngredients).values(recipe.ingredients.map(([foodId, amount, unit, requirement, preparation], position) => ({
      id: `${recipe.id}-${position + 1}`,
      recipeId: recipe.id,
      foodId,
      amount,
      unit,
      requirement,
      preparation,
      position,
    }))).onConflictDoNothing();
  }

  client.close();
  console.log(
    `${seedFoods.length} Lebensmittel, ${seedRecipes.length} Rezepte und ` +
      `${referenceNutritionProfiles.length} Optimierungsprofile sind verfügbar.`,
  );
}

main().catch((error: unknown) => {
  console.error("Seed-Daten konnten nicht angelegt werden.", error);
  process.exitCode = 1;
});
