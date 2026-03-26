# Quickstart - JakTrafic (Python + soseki.io)

## Prerequisites
- Python 3.12+
- GTFS static files present in `data/` (or `data/gtfs.zip`)

## 1) Create and activate virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

## 2) Install dependencies

```bash
pip install soseki pydantic python-dateutil pytest playwright
```

## 3) Initialize app from soseki template structure

Use the soseki template-app layout and keep this structure:

```text
app/
  main.py
  blueprints/
  logic/
  models/
  cfg/
    lite.yaml
  html/
    local/
  assets/
    local/
  templates -> html/local
  static -> assets/local
```

## 4) Validate GTFS data startup assumptions

- Required files: `stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`
- Optional but recommended: `feed_info.txt`, `calendar.txt`, `calendar_dates.txt`
- App must fail fast with clear errors if required files are malformed or missing.

## 5) Run the application

```bash
python -m app.main
```

Expected:
- Web UI available for route planning and stop departures.
- REST API served under `/api/v1`.
- Feed-status endpoint returns GTFS validity window state.

## 6) Run tests

```bash
pytest
```

Optional E2E browser checks:

```bash
playwright install
pytest tests/integration/test_web_planner_flow.py tests/integration/test_web_departures_flow.py
```

## 7) Manual sanity checks

1. Search stops by partial name and confirm disambiguation list appears.
2. Plan route with different origin/destination and verify journey details.
3. Plan route for out-of-feed date and verify visible freshness warning.
4. Open departures view for a stop/date and verify schedule list or no-service message.
5. Navigate planner and departures pages using keyboard only.
