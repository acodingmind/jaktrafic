from __future__ import annotations

from app import create_app


def test_planner_page_has_core_accessibility_landmarks() -> None:
    app = create_app(testing=True)
    client = app.test_client()

    response = client.get("/planner/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="#main-content"' in body
    assert '<main id="main-content"' in body
    assert 'aria-live="polite"' in body
    assert 'label for="origin_stop_id"' in body
    assert 'label for="destination_stop_id"' in body


def test_departures_page_has_core_accessibility_landmarks() -> None:
    app = create_app(testing=True)
    client = app.test_client()

    response = client.get("/departures/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="#main-content"' in body
    assert '<main id="main-content"' in body
    assert 'aria-live="polite"' in body
    assert 'label for="stop_id"' in body


def test_route_and_departure_views_do_not_rely_on_color_only() -> None:
    app = create_app(testing=True)
    client = app.test_client()

    planner_body = client.post(
        "/planner/",
        data={
            "origin_stop_id": "STOP_A",
            "destination_stop_id": "STOP_C",
            "travel_date": "2026-03-26",
            "departure_time": "08:00:00",
        },
    ).get_data(as_text=True)
    departures_body = client.get(
        "/departures/",
        query_string={"stop_id": "STOP_A", "travel_date": "2026-03-26"},
    ).get_data(as_text=True)

    assert "Line " in planner_body
    assert "Line " in departures_body
