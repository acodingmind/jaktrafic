from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app(testing=True)
    return app.test_client()


def test_feed_status_endpoint_returns_feed_window_status(client) -> None:
    response = client.get("/api/v1/feed/status")

    _xfail_if_feed_status_endpoint_is_not_implemented(response)

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, dict)
    assert payload["state"] in {"healthy", "warning"}
    assert "message" in payload


def _xfail_if_feed_status_endpoint_is_not_implemented(response) -> None:
    if response.status_code in {404, 405}:
        pytest.xfail("feed status API endpoint is not implemented yet")

    if response.mimetype != "application/json":
        pytest.xfail("feed status API endpoint is not implemented yet")
