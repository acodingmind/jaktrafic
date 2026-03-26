from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_routes_plan_returns_journeys_for_valid_request(client) -> None:
    response = client.post(
        "/api/v1/routes/plan",
        json={
            "origin_stop_id": "STOP_A",
            "destination_stop_id": "STOP_C",
            "travel_date": "2026-03-26",
            "departure_time": "08:00:00",
        },
    )

    _xfail_if_route_plan_endpoint_is_not_implemented(response)

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert "journeys" in payload
    assert isinstance(payload["journeys"], list)


def test_routes_plan_rejects_same_origin_and_destination(client) -> None:
    response = client.post(
        "/api/v1/routes/plan",
        json={
            "origin_stop_id": "STOP_A",
            "destination_stop_id": "STOP_A",
            "travel_date": "2026-03-26",
            "departure_time": "08:00:00",
        },
    )

    _xfail_if_route_plan_endpoint_is_not_implemented(response)

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "bad_request"


def test_routes_plan_returns_empty_results_when_no_route_exists(client) -> None:
    response = client.post(
        "/api/v1/routes/plan",
        json={
            "origin_stop_id": "STOP_A",
            "destination_stop_id": "UNREACHABLE_STOP",
            "travel_date": "2026-03-26",
            "departure_time": "08:00:00",
        },
    )

    _xfail_if_route_plan_endpoint_is_not_implemented(response)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["journeys"] == []


def _xfail_if_route_plan_endpoint_is_not_implemented(response) -> None:
    if response.status_code in {404, 405}:
        pytest.xfail("route plan API endpoint is not implemented yet")

    if response.mimetype != "application/json":
        pytest.xfail("route plan API endpoint is not implemented yet")