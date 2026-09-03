from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.exc import SQLAlchemyError

import preppilot_api.main as main_module


def test_health_reports_ready(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(main_module, "load_recipes", lambda session: (object(),))
    with TestClient(main_module.app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "recipes": "ok"}


def test_health_distinguishes_database_from_empty_recipes(
    monkeypatch: MonkeyPatch,
) -> None:
    def raise_database_error(session: object) -> None:
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(main_module, "load_recipes", raise_database_error)
    with TestClient(main_module.app) as client:
        response = client.get("/api/health")
    assert response.status_code == 503
    assert response.json()["database"] == "unavailable"

    monkeypatch.setattr(main_module, "load_recipes", lambda session: ())
    with TestClient(main_module.app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "recipes": "empty",
    }
