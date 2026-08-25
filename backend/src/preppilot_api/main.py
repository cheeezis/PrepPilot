from typing import Literal

from fastapi import FastAPI, Response, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from preppilot_api.database import check_database_connection


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]


app = FastAPI(title="PrepPilot API", version="0.1.0")


@app.get("/api/health", tags=["system"], response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    try:
        check_database_connection()
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="error", database="unavailable")

    return HealthResponse(status="ok", database="ok")
