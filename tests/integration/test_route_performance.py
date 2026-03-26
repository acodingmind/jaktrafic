from __future__ import annotations

from statistics import quantiles
from time import perf_counter

from app import create_app


def test_route_plan_api_performance_smoke() -> None:
    app = create_app(testing=True)
    client = app.test_client()

    durations: list[float] = []
    for _ in range(20):
        started_at = perf_counter()
        response = client.post(
            "/api/v1/routes/plan",
            json={
                "origin_stop_id": "STOP_A",
                "destination_stop_id": "STOP_C",
                "travel_date": "2026-03-26",
                "departure_time": "08:00:00",
            },
        )
        durations.append(perf_counter() - started_at)
        assert response.status_code == 200

    p95 = quantiles(durations, n=20)[18]
    assert p95 < 0.5
    assert max(durations) < 1.0
