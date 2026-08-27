import httpx2
import pytest

from preppilot_api.themealdb import (
    MalformedMealResponseError,
    MealNotFoundError,
    TheMealDbClient,
)


def test_get_recipe_combines_numbered_ingredients_and_measures() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/json/v1/test-key/lookup.php"
        assert request.url.params["i"] == "52850"
        return httpx2.Response(
            200,
            json={
                "meals": [
                    {
                        "idMeal": "52850",
                        "strMeal": " Chicken Couscous ",
                        "strCategory": "Chicken",
                        "strArea": "Moroccan",
                        "strInstructions": " Cook everything. ",
                        "strSource": " https://example.com/original ",
                        "strIngredient1": " Olive Oil ",
                        "strMeasure1": " 1 tbsp ",
                        "strIngredient2": "Chicken Breast",
                        "strMeasure2": "200g",
                        "strIngredient3": "",
                        "strMeasure3": "",
                        "strIngredient20": None,
                        "strMeasure20": None,
                    }
                ]
            },
        )

    http_client = httpx2.Client(transport=httpx2.MockTransport(handler))
    client = TheMealDbClient("test-key", http_client=http_client)

    recipe = client.get_recipe("52850")

    assert recipe.source_id == "52850"
    assert recipe.name == "Chicken Couscous"
    assert recipe.category == "Chicken"
    assert recipe.area == "Moroccan"
    assert recipe.instructions == "Cook everything."
    assert recipe.original_source_url == "https://example.com/original"
    assert [(item.name, item.measure) for item in recipe.ingredients] == [
        ("Olive Oil", "1 tbsp"),
        ("Chicken Breast", "200g"),
    ]


def test_get_recipe_reports_missing_meal() -> None:
    http_client = httpx2.Client(
        transport=httpx2.MockTransport(
            lambda _: httpx2.Response(200, json={"meals": None})
        )
    )
    client = TheMealDbClient("test-key", http_client=http_client)

    with pytest.raises(MealNotFoundError):
        client.get_recipe("unknown")


def test_get_recipe_rejects_measure_without_ingredient() -> None:
    http_client = httpx2.Client(
        transport=httpx2.MockTransport(
            lambda _: httpx2.Response(
                200,
                json={
                    "meals": [
                        {
                            "idMeal": "52850",
                            "strMeal": "Chicken Couscous",
                            "strInstructions": "Cook it.",
                            "strIngredient1": "",
                            "strMeasure1": "200g",
                        }
                    ]
                },
            )
        )
    )
    client = TheMealDbClient("test-key", http_client=http_client)

    with pytest.raises(MalformedMealResponseError):
        client.get_recipe("52850")
