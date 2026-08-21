import { z } from "zod";

import { STORAGE_LOCATIONS, UNITS } from "@/domain";

const optionalDate = z
  .string()
  .refine(
    (value) => value === "" || /^\d{4}-\d{2}-\d{2}$/.test(value),
    "Bitte wähle ein gültiges Datum.",
  )
  .transform((value) => (value ? new Date(`${value}T12:00:00`) : null));

export const inventoryFormSchema = z.object({
  foodId: z.string().min(1, "Bitte wähle ein Lebensmittel."),
  amount: z.coerce
    .number<number>()
    .positive("Die Menge muss größer als null sein."),
  unit: z.enum(UNITS),
  storageLocation: z.enum(STORAGE_LOCATIONS),
  expiresAt: optionalDate,
  openedAt: optionalDate,
});

export const inventoryUpdateFormSchema = inventoryFormSchema.omit({
  foodId: true,
});

export type InventoryFormState = {
  status: "idle" | "error" | "success";
  message: string;
  errors?: Record<string, string[]>;
};

export const initialInventoryFormState: InventoryFormState = {
  status: "idle",
  message: "",
};
