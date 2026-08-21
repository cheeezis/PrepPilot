import Link from "next/link";
import { notFound } from "next/navigation";

import { getRecipeMatch } from "@/features/recipes/queries";
import { RecipeActions } from "../recipe-actions";

const unitLabels = {
  g: "g",
  kg: "kg",
  ml: "ml",
  l: "l",
  piece: "Stück",
  tsp: "TL",
  tbsp: "EL",
} as const;

const tagLabels = {
  vegan: "Vegan",
  vegetarian: "Vegetarisch",
  pescatarian: "Pescetarisch",
  "gluten-free": "Glutenfrei",
  "high-protein": "Proteinreich",
} as const;

export const dynamic = "force-dynamic";

export default async function RecipePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const recipe = await getRecipeMatch(id);
  if (!recipe) notFound();

  return (
    <main className="min-h-screen bg-[#f3f1e8] px-5 py-8 text-[#1f2921] sm:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6 flex items-center justify-between">
          <Link href="/" className="rounded-xl px-3 py-2 text-sm font-medium text-[#52604e] hover:bg-white/60">
            ← Zur Übersicht
          </Link>
          <Link href="/shopping-list" className="rounded-xl px-3 py-2 text-sm font-medium text-[#52604e] hover:bg-white/60">
            Einkaufsliste
          </Link>
        </div>

        <article className="overflow-hidden rounded-[2rem] bg-[#fffdf7] shadow-[0_20px_70px_rgba(44,58,39,0.09)]">
          <header className="bg-[#dfead8] p-7 sm:p-10">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
              <div className="max-w-2xl">
                <div className="mb-3 flex flex-wrap gap-2">
                  {recipe.dietaryTags.map((tag) => (
                    <span key={tag} className="rounded-full bg-white/65 px-3 py-1 text-xs font-semibold text-[#50634b]">
                      {tagLabels[tag]}
                    </span>
                  ))}
                </div>
                <h1 className="text-3xl font-bold tracking-[-0.04em] sm:text-5xl">
                  {recipe.title}
                </h1>
                <p className="mt-4 max-w-xl leading-7 text-[#596755]">{recipe.description}</p>
              </div>
              <div className="grid size-24 shrink-0 place-items-center rounded-full bg-[#315c3b] text-center text-white">
                <div><strong className="block text-2xl">{recipe.score}%</strong><span className="text-xs">Match</span></div>
              </div>
            </div>
            <div className="mt-7 flex flex-wrap gap-5 text-sm font-medium text-[#4d5e49]">
              <span>{recipe.servings} Portionen</span>
              <span>{recipe.prepMinutes + recipe.cookMinutes} Minuten</span>
              {recipe.caloriesKcal !== null && <span>{recipe.caloriesKcal} kcal / Portion</span>}
              {recipe.proteinGrams !== null && <span>{recipe.proteinGrams} g Protein</span>}
            </div>
          </header>

          <div className="grid gap-9 p-7 sm:p-10 lg:grid-cols-[1fr_0.9fr]">
            <section>
              <h2 className="text-2xl font-bold tracking-tight">Zutatencheck</h2>
              <div className="mt-5 space-y-3">
                {recipe.ingredientMatches.map((ingredient) => (
                  <div key={ingredient.foodId} className="flex items-center gap-3 rounded-2xl bg-[#f6f6ef] p-4">
                    <span className={`grid size-8 shrink-0 place-items-center rounded-full text-sm font-bold ${ingredient.status === "available" ? "bg-[#dcebd5] text-[#315c3b]" : ingredient.status === "partial" ? "bg-[#f4e7bd] text-[#735c18]" : "bg-[#f3dddd] text-[#8a4747]"}`}>
                      {ingredient.status === "available" ? "✓" : ingredient.status === "partial" ? "½" : "–"}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold">{ingredient.foodName}{ingredient.requirement === "optional" ? " (optional)" : ""}</p>
                      <p className="mt-0.5 text-sm text-[#737a70]">
                        {ingredient.amount} {unitLabels[ingredient.unit]}
                        {ingredient.preparation ? ` · ${ingredient.preparation}` : ""}
                      </p>
                    </div>
                    {ingredient.missingAmount > 0 && (
                      <span className="text-right text-xs font-medium text-[#8a554f]">
                        noch {formatAmount(ingredient.missingAmount)} {unitLabels[ingredient.unit]}
                      </span>
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-6 rounded-2xl border border-[#dce3d7] p-4">
                {recipe.reasons.map((reason) => <p key={reason} className="text-sm leading-6 text-[#5e6b5a]">• {reason}</p>)}
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold tracking-tight">Zubereitung</h2>
              <ol className="mt-5 space-y-5">
                {recipe.instructions.map((instruction, index) => (
                  <li key={instruction} className="flex gap-4">
                    <span className="grid size-8 shrink-0 place-items-center rounded-full bg-[#e5ecdf] text-sm font-bold text-[#4b6146]">{index + 1}</span>
                    <p className="pt-1 text-sm leading-6 text-[#596158]">{instruction}</p>
                  </li>
                ))}
              </ol>
            </section>
          </div>

          <footer className="border-t border-[#ecece4] p-7 sm:p-10">
            <RecipeActions recipeId={recipe.id} canCook={recipe.canCook} missingCount={recipe.missingRequiredCount} />
          </footer>
        </article>
      </div>
    </main>
  );
}

function formatAmount(amount: number) {
  return Number(amount.toFixed(2));
}
