from fastapi.testclient import TestClient

from preppilot_api.main import app
from preppilot_api.models import Base


def test_v5_foundation_has_no_domain_tables() -> None:
    assert not Base.metadata.tables


def test_v5_foundation_exposes_no_domain_endpoints() -> None:
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    assert set(schema["paths"]) == {"/api/health"}
