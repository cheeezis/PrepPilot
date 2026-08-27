from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PREPPILOT_")

    database_url: str = (
        "postgresql+psycopg://preppilot:preppilot@localhost:5432/preppilot"
    )
    food_data_central_api_key: str | None = None
    themealdb_api_key: str = "1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
