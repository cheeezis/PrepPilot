from fastapi.testclient import TestClient


def create_food(
    client: TestClient,
    name: str,
    unit: str,
    calories: float,
    protein: float,
    carbohydrates: float,
    fat: float,
) -> int:
    response = client.post(
        "/api/foods",
        json={
            "name": name,
            "base_unit": unit,
            "calories_kcal": calories,
            "protein_g": protein,
            "carbohydrates_g": carbohydrates,
            "fat_g": fat,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def recipe_payload(oats_id: int, milk_id: int) -> dict[str, object]:
    return {
        "title": "Porridge",
        "servings": 2,
        "meal_roles": ["snack", "breakfast"],
        "ingredients": [
            {"food_id": oats_id, "amount": 100},
            {"food_id": milk_id, "amount": 200},
        ],
        "instructions": ["Alles verrühren.", "Kurz aufkochen."],
    }


def test_recipe_crud_and_nutrition(client: TestClient) -> None:
    oats_id = create_food(client, "Haferflocken", "g", 370, 13, 60, 7)
    milk_id = create_food(client, "Milch", "ml", 50, 3.4, 4.8, 1.5)

    created = client.post("/api/recipes", json=recipe_payload(oats_id, milk_id))

    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Porridge"
    assert body["servings"] == 2
    assert body["is_meal_prep"] is True
    assert body["meal_roles"] == ["breakfast", "snack"]
    assert body["ingredients"] == [
        {
            "food_id": oats_id,
            "food_name": "Haferflocken",
            "amount": 100.0,
            "unit": "g",
            "position": 0,
        },
        {
            "food_id": milk_id,
            "food_name": "Milch",
            "amount": 200.0,
            "unit": "ml",
            "position": 1,
        },
    ]
    assert body["nutrition_total"] == {
        "calories_kcal": 470.0,
        "protein_g": 19.8,
        "carbohydrates_g": 69.6,
        "fat_g": 10.0,
    }
    assert body["nutrition_per_serving"] == {
        "calories_kcal": 235.0,
        "protein_g": 9.9,
        "carbohydrates_g": 34.8,
        "fat_g": 5.0,
    }
    assert client.get("/api/recipes").json()[0]["id"] == body["id"]

    payload = recipe_payload(oats_id, milk_id)
    payload["title"] = "Schnelles Porridge"
    payload["servings"] = 1
    updated = client.put(f"/api/recipes/{body['id']}", json=payload)
    assert updated.status_code == 200
    assert updated.json()["title"] == "Schnelles Porridge"
    assert updated.json()["is_meal_prep"] is False

    assert client.delete(f"/api/recipes/{body['id']}").status_code == 204
    assert client.get("/api/recipes").json() == []


def test_recipe_rejects_unknown_food(client: TestClient) -> None:
    response = client.post(
        "/api/recipes",
        json={
            "title": "Unvollständig",
            "servings": 1,
            "meal_roles": ["lunch"],
            "ingredients": [{"food_id": 999, "amount": 100}],
            "instructions": ["Zubereiten."],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Unbekannte Lebensmittel-ID: 999"


def test_recipe_requires_unique_roles_foods_and_nonblank_steps(
    client: TestClient,
) -> None:
    food_id = create_food(client, "Reis", "g", 350, 7, 77, 1)
    payload = recipe_payload(food_id, food_id)
    payload["meal_roles"] = ["lunch", "lunch"]
    payload["instructions"] = ["   "]

    assert client.post("/api/recipes", json=payload).status_code == 422


def test_food_used_by_recipe_cannot_be_deleted(client: TestClient) -> None:
    oats_id = create_food(client, "Haferflocken", "g", 370, 13, 60, 7)
    milk_id = create_food(client, "Milch", "ml", 50, 3.4, 4.8, 1.5)
    recipe = client.post("/api/recipes", json=recipe_payload(oats_id, milk_id))
    assert recipe.status_code == 201

    response = client.delete(f"/api/foods/{oats_id}")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Lebensmittel wird bereits in einem Rezept verwendet"
    )


def test_unknown_recipe_returns_not_found(client: TestClient) -> None:
    food_id = create_food(client, "Reis", "g", 350, 7, 77, 1)
    payload = recipe_payload(food_id, food_id + 1)

    assert client.put("/api/recipes/404", json=payload).status_code == 404
    assert client.delete("/api/recipes/404").status_code == 404
