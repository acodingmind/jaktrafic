# JakTrafic

JakTrafic is a server-rendered GTFS route planner and departures board built on soseki.

## Features

- Route planning between stops with transfer-aware journeys
- Departure board lookup for a stop and date
- Feed freshness warnings when the selected date is outside the GTFS validity window
- REST API with OpenAPI contract under `/api/v1`
- Keyboard-first, screen-reader-friendly planner and departures pages

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[test]
./bin/run_app.sh
```

## Test Suite

```bash
pytest
```

Optional browser validation:

```bash
python -m playwright install chromium firefox webkit
pytest tests/integration/test_cross_browser.py
```

## Key Endpoints

- `/planner/`
- `/departures/`
- `/api/v1/routes/plan`
- `/api/v1/departures`
- `/api/v1/feed/status`
- `/api/v1/openapi.yaml`

## Privacy

JakTrafic does not include analytics or tracking scripts by default and does not persist route queries beyond request processing.
