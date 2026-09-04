from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from preppilot_api.database import get_session


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]


app = FastAPI(title="PrepPilot API", version="0.5.0")
DatabaseSession = Annotated[Session, Depends(get_session)]


def check_database(session: Session) -> None:
    session.execute(text("SELECT 1"))


@app.get("/api/health", tags=["system"], response_model=HealthResponse)
def health(response: Response, session: DatabaseSession) -> HealthResponse:
    try:
        check_database(session)
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="error", database="unavailable")
    return HealthResponse(status="ok", database="ok")
