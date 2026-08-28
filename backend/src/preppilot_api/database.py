from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from preppilot_api.config import get_settings

engine = create_engine(
    get_settings().database_url,
    connect_args={"connect_timeout": 3},
    pool_pre_ping=True,
)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
