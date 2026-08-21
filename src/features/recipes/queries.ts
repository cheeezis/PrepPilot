import { asc, eq } from "drizzle-orm";

import { db } from "@/db";
import { foods, inventoryItems, recipeIngredients, recipes } from "@/db/schema";
import {
  matchRecipe,
  rankRecipes,
  type MatchableRecipe,
} from "@/features/matching/match";

export async function getRankedRecipes() {
  const [allRecipes, inventory] = await Promise.all([
    getRecipes(),
    getMatchableInventory(),
  ]);
  return rankRecipes(allRecipes, inventory);
}

export async function getRecipeMatch(id: string) {
  const [allRecipes, inventory] = await Promise.all([
    getRecipes(),
    getMatchableInventory(),
  ]);
  const recipe = allRecipes.find((item) => item.id === id);
  return recipe ? matchRecipe(recipe, inventory) : null;
}

export async function getRecipes(): Promise<MatchableRecipe[]> {
  const [recipeRows, ingredientRows] = await Promise.all([
    db.select().from(recipes).orderBy(asc(recipes.title)),
    db
      .select({
        recipeId: recipeIngredients.recipeId,
        foodId: recipeIngredients.foodId,
        foodName: foods.name,
        amount: recipeIngredients.amount,
        unit: recipeIngredients.unit,
        requirement: recipeIngredients.requirement,
        preparation: recipeIngredients.preparation,
      })
      .from(recipeIngredients)
      .innerJoin(foods, eq(recipeIngredients.foodId, foods.id))
      .orderBy(asc(recipeIngredients.position)),
  ]);

  return recipeRows.map((recipe) => ({
    id: recipe.id,
    title: recipe.title,
    description: recipe.description,
    servings: recipe.servings,
    prepMinutes: recipe.prepMinutes,
    cookMinutes: recipe.cookMinutes,
    instructions: recipe.instructions,
    caloriesKcal: recipe.caloriesKcal,
    proteinGrams: recipe.proteinGrams,
    carbohydratesGrams: recipe.carbohydratesGrams,
    fatGrams: recipe.fatGrams,
    dietaryTags: recipe.dietaryTags,
    ingredients: ingredientRows.filter(
      (ingredient) => ingredient.recipeId === recipe.id,
    ),
  }));
}

async function getMatchableInventory() {
  return db
    .select({
      foodId: inventoryItems.foodId,
      amount: inventoryItems.amount,
      unit: inventoryItems.unit,
      expiresAt: inventoryItems.expiresAt,
    })
    .from(inventoryItems);
}
