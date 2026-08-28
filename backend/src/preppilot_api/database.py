from sqlalchemy import create_engine, text

from preppilot_api.config import get_settings

engine = create_engine(
    get_settings().database_url,
    connect_args={"connect_timeout": 3},
    pool_pre_ping=True,
)


def check_database_connection() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
