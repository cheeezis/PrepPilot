import type { Quantity } from "./food";

export const STORAGE_LOCATIONS = ["pantry", "fridge", "freezer"] as const;

export type StorageLocation = (typeof STORAGE_LOCATIONS)[number];

export type InventoryItem = {
  id: string;
  foodId: string;
  quantity: Quantity;
  storageLocation: StorageLocation;
  expiresAt: string | null;
  openedAt: string | null;
};
