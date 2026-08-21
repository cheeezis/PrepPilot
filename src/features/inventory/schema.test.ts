import { describe, expect, it } from "vitest";

import { inventoryFormSchema } from "./schema";

describe("inventoryFormSchema", () => {
  it("parses valid form values", () => {
    const result = inventoryFormSchema.safeParse({
      foodId: "rice",
      amount: "500",
      unit: "g",
      storageLocation: "pantry",
      expiresAt: "2026-12-31",
      openedAt: "",
    });

    expect(result.success).toBe(true);
    if (!result.success) return;

    expect(result.data.amount).toBe(500);
    expect(result.data.expiresAt).toBeInstanceOf(Date);
    expect(result.data.openedAt).toBeNull();
  });

  it("rejects missing foods and non-positive amounts", () => {
    const result = inventoryFormSchema.safeParse({
      foodId: "",
      amount: "0",
      unit: "g",
      storageLocation: "pantry",
      expiresAt: "",
      openedAt: "",
    });

    expect(result.success).toBe(false);
  });
});
