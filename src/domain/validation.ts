import type { Quantity } from "./food";
import type { InventoryItem } from "./inventory";
import type { FoodPackageOffer, NutritionProfile } from "./nutrition";
import type { Recipe } from "./recipe";

export type ValidationResult =
  | { valid: true }
  | { valid: false; errors: string[] };

export function validateQuantity(quantity: Quantity): ValidationResult {
  if (!Number.isFinite(quantity.amount) || quantity.amount <= 0) {
    return { valid: false, errors: ["Quantity must be greater than zero."] };
  }

  return { valid: true };
}

export function validateInventoryItem(item: InventoryItem): ValidationResult {
  const errors: string[] = [];
  const quantityResult = validateQuantity(item.quantity);

  if (!item.id.trim()) errors.push("Inventory item requires an id.");
  if (!item.foodId.trim()) errors.push("Inventory item requires a food id.");
  if (!quantityResult.valid) errors.push(...quantityResult.errors);

  return errors.length > 0 ? { valid: false, errors } : { valid: true };
}

export function validateRecipe(recipe: Recipe): ValidationResult {
  const errors: string[] = [];

  if (!recipe.id.trim()) errors.push("Recipe requires an id.");
  if (!recipe.title.trim()) errors.push("Recipe requires a title.");
  if (!Number.isInteger(recipe.servings) || recipe.servings <= 0) {
    errors.push("Recipe servings must be a positive integer.");
  }
  if (recipe.prepMinutes < 0 || recipe.cookMinutes < 0) {
    errors.push("Recipe times cannot be negative.");
  }
  if (recipe.ingredients.length === 0) {
    errors.push("Recipe requires at least one ingredient.");
  }
  if (recipe.instructions.length === 0) {
    errors.push("Recipe requires at least one instruction.");
  }

  recipe.ingredients.forEach((ingredient, index) => {
    if (!ingredient.foodId.trim()) {
      errors.push(`Ingredient ${index + 1} requires a food id.`);
    }

    const quantityResult = validateQuantity(ingredient.quantity);
    if (!quantityResult.valid) {
      errors.push(
        ...quantityResult.errors.map(
          (error) => `Ingredient ${index + 1}: ${error}`,
        ),
      );
    }
  });

  return errors.length > 0 ? { valid: false, errors } : { valid: true };
}

export function validateNutritionProfile(
  profile: NutritionProfile,
): ValidationResult {
  const errors: string[] = [];

  if (!profile.foodId.trim()) errors.push("Nutrition profile requires a food id.");
  if (!Number.isFinite(profile.referenceAmount) || profile.referenceAmount <= 0) {
    errors.push("Nutrition reference amount must be greater than zero.");
  }
  const nutrients = [
    ["Calories", profile.caloriesKcal],
    ["Protein", profile.proteinGrams],
    ["Carbohydrates", profile.carbohydratesGrams],
    ["Fat", profile.fatGrams],
  ] as const;
  for (const [name, value] of nutrients) {
    if (!Number.isFinite(value) || value < 0) {
      errors.push(`${name} cannot be negative.`);
    }
  }
  if (!profile.sourceProvider.trim()) {
    errors.push("Nutrition profile requires a source provider.");
  }
  if (!profile.sourceExternalId.trim()) {
    errors.push("Nutrition profile requires an external source id.");
  }
  if (!isHttpUrl(profile.sourceUrl)) {
    errors.push("Nutrition profile requires a valid source URL.");
  }
  if (!isIsoDate(profile.sourceRetrievedAt)) {
    errors.push("Nutrition profile requires a valid retrieval date.");
  }

  return errors.length > 0 ? { valid: false, errors } : { valid: true };
}

export function validateFoodPackageOffer(
  offer: FoodPackageOffer,
): ValidationResult {
  const errors: string[] = [];

  if (!offer.id.trim()) errors.push("Package offer requires an id.");
  if (!offer.foodId.trim()) errors.push("Package offer requires a food id.");
  if (!offer.label.trim()) errors.push("Package offer requires a label.");
  if (!Number.isFinite(offer.amount) || offer.amount <= 0) {
    errors.push("Package amount must be greater than zero.");
  }
  if (!Number.isInteger(offer.priceCents) || offer.priceCents <= 0) {
    errors.push("Package price must be a positive integer in cents.");
  }
  if (!isIsoDate(offer.priceObservedAt)) {
    errors.push("Package offer requires a valid observation date.");
  }
  if (offer.sourceType === "retailer" && !offer.sourceProvider?.trim()) {
    errors.push("Retailer price requires a source provider.");
  }
  if (offer.sourceUrl !== null && !isHttpUrl(offer.sourceUrl)) {
    errors.push("Package offer source URL must be valid.");
  }

  return errors.length > 0 ? { valid: false, errors } : { valid: true };
}

function isHttpUrl(value: string) {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function isIsoDate(value: string) {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
}
