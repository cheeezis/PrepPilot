import { createClient } from "@libsql/client";
import { drizzle } from "drizzle-orm/libsql";

import type { Food } from "../domain";
import { foods } from "./schema";

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

async function main() {
  const client = createClient({
    url: process.env.DB_FILE_NAME ?? "file:data/preppilot.db",
  });
  const seedDb = drizzle(client);

  await seedDb
    .insert(foods)
    .values(
      seedFoods.map((food) => ({
        ...food,
        normalizedName: food.name.toLocaleLowerCase("de-DE"),
      })),
    )
    .onConflictDoNothing();

  client.close();
  console.log(`${seedFoods.length} Lebensmittel sind verfügbar.`);
}

main().catch((error: unknown) => {
  console.error("Lebensmittel konnten nicht angelegt werden.", error);
  process.exitCode = 1;
});
