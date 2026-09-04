export type BaseUnit = 'g' | 'ml'

export type Food = {
  id: number
  name: string
  base_unit: BaseUnit
  calories_kcal: number
  protein_g: number
  carbohydrates_g: number
  fat_g: number
  created_at: string
  updated_at: string
}

export type FoodInput = Pick<
  Food,
  | 'name'
  | 'base_unit'
  | 'calories_kcal'
  | 'protein_g'
  | 'carbohydrates_g'
  | 'fat_g'
>

export async function listFoods(signal?: AbortSignal): Promise<Food[]> {
  return request<Food[]>('/api/foods', { signal })
}

export async function createFood(input: FoodInput): Promise<Food> {
  return request<Food>('/api/foods', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export async function updateFood(id: number, input: FoodInput): Promise<Food> {
  return request<Food>(`/api/foods/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export async function deleteFood(id: number): Promise<void> {
  await request<void>(`/api/foods/${id}`, { method: 'DELETE' })
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string
    } | null
    throw new Error(body?.detail ?? 'Lebensmittelkatalog nicht verfügbar')
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
