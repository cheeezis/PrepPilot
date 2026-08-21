import type { Quantity } from "./food";
import type { InventoryItem } from "./inventory";
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

