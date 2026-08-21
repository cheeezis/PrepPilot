"use client";

import { useActionState, useState } from "react";
import { useFormStatus } from "react-dom";

import type { StorageLocation, Unit } from "@/domain";
import { initialInventoryFormState } from "@/features/inventory/schema";
import { deleteInventoryItem, updateInventoryItem } from "./actions";

type InventoryItemActionsProps = {
  id: string;
  foodName: string;
  amount: number;
  unit: Unit;
  storageLocation: StorageLocation;
  expiresAt: string | null;
  openedAt: string | null;
};

const unitLabels: Record<Unit, string> = {
  g: "g",
  kg: "kg",
  ml: "ml",
  l: "l",
  piece: "Stück",
  tsp: "TL",
  tbsp: "EL",
};

export function InventoryItemActions({
  id,
  foodName,
  amount,
  unit,
  storageLocation,
  expiresAt,
  openedAt,
}: InventoryItemActionsProps) {
  const [isEditing, setIsEditing] = useState(false);
  const updateAction = updateInventoryItem.bind(null, id);
  const deleteAction = deleteInventoryItem.bind(null, id);
  const [state, formAction, pending] = useActionState(
    updateAction,
    initialInventoryFormState,
  );

  if (!isEditing) {
    return (
      <div className="flex shrink-0 items-center gap-1">
        <button
          type="button"
          onClick={() => setIsEditing(true)}
          className="rounded-xl px-3 py-2 text-sm font-medium text-[#51664c] transition hover:bg-[#edf2e9]"
        >
          Bearbeiten
        </button>
        <form action={deleteAction}>
          <DeleteButton foodName={foodName} />
        </form>
      </div>
    );
  }

  return (
    <form
      action={formAction}
      className="col-span-full mt-1 rounded-2xl bg-[#f6f6ef] p-4 sm:ml-[3.75rem]"
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <label className="text-xs font-semibold text-[#5d6659]">
          Menge
          <input
            name="amount"
            type="number"
            min="0.01"
            step="0.01"
            required
            defaultValue={amount}
            className="field-control mt-1"
          />
        </label>
        <label className="text-xs font-semibold text-[#5d6659]">
          Einheit
          <select name="unit" defaultValue={unit} className="field-control mt-1">
            {Object.entries(unitLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-semibold text-[#5d6659]">
          Lagerort
          <select
            name="storageLocation"
            defaultValue={storageLocation}
            className="field-control mt-1"
          >
            <option value="pantry">Vorratsschrank</option>
            <option value="fridge">Kühlschrank</option>
            <option value="freezer">Gefrierschrank</option>
          </select>
        </label>
        <label className="text-xs font-semibold text-[#5d6659]">
          Verbrauchsdatum
          <input
            name="expiresAt"
            type="date"
            defaultValue={expiresAt ?? ""}
            className="field-control mt-1"
          />
        </label>
        <label className="text-xs font-semibold text-[#5d6659]">
          Geöffnet am
          <input
            name="openedAt"
            type="date"
            defaultValue={openedAt ?? ""}
            className="field-control mt-1"
          />
        </label>
      </div>

      {state.message && (
        <p
          aria-live="polite"
          className={`mt-3 text-sm ${
            state.status === "error" ? "text-red-700" : "text-[#315c3b]"
          }`}
        >
          {state.message}
        </p>
      )}

      <div className="mt-4 flex justify-end gap-2">
        <button
          type="button"
          onClick={() => setIsEditing(false)}
          className="rounded-xl px-3 py-2 text-sm font-medium text-[#626a5f] hover:bg-black/5"
        >
          Abbrechen
        </button>
        <button
          type="submit"
          disabled={pending}
          className="rounded-xl bg-[#315c3b] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          {pending ? "Speichert …" : "Speichern"}
        </button>
      </div>
    </form>
  );
}

function DeleteButton({ foodName }: { foodName: string }) {
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      aria-label={`${foodName} löschen`}
      className="rounded-xl px-3 py-2 text-sm font-medium text-[#8a554f] transition hover:bg-[#f6e9e6] disabled:opacity-50"
    >
      {pending ? "Löscht …" : "Löschen"}
    </button>
  );
}
