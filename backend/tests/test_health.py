from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy.exc import SQLAlchemyError

import preppilot_api.main as main_module
from preppilot_api.catalog_repository import CatalogUnavailableError


def test_health_reports_ready(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(
        main_module,
        "load_catalog_from_database",
        lambda session: object(),
    )

    with TestClient(main_module.app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "ok",
        "catalog": "ok",
    }


def test_health_reports_unavailable(monkeypatch: MonkeyPatch) -> None:
    def raise_database_error(session: object) -> None:
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(
        main_module,
        "load_catalog_from_database",
        raise_database_error,
    )

    with TestClient(main_module.app) as client:
        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "database": "unavailable",
        "catalog": "unavailable",
    }


def test_health_reports_empty_catalog(monkeypatch: MonkeyPatch) -> None:
    def raise_catalog_error(session: object) -> None:
        raise CatalogUnavailableError("catalog unavailable")

    monkeypatch.setattr(
        main_module,
        "load_catalog_from_database",
        raise_catalog_error,
    )

    with TestClient(main_module.app) as client:
        response = client.get("/api/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "error",
        "database": "ok",
        "catalog": "unavailable",
    }
