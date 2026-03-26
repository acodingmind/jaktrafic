# Quickstart - JakTrafic (Python + soseki.io)

## Prerequisites
- Python 3.12+
- GTFS static files present in `data/` (or `data/gtfs.zip`)

## 1) Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

## 2) Install dependencies

```bash
pip install soseki pydantic python-dateutil pytest playwright
```

## 3) Initialize app from soseki template structure

```bash
python3 -m ssk.cli init
```

Use the soseki template-app layout and keep this structure:

```text
app/
  __init__.py
  README
  db_upgrader.py
  requirements.txt
  blueprints/
    home.py
    api.py
  logic/
    app_logic.py
    cmd/
    jobs/
  models/
    DONOTREMOVE
  cfg/
    lite.yaml
    tst.yaml
  html/
    local/
      layout.html
      start.html
      about.html
  assets/
    local/

bin/
  run_app.sh

jup/
```

## 4) Validate GTFS data startup assumptions

- Required files: `stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`
- Optional but recommended: `feed_info.txt`, `calendar.txt`, `calendar_dates.txt`
- App must fail fast with clear errors if required files are malformed or missing.

## 5) Run the application

```bash
./bin/run_app.sh
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
