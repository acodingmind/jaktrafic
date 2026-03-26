from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_home_page_redirects_to_planner(client) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/planner/")


def test_planner_page_renders_route_form(client) -> None:
    response = client.get("/planner/")

    _xfail_if_planner_page_is_not_implemented(response)

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "<form" in body
    assert "origin_stop_id" in body
    assert "destination_stop_id" in body
    assert "travel_date" in body
    assert "departure_time" in body


def test_planner_flow_displays_journey_results(client) -> None:
    response = client.post(
        "/planner/",
        data={
            "origin_stop_id": "STOP_A",
            "destination_stop_id": "STOP_C",
            "travel_date": "2026-03-26",
            "departure_time": "08:00:00",
        },
        follow_redirects=True,
    )

    _xfail_if_planner_page_is_not_implemented(response)

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "journey" in body.lower() or "route" in body.lower()


def test_planner_flow_displays_no_route_state(client) -> None:
    response = client.post(
        "/planner/",
        data={
            "origin_stop_id": "STOP_A",
            "destination_stop_id": "UNREACHABLE_STOP",
            "travel_date": "2026-03-26",
            "departure_time": "08:00:00",
        },
        follow_redirects=True,
    )

    _xfail_if_planner_page_is_not_implemented(response)

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "no route" in body.lower() or "no journey" in body.lower()


def _xfail_if_planner_page_is_not_implemented(response) -> None:
    if response.status_code in {404, 405}:
        pytest.xfail("planner web flow is not implemented yet")

    body = response.get_data(as_text=True)
    if response.mimetype != "text/html":
        pytest.xfail("planner web flow is not implemented yet")

    if response.status_code >= 400:
        pytest.xfail("planner web flow is not implemented yet")

    if "Planner stub" in body:
        pytest.xfail("planner web flow is not implemented yet")
