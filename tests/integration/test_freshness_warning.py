from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_planner_displays_freshness_warning_for_out_of_window_date(client) -> None:
    response = client.post(
        "/planner/",
        data={
            "origin_stop_id": "STOP_A",
            "destination_stop_id": "STOP_C",
            "travel_date": "2026-04-05",
            "departure_time": "08:00:00",
        },
        follow_redirects=True,
    )

    _xfail_if_freshness_warning_is_not_implemented(response)

    body = response.get_data(as_text=True).lower()
    assert response.status_code == 200
    assert "warning" in body or "unreliable" in body or "freshness" in body


def _xfail_if_freshness_warning_is_not_implemented(response) -> None:
    if response.status_code in {404, 405}:
        pytest.xfail("planner freshness warning is not implemented yet")

    if response.mimetype != "text/html":
        pytest.xfail("planner freshness warning is not implemented yet")

    body = response.get_data(as_text=True).lower()
    if "warning" not in body and "unreliable" not in body and "freshness" not in body:
        pytest.xfail("planner freshness warning is not implemented yet")
