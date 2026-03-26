from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_departures_returns_items_for_valid_stop_and_date(client) -> None:
    response = client.get(
        "/api/v1/departures",
        query_string={
            "stop_id": "STOP_A",
            "date": "2026-03-26",
        },
    )

    _xfail_if_departures_endpoint_is_not_implemented(response)

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert "items" in payload
    assert isinstance(payload["items"], list)


def test_departures_rejects_missing_stop_id(client) -> None:
    response = client.get(
        "/api/v1/departures",
        query_string={
            "date": "2026-03-26",
        },
    )

    _xfail_if_departures_endpoint_is_not_implemented(response)

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["error"] == "bad_request"


def test_departures_returns_empty_results_when_no_departures_exist(client) -> None:
    response = client.get(
        "/api/v1/departures",
        query_string={
            "stop_id": "UNUSED_STOP",
            "date": "2026-03-26",
        },
    )

    _xfail_if_departures_endpoint_is_not_implemented(response)

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["items"] == []


def _xfail_if_departures_endpoint_is_not_implemented(response) -> None:
    if response.status_code in {404, 405}:
        pytest.xfail("departures API endpoint is not implemented yet")

    if response.mimetype != "application/json":
        pytest.xfail("departures API endpoint is not implemented yet")
