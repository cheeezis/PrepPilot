from fastapi.testclient import TestClient


def test_weekly_plan_is_generated_persisted_and_reloaded(
    client: TestClient,
) -> None:
    food_id = create_food(client)
    portion = client.post(
        f"/api/foods/{food_id}/portions",
        json={"name": "Packung", "amount": 700},
    )
    assert portion.status_code == 201
    create_recipe(client, "Frühstück", 1, ["breakfast"], food_id)
    batch_id = create_recipe(
        client, "Sechser-Batch", 6, ["lunch", "dinner"], food_id
    )
    create_recipe(client, "Kleine Mahlzeit", 1, ["lunch", "dinner"], food_id)
    create_recipe(client, "Snack", 1, ["snack"], food_id)

    response = client.post("/api/weekly-plans/generate", json=plan_payload())

    assert response.status_code == 201
    plan = response.json()
    assert plan["start_date"] == "2026-09-07"
    assert plan["end_date"] == "2026-09-13"
    assert len(plan["assignments"]) == 28
    batch_assignments = [
        item for item in plan["assignments"] if item["recipe_id"] == batch_id
    ]
    assert [item["portion_number"] for item in batch_assignments] == list(
        range(1, 7)
    )
    assert len({item["day_index"] for item in batch_assignments}) == 6
    assert {item["recipe_servings"] for item in batch_assignments} == {6}

    assert client.get(f"/api/weekly-plans/{plan['id']}").json() == plan
    assert [item["id"] for item in client.get("/api/weekly-plans").json()] == [
        plan["id"]
    ]
    assert client.get(f"/api/weekly-plans/{plan['id']}/shopping-list").json() == [
        {
            "food_id": food_id,
            "food_name": "Testlebensmittel",
            "category": "other",
            "amount": 2800.0,
            "unit": "g",
            "equivalent_amount": 4,
            "equivalent_unit": "Packung",
        }
    ]


def test_existing_period_requires_confirmation_before_replacement(
    client: TestClient,
) -> None:
    create_complete_recipe_set(client)
    assert client.post(
        "/api/weekly-plans/generate", json=plan_payload()
    ).status_code == 201

    conflict = client.post("/api/weekly-plans/generate", json=plan_payload())
    assert conflict.status_code == 409
    assert conflict.json()["detail"] == (
        "Für diesen Zeitraum existiert bereits ein Wochenplan"
    )

    replacement = plan_payload()
    replacement["replace_existing"] = True
    assert client.post(
        "/api/weekly-plans/generate", json=replacement
    ).status_code == 201
    assert len(client.get("/api/weekly-plans").json()) == 1


def test_differently_overlapping_period_cannot_be_replaced(
    client: TestClient,
) -> None:
    create_complete_recipe_set(client)
    client.post("/api/weekly-plans/generate", json=plan_payload())
    overlapping = plan_payload()
    overlapping["start_date"] = "2026-09-10"
    overlapping["replace_existing"] = True

    response = client.post("/api/weekly-plans/generate", json=overlapping)

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Der Zeitraum überschneidet sich mit einem anderen Wochenplan"
    )


def test_generation_explains_missing_recipe(client: TestClient) -> None:
    response = client.post("/api/weekly-plans/generate", json=plan_payload())

    assert response.status_code == 422
    assert response.json()["detail"] == "Kein Einzelrezept für Tag 1, Frühstück verfügbar"


def test_unknown_plan_has_no_shopping_list(client: TestClient) -> None:
    assert client.get("/api/weekly-plans/404/shopping-list").status_code == 404


def test_meal_replacements_are_suggested_and_applied(client: TestClient) -> None:
    food_id = create_food(client)
    breakfast_ids = {
        create_recipe(client, title, 1, ["breakfast"], food_id)
        for title in ("Frühstück A", "Frühstück B")
    }
    create_recipe(client, "Mittagessen", 1, ["lunch"], food_id)
    create_recipe(client, "Abendessen", 1, ["dinner"], food_id)
    create_recipe(client, "Snack", 1, ["snack"], food_id)
    plan = client.post("/api/weekly-plans/generate", json=plan_payload()).json()
    assignment = next(
        item
        for item in plan["assignments"]
        if item["day_index"] == 0 and item["meal_role"] == "breakfast"
    )
    replacement_id = next(iter(breakfast_ids - {assignment["recipe_id"]}))

    suggestions = client.get(
        f"/api/weekly-plans/{plan['id']}/assignments/"
        f"{assignment['id']}/replacements"
    )

    assert suggestions.status_code == 200
    assert suggestions.json() == [
        {
            "recipe_id": replacement_id,
            "recipe_title": "Frühstück B",
            "daily_nutrition": plan["daily_nutrition"][0],
        }
    ]

    replaced = client.patch(
        f"/api/weekly-plans/{plan['id']}/assignments/{assignment['id']}",
        json={"recipe_id": replacement_id},
    )

    assert replaced.status_code == 200
    updated_assignment = next(
        item
        for item in replaced.json()["assignments"]
        if item["id"] == assignment["id"]
    )
    assert updated_assignment["recipe_id"] == replacement_id
    assert updated_assignment["portion_number"] is None
    assert client.get(f"/api/weekly-plans/{plan['id']}").json() == replaced.json()


