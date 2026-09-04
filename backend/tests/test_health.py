from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.exc import SQLAlchemyError

import preppilot_api.main as main_module


def test_health_reports_ready(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(main_module, "check_database", lambda session: None)
    with TestClient(main_module.app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_an_unavailable_database(monkeypatch: MonkeyPatch) -> None:
    def raise_database_error(session: object) -> None:
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(main_module, "check_database", raise_database_error)
    with TestClient(main_module.app) as client:
        response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "database": "unavailable",
    }
