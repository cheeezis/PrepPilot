import unicodedata


def normalize_ingredient_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKC", name).casefold()
    normalized = " ".join(normalized.split())
    if not normalized:
        raise ValueError("Ingredient name must not be blank")
    return normalized
