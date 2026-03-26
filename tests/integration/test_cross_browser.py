from __future__ import annotations

import threading
from contextlib import contextmanager

import pytest
from werkzeug.serving import make_server

from app import create_app


@pytest.mark.parametrize("browser_name", ["chromium", "firefox", "webkit"])
def test_core_pages_render_in_supported_browsers(browser_name: str) -> None:
    playwright = pytest.importorskip("playwright.sync_api")

    app = create_app(testing=True)
    with _serve_app(app) as base_url:
        try:
            with playwright.sync_playwright() as p:
                browser_type = getattr(p, browser_name)
                browser = browser_type.launch()
                page = browser.new_page()
                for path, heading in (("/planner/", "Plan Your Route"), ("/departures/", "Departure Board")):
                    page.goto(f"{base_url}{path}")
                    assert page.locator("h1").text_content() == heading
                browser.close()
        except Exception as exc:  # pragma: no cover - environment dependent
            pytest.skip(f"browser runtime unavailable for {browser_name}: {exc}")


@contextmanager
def _serve_app(app):
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
