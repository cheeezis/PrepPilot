export type RecipeActionState = {
  status: "idle" | "error" | "success";
  message: string;
};

export const initialRecipeActionState: RecipeActionState = {
  status: "idle",
  message: "",
};