def test_invalid_meal_replacement_is_rejected(client: TestClient) -> None:
    create_complete_recipe_set(client)
    plan = client.post("/api/weekly-plans/generate", json=plan_payload()).json()
    assignment = plan["assignments"][0]

    response = client.patch(
        f"/api/weekly-plans/{plan['id']}/assignments/{assignment['id']}",
        json={"recipe_id": assignment["recipe_id"]},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Dieses Rezept ist für diese Mahlzeit kein gültiger Ersatz"
    )


def test_generation_optimizes_targets_in_documented_priority_order(
    client: TestClient,
) -> None:
    low_id = create_nutrition_food(client, "Wenig Protein", 100, 10, 10, 1)
    high_id = create_nutrition_food(client, "Viel Protein", 600, 60, 10, 1)
    low_recipe = create_recipe(
        client, "Leichte Mahlzeit", 1, ["breakfast", "lunch", "dinner"], low_id
    )
    high_recipe = create_recipe(
        client, "Proteinmahlzeit", 1, ["breakfast", "lunch", "dinner"], high_id
    )
    payload = plan_payload()
    payload.update(
        {
            "snacks_per_day": 0,
            "calories_maximum_kcal": 1000,
            "protein_minimum_g": 150,
            "carbohydrates_target_g": 30,
            "fat_maximum_g": 10,
        }
    )

    first = client.post("/api/weekly-plans/generate", json=payload)
    assert first.status_code == 201
    assert {item["recipe_id"] for item in first.json()["assignments"]} == {
        high_recipe
    }
    assert low_recipe != high_recipe
    assert first.json()["daily_nutrition"][0] == {
        "date": "2026-09-07",
        "day_index": 0,
        "calories_kcal": 1800.0,
        "protein_g": 180.0,
        "carbohydrates_g": 30.0,
        "fat_g": 3.0,
        "calories_over_kcal": 800.0,
        "protein_shortfall_g": 0.0,
        "carbohydrates_difference_g": 0.0,
        "fat_over_g": 0.0,
    }

    payload["replace_existing"] = True
    repeated = client.post("/api/weekly-plans/generate", json=payload)
    assert [item["recipe_id"] for item in repeated.json()["assignments"]] == [
        item["recipe_id"] for item in first.json()["assignments"]
    ]


def test_generation_avoids_duplicate_recipes_within_a_day(
    client: TestClient,
) -> None:
    food_id = create_food(client)
    recipe_ids = {
        create_recipe(
            client,
            f"Gleichwertige Mahlzeit {number}",
            1,
            ["breakfast", "lunch", "dinner"],
            food_id,
        )
        for number in range(1, 4)
    }
    payload = plan_payload()
    payload["snacks_per_day"] = 0

    response = client.post("/api/weekly-plans/generate", json=payload)

    assert response.status_code == 201
    for day_index in range(7):
        daily_recipe_ids = {
            item["recipe_id"]
            for item in response.json()["assignments"]
            if item["day_index"] == day_index
        }
        assert daily_recipe_ids == recipe_ids


def test_generation_rotates_equally_suitable_single_recipes(
    client: TestClient,
) -> None:
    food_id = create_food(client)
    breakfast_ids = {
        create_recipe(client, title, 1, ["breakfast"], food_id)
        for title in ("Frühstück A", "Frühstück B")
    }
    create_recipe(client, "Mittagessen", 1, ["lunch"], food_id)
    create_recipe(client, "Abendessen", 1, ["dinner"], food_id)
    payload = plan_payload()
    payload["snacks_per_day"] = 0

    response = client.post("/api/weekly-plans/generate", json=payload)

    assert response.status_code == 201
    breakfasts = [
        item["recipe_id"]
        for item in response.json()["assignments"]
        if item["meal_role"] == "breakfast"
    ]
    assert set(breakfasts) == breakfast_ids
    assert abs(breakfasts.count(min(breakfast_ids)) - breakfasts.count(max(breakfast_ids))) == 1


def create_complete_recipe_set(client: TestClient) -> None:
    food_id = create_food(client)
    create_recipe(client, "Frühstück", 1, ["breakfast"], food_id)
    create_recipe(client, "Hauptgericht", 1, ["lunch", "dinner"], food_id)
    create_recipe(client, "Snack", 1, ["snack"], food_id)


def create_food(client: TestClient) -> int:
    return create_nutrition_food(client, "Testlebensmittel", 100, 10, 10, 1)


def create_nutrition_food(
    client: TestClient,
    name: str,
    calories: float,
    protein: float,
    carbohydrates: float,
    fat: float,
) -> int:
    response = client.post(
        "/api/foods",
        json={
            "name": name,
            "base_unit": "g",
            "category": "other",
            "calories_kcal": calories,
            "protein_g": protein,
            "carbohydrates_g": carbohydrates,
            "fat_g": fat,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_recipe(
    client: TestClient,
    title: str,
    servings: int,
    roles: list[str],
    food_id: int,
) -> int:
    response = client.post(
        "/api/recipes",
        json={
            "title": title,
            "servings": servings,
            "meal_roles": roles,
            "ingredients": [{"food_id": food_id, "amount": 100 * servings}],
            "instructions": ["Zubereiten."],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def plan_payload() -> dict[str, object]:
    return {
        "start_date": "2026-09-07",
        "snacks_per_day": 1,
        "calories_maximum_kcal": 2500,
        "protein_minimum_g": 180,
        "carbohydrates_target_g": 250,
        "fat_maximum_g": 80,
        "replace_existing": False,
    }
