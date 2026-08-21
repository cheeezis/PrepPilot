import { describe, expect, it } from "vitest";

import { purchasedItemFormSchema } from "./schema";

describe("purchasedItemFormSchema", () => {
  it("akzeptiert Lagerort und optionales Verbrauchsdatum", () => {
    const result = purchasedItemFormSchema.safeParse({
      storageLocation: "fridge",
      expiresAt: "2026-08-30",
    });

    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.expiresAt).toBeInstanceOf(Date);
    }
  });

  it("lehnt einen unbekannten Lagerort ab", () => {
    expect(
      purchasedItemFormSchema.safeParse({
        storageLocation: "garage",
        expiresAt: "",
      }).success,
    ).toBe(false);
  });
});
