import { z } from "zod";

import { STORAGE_LOCATIONS } from "@/domain";
import { optionalDateSchema } from "@/features/inventory/schema";

export const purchasedItemFormSchema = z.object({
  storageLocation: z.enum(STORAGE_LOCATIONS),
  expiresAt: optionalDateSchema,
});

export type PurchasedItemFormState = {
  status: "idle" | "error" | "success";
  message: string;
};

export const initialPurchasedItemFormState: PurchasedItemFormState = {
  status: "idle",
  message: "",
};
