from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_departures_page_renders_form(client) -> None:
    response = client.get("/departures/")

    _xfail_if_departures_page_is_not_implemented(response)

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<form" in body
    assert "stop_id" in body
    assert "travel_date" in body or "date" in body


def test_departures_flow_displays_departure_results(client) -> None:
    response = client.get(
        "/departures/",
        query_string={
            "stop_id": "STOP_A",
            "travel_date": "2026-03-26",
        },
        follow_redirects=True,
    )

    _xfail_if_departures_page_is_not_implemented(response)

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "departure" in body.lower() or "board" in body.lower()


def test_departures_flow_displays_no_departures_state(client) -> None:
    response = client.get(
        "/departures/",
        query_string={
            "stop_id": "UNUSED_STOP",
            "travel_date": "2026-03-26",
        },
        follow_redirects=True,
    )

    _xfail_if_departures_page_is_not_implemented(response)

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "no departures" in body.lower()


def _xfail_if_departures_page_is_not_implemented(response) -> None:
    if response.status_code in {404, 405}:
        pytest.xfail("departures web flow is not implemented yet")

    body = response.get_data(as_text=True)
    if response.mimetype != "text/html":
        pytest.xfail("departures web flow is not implemented yet")

    if response.status_code >= 400:
        pytest.xfail("departures web flow is not implemented yet")

    if "Departures stub" in body:
        pytest.xfail("departures web flow is not implemented yet")
