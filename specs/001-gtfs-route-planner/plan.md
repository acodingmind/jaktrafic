# Implementation Plan: JakTrafic - GTFS Route Planner Web Application

**Branch**: `001-gtfs-route-planner` | **Date**: 2026-03-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-gtfs-route-planner/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a Python web application on the soseki.io template structure that provides:
1) route planning between stops, 2) stop departure boards, and 3) GTFS feed validity
warnings. The system consumes static GTFS data from `data/` only (no GTFS-Realtime),
preloads validated feed data at startup, and serves REST endpoints plus accessible web
pages for journey search and departures.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: soseki.io framework, pydantic (validation), python-dateutil (time parsing), pytest  
**Storage**: File-based GTFS dataset in `data/`; in-memory indexes (no DB in v1)  
**Testing**: pytest (unit/integration), Playwright (E2E accessibility/user journey checks)  
**Target Platform**: Linux container/server for backend + modern desktop/mobile browsers
**Project Type**: Web application (server-rendered pages + REST API)
**Performance Goals**: Route query <= 2s p95; initial page interactive <= 3s on median 4G
**Load Baseline** (normal load): ≤ 50 concurrent users, single metropolitan GTFS feed (~300k stop_times rows)
**Constraints**: Static GTFS only, WCAG 2.1 AA, no PII query persistence, no IP-linked route logs
**Scale/Scope**: Single metropolitan GTFS feed, public read-only usage, no authentication

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Gate 1 - Routing Accuracy: PASS
  - Plan uses only static GTFS from `data/`.
  - Includes startup and per-request feed validity checks.
- Gate 2 - Accessibility: PASS
  - Includes semantic HTML templates, keyboard-only interactions, and screen-reader support.
- Gate 3 - Privacy by Design: PASS
  - No persisted user locations/queries; logs are request-level without user identifiers.
- Gate 4 - Simplicity & YAGNI: PASS
  - File/in-memory architecture first; no DB, queues, or distributed components in v1.

Post-Phase-1 re-check: PASS (research, data model, and contracts keep all four gates satisfied).

## Project Structure

### Documentation (this feature)

```text
specs/001-gtfs-route-planner/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
app/                              # soseki Blanco application package
├── __init__.py                   # create_app entry point and blueprint registration
├── README
├── db_upgrader.py
├── requirements.txt
├── assets/
│   └── local/                    # static files (CSS, JS) from soseki init
│       ├── global.css
│       └── global.js
├── blueprints/                   # Flask blueprints (soseki convention)
│   ├── home.py                   # default scaffold blueprint
│   ├── api.py                    # default API scaffold; extended for /api/v1
│   ├── planner.py                # planned web routes for route planning UI
│   └── departures.py             # planned web routes for departure board UI
├── cfg/
│   ├── lite.yaml                 # primary YAML application configuration
│   └── tst.yaml                  # scaffolded test profile config
├── html/
│   └── local/                    # local HTML templates copied into runtime templates
│       ├── layout.html
│       ├── start.html
│       ├── about.html
│       ├── planner.html
│       └── departures.html
├── logic/                        # business logic (soseki convention)
│   ├── app_logic.py              # soseki wiring and startup hooks
│   ├── cmd/                      # custom commands
│   ├── jobs/                     # background jobs
│   ├── gtfs_loader.py            # GTFS source discovery, parsing, in-memory indexes
│   ├── service_calendar.py       # calendar/calendar_dates date filtering
│   ├── route_planner.py          # earliest-arrival journey computation
│   ├── departures_service.py     # stop departure board computation
│   ├── feed_status.py            # feed validity-window evaluation
│   ├── logging.py                # privacy-safe request and error logging
│   ├── stop_search.py            # stop name search and disambiguation
│   └── validators.py             # input and feed-window validation
├── models/                       # domain entities (soseki convention)
│   ├── DONOTREMOVE
│   └── entities.py               # Stop, Route, Trip, Journey, Leg, Departure (Pydantic)
├── static/                       # runtime-generated from soseki base + local assets
└── templates/                    # runtime-generated from soseki base + local html

bin/
└── run_app.sh                    # quickstart runner script generated by soseki init

jup/                              # scaffolded notebook/util workspace

data/
└── gtfs.zip or *.txt             # static GTFS feed source (read-only at startup)

tests/
├── unit/
│   ├── test_gtfs_loader.py
│   ├── test_route_planner.py
│   ├── test_departures_service.py
│   └── test_feed_status.py
├── integration/
│   ├── test_gtfs_ingestion.py
│   ├── test_api_routes_plan.py
│   ├── test_api_departures.py
│   ├── test_api_feed_status.py
│   ├── test_web_planner_flow.py
│   ├── test_web_departures_flow.py
│   ├── test_freshness_warning.py
│   ├── test_web_accessibility.py
│   ├── test_route_performance.py
│   └── test_cross_browser.py
└── contract/
    ├── test_openapi_contract.py
    └── test_no_tracking.py
```

**Structure Decision**: Adopt the scaffold produced by the documented soseki
quickstart (`python3 -m ssk.cli init`) as the canonical base layout. `app/__init__.py`
is the application entry point, `bin/run_app.sh` is the generated runner, `html/local/`
and `assets/local/` hold app-specific overrides, and `templates/` plus `static/` are
materialized at runtime by the soseki bootstrap. The source tree above is the concrete
v1 file layout and must stay synchronized with `tasks.md` as implementation details
evolve. This keeps architecture simple, aligns with constitution Principle IV (YAGNI),
and follows the upstream framework setup path exactly.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
