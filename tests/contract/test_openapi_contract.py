from __future__ import annotations

from pathlib import Path

import yaml

from app import create_app


def test_live_openapi_matches_checked_in_contract() -> None:
    app = create_app(testing=True)
    client = app.test_client()

    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    live_contract = response.get_json()
    checked_in_contract = yaml.safe_load(
        Path("specs/001-gtfs-route-planner/contracts/openapi.yaml").read_text(encoding="utf-8")
    )

    assert live_contract["openapi"] == checked_in_contract["openapi"]
    assert live_contract["info"] == checked_in_contract["info"]
    assert set(live_contract["paths"]) == set(checked_in_contract["paths"])

    for path_name, operations in checked_in_contract["paths"].items():
        assert set(live_contract["paths"][path_name]) == set(operations)


def test_openapi_contract_declares_core_schemas() -> None:
    checked_in_contract = yaml.safe_load(
        Path("specs/001-gtfs-route-planner/contracts/openapi.yaml").read_text(encoding="utf-8")
    )

    schemas = checked_in_contract["components"]["schemas"]
    assert "RoutePlanRequest" in schemas
    assert "RoutePlanResponse" in schemas
    assert "DeparturesResponse" in schemas
    assert "FeedStatus" in schemas
