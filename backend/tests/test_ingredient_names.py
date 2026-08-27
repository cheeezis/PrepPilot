import pytest

from preppilot_api.ingredient_names import normalize_ingredient_name


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("  Chicken   Breast ", "chicken breast"),
        ("\tOLIVE OIL\n", "olive oil"),
        (
            "\uff2f\uff2c\uff29\uff36\uff25 \uff2f\uff29\uff2c",
            "olive oil",
        ),
        ("Tomatoes, chopped", "tomatoes, chopped"),
    ],
)
def test_normalizes_only_safe_text_variations(name: str, expected: str) -> None:
    assert normalize_ingredient_name(name) == expected


def test_rejects_blank_ingredient_names() -> None:
    with pytest.raises(ValueError, match="must not be blank"):
        normalize_ingredient_name("  \t")
