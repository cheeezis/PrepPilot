from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PREPPILOT_")

    database_url: str = (
        "postgresql+psycopg://preppilot:preppilot@localhost:5432/preppilot"
    )
    themealdb_api_key: str = "1"
    themealdb_base_url: str = "https://www.themealdb.com/api/json/v1"
    food_data_central_api_key: str = "DEMO_KEY"
    fooddata_central_base_url: str = "https://api.nal.usda.gov/fdc/v1"
    external_request_timeout_seconds: float = 10.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
