from __future__ import annotations

import re

from app import create_app


TRACKING_PATTERNS = (
    r"googletagmanager",
    r"google-analytics",
    r"gtag/js",
    r"segment\\.com",
    r"plausible",
    r"mixpanel",
    r"hotjar",
    r"facebook\\.net",
    r"doubleclick",
)


def test_pages_do_not_load_tracking_scripts_or_pixels() -> None:
    app = create_app(testing=True)
    client = app.test_client()

    for path in ("/planner/", "/departures/"):
        response = client.get(path)
        assert response.status_code == 200
        body = response.get_data(as_text=True).lower()

        for pattern in TRACKING_PATTERNS:
            assert re.search(pattern, body) is None

        assert "<iframe" not in body
        assert "tracking pixel" not in body
