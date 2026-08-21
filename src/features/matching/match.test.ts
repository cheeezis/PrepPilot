import { describe, expect, it } from "vitest";

import type { MatchableRecipe } from "./match";
import { matchRecipe, rankRecipes } from "./match";

const recipe: MatchableRecipe = {
  id: "test",
  title: "Testrezept",
  description: "",
  servings: 2,
  prepMinutes: 10,
  cookMinutes: 20,
  instructions: [],
  caloriesKcal: null,
  proteinGrams: null,
  carbohydratesGrams: null,
  fatGrams: null,
  dietaryTags: [],
  ingredients: [
    { foodId: "rice", foodName: "Reis", amount: 500, unit: "g", requirement: "required", preparation: null },
    { foodId: "onion", foodName: "Zwiebel", amount: 1, unit: "piece", requirement: "required", preparation: null },
    { foodId: "garlic", foodName: "Knoblauch", amount: 1, unit: "piece", requirement: "optional", preparation: null },
  ],
};

describe("matchRecipe", () => {
  it("berücksichtigt Mengen und kompatible Einheiten", () => {
    const result = matchRecipe(recipe, [
      { foodId: "rice", amount: 0.5, unit: "kg", expiresAt: null },
      { foodId: "onion", amount: 1, unit: "piece", expiresAt: null },
    ]);

    expect(result.canCook).toBe(true);
    expect(result.requiredAvailable).toBe(2);
    expect(result.score).toBe(80);
  });

  it("weist Teilmengen und die fehlende Menge aus", () => {
    const result = matchRecipe(recipe, [
      { foodId: "rice", amount: 200, unit: "g", expiresAt: null },
    ]);
    const rice = result.ingredientMatches[0];

    expect(rice.status).toBe("partial");
    expect(rice.missingAmount).toBe(300);
    expect(result.canCook).toBe(false);
    expect(result.score).toBe(16);
  });

  it("gewichtet bald ablaufende Zutaten höher", () => {
    const now = new Date("2026-08-21T10:00:00Z");
    const normal = matchRecipe(
      recipe,
      [{ foodId: "rice", amount: 500, unit: "g", expiresAt: null }],
      now,
    );
    const expiring = matchRecipe(
      recipe,
      [{ foodId: "rice", amount: 500, unit: "g", expiresAt: new Date("2026-08-22T10:00:00Z") }],
      now,
    );

    expect(expiring.score).toBeGreaterThan(normal.score);
    expect(expiring.reasons[1]).toContain("bald ablaufende");
  });

  it("sortiert bessere Matches zuerst", () => {
    const worse: MatchableRecipe = {
      ...recipe,
      id: "worse",
      ingredients: [
        ...recipe.ingredients,
        { foodId: "tofu", foodName: "Tofu", amount: 200, unit: "g", requirement: "required", preparation: null },
      ],
    };
    const ranked = rankRecipes([worse, recipe], [
      { foodId: "rice", amount: 500, unit: "g", expiresAt: null },
      { foodId: "onion", amount: 1, unit: "piece", expiresAt: null },
    ]);

    expect(ranked[0].id).toBe("test");
  });
});
