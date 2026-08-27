import json
from decimal import Decimal

import httpx2

from preppilot_api.food_data_central import FoodDataCentralClient


def test_search_foods_returns_only_small_candidate_objects() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "POST"
        assert request.url.path == "/fdc/v1/foods/search"
        assert request.url.params["api_key"] == "test-key"
        assert json.loads(request.content) == {
            "query": "chicken breast",
            "dataType": ["Foundation", "SR Legacy"],
            "pageSize": 10,
        }
        return httpx2.Response(
            200,
            json={
                "foods": [
                    {
                        "fdcId": 2646170,
                        "description": "Chicken, breast, boneless, skinless, raw",
                        "dataType": "Foundation",
                        "unusedExternalField": "ignored",
                    }
                ]
            },
        )

    http_client = httpx2.Client(transport=httpx2.MockTransport(handler))
    client = FoodDataCentralClient("test-key", http_client=http_client)

    candidates = client.search_foods("chicken breast")

    assert len(candidates) == 1
    assert candidates[0].fdc_id == 2646170
    assert candidates[0].description == "Chicken, breast, boneless, skinless, raw"
    assert candidates[0].data_type == "Foundation"


def test_get_food_extracts_mvp_nutrients_per_100g() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "GET"
        assert request.url.path == "/fdc/v1/food/2646170"
        return httpx2.Response(
            200,
            json={
                "fdcId": 2646170,
                "description": "Chicken, breast, boneless, skinless, raw",
                "dataType": "Foundation",
                "foodNutrients": [
                    _nutrient(1008, "kcal", "120"),
                    _nutrient(1003, "g", "22.5"),
                    _nutrient(1005, "g", "0"),
                    _nutrient(1004, "g", "2.6"),
                ],
                "foodPortions": [
                    {
                        "id": 12345,
                        "amount": 1,
                        "gramWeight": 114,
                        "measureUnit": {"name": "undetermined"},
                        "modifier": "medium (3 inch)",
                    }
                ],
            },
        )

    http_client = httpx2.Client(transport=httpx2.MockTransport(handler))
    client = FoodDataCentralClient("test-key", http_client=http_client)

    food = client.get_food(2646170)

    assert food.fdc_id == 2646170
    assert food.nutrients_per_100g.calories == Decimal("120")
    assert food.nutrients_per_100g.protein == Decimal("22.5")
    assert food.nutrients_per_100g.carbs == Decimal("0")
    assert food.nutrients_per_100g.fat == Decimal("2.6")
    assert len(food.portions) == 1
    assert food.portions[0].source_id == 12345
    assert food.portions[0].amount == Decimal("1")
    assert food.portions[0].gram_weight == Decimal("114")
    assert food.portions[0].unit == "piece"
    assert food.portions[0].modifier == "medium"


def test_get_food_normalizes_half_as_fractional_piece() -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "fdcId": 173941,
                "description": "Apricots, dried",
                "dataType": "SR Legacy",
                "foodNutrients": [],
                "foodPortions": [
                    {
                        "id": 987,
                        "amount": 1,
                        "gramWeight": 3.5,
                        "measureUnit": {"name": "undetermined"},
                        "modifier": "half",
                    }
                ],
            },
        )

    client = FoodDataCentralClient(
        "test-key",
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )

    portion = client.get_food(173941).portions[0]

    assert portion.amount == Decimal("0.5")
    assert portion.gram_weight == Decimal("3.5")
    assert portion.unit == "piece"
    assert portion.modifier is None


def test_get_food_accepts_atwater_energy_when_regular_energy_is_missing() -> None:
    def handler(_: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "fdcId": 123,
                "description": "Example food",
                "dataType": "Foundation",
                "foodNutrients": [_nutrient(2047, "kcal", "98")],
            },
        )

    http_client = httpx2.Client(transport=httpx2.MockTransport(handler))
    client = FoodDataCentralClient("test-key", http_client=http_client)

    food = client.get_food(123)

    assert food.nutrients_per_100g.calories == Decimal("98")


def _nutrient(nutrient_id: int, unit: str, amount: str) -> dict[str, object]:
    return {
        "nutrient": {"id": nutrient_id, "unitName": unit},
        "amount": amount,
    }
