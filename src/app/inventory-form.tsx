"use client";

import { useActionState, useState } from "react";

import type { Unit } from "@/domain";
import { initialInventoryFormState } from "@/features/inventory/schema";
import { createInventoryItem } from "./actions";

type FoodOption = {
  id: string;
  name: string;
  defaultUnit: Unit;
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

export function InventoryForm({ foods }: { foods: FoodOption[] }) {
  const [state, formAction, pending] = useActionState(
    createInventoryItem,
    initialInventoryFormState,
  );
  const [unit, setUnit] = useState<Unit>(foods[0]?.defaultUnit ?? "g");

  return (
    <form action={formAction} className="space-y-5">
      <div>
        <label htmlFor="foodId" className="field-label">
          Lebensmittel
        </label>
        <select
          id="foodId"
          name="foodId"
          required
          className="field-control"
          onChange={(event) => {
            const food = foods.find((item) => item.id === event.target.value);
            if (food) setUnit(food.defaultUnit);
          }}
        >
          {foods.map((food) => (
            <option key={food.id} value={food.id}>
              {food.name}
            </option>
          ))}
        </select>
        <FieldError errors={state.errors?.foodId} />
      </div>

      <div className="grid grid-cols-[1fr_8rem] gap-3">
        <div>
          <label htmlFor="amount" className="field-label">
            Menge
          </label>
          <input
            id="amount"
            name="amount"
            type="number"
            min="0.01"
            step="0.01"
            placeholder="500"
            required
            className="field-control"
          />
          <FieldError errors={state.errors?.amount} />
        </div>
        <div>
          <label htmlFor="unit" className="field-label">
            Einheit
          </label>
          <select
            id="unit"
            name="unit"
            value={unit}
            onChange={(event) => setUnit(event.target.value as Unit)}
            className="field-control"
          >
            {Object.entries(unitLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="storageLocation" className="field-label">
          Lagerort
        </label>
        <select
          id="storageLocation"
          name="storageLocation"
          className="field-control"
          defaultValue="pantry"
        >
          <option value="pantry">Vorratsschrank</option>
          <option value="fridge">Kühlschrank</option>
          <option value="freezer">Gefrierschrank</option>
        </select>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="expiresAt" className="field-label">
            Verbrauchsdatum
          </label>
          <input id="expiresAt" name="expiresAt" type="date" className="field-control" />
        </div>
        <div>
          <label htmlFor="openedAt" className="field-label">
            Geöffnet am
          </label>
          <input id="openedAt" name="openedAt" type="date" className="field-control" />
        </div>
      </div>

      <p
        aria-live="polite"
        className={state.status === "error" ? "text-sm text-red-700" : "text-sm text-[#315c3b]"}
      >
        {state.message}
      </p>

      <button
        type="submit"
        disabled={pending || foods.length === 0}
        className="w-full rounded-2xl bg-[#315c3b] px-5 py-3.5 font-semibold text-white transition hover:bg-[#274c30] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {pending ? "Wird gespeichert …" : "Zum Vorrat hinzufügen"}
      </button>
    </form>
  );
}

function FieldError({ errors }: { errors?: string[] }) {
  if (!errors?.length) return null;
  return <p className="mt-1 text-xs text-red-700">{errors[0]}</p>;
}
