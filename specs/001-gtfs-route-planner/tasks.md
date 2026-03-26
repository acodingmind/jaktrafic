# Tasks: JakTrafic - GTFS Route Planner Web Application

**Input**: Design documents from `/specs/001-gtfs-route-planner/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize Python + soseki template-app foundation and baseline tooling.

- [x] T001 Create soseki Blanco app directory skeleton via `python3 -m ssk.cli init`, including app/__init__.py, app/blueprints/, app/logic/cmd/, app/logic/jobs/, app/models/, app/html/local/, app/assets/local/, app/cfg/lite.yaml, app/requirements.txt, bin/run_app.sh, and jup/
- [x] T002 Create Python project metadata and dependencies in pyproject.toml
- [x] T003 [P] Add environment and runtime configuration scaffolding in app/cfg/lite.yaml and .env.example
- [x] T004 [P] Add initial app bootstrap and blueprint registration stubs in app/__init__.py and app/blueprints/
- [x] T005 [P] Configure test runners and baseline test packages in tests/unit/, tests/integration/, tests/contract/, and pytest.ini

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core GTFS ingestion, validation, privacy-safe logging, and shared infrastructure required by all stories.

**⚠️ CRITICAL**: No user story work should begin before this phase is complete.

- [x] T006 Implement GTFS source discovery (directory and zip support) in app/logic/gtfs_loader.py
- [x] T007 [P] Define core domain entities and typed DTOs in app/models/entities.py
- [x] T008 Implement GTFS parser and in-memory indexes for stops/routes/trips/stop_times in app/logic/gtfs_loader.py
- [x] T009 Implement service-calendar date filtering logic from calendar/calendar_dates in app/logic/service_calendar.py
- [x] T010 Implement feed validity-window parsing and startup-state evaluation in app/logic/feed_status.py
- [x] T011 Implement shared request validators (date/time, distinct stops, required params) in app/logic/validators.py
- [ ] T012 Implement privacy-preserving logging and error mapping middleware in app/__init__.py and app/logic/logging.py
- [ ] T013 Implement API blueprint scaffold and OpenAPI exposure wiring in app/blueprints/api.py and app/__init__.py
- [ ] T014 Create accessible base template and shared styles in app/html/local/base.html and app/assets/local/css/app.css
- [ ] T049 [P] Add unit tests for GTFS loader: source discovery (zip vs directory), required-field validation, and malformed-file rejection in tests/unit/test_gtfs_loader.py
- [ ] T050 [P] Add integration tests for GTFS feed ingestion boundary behavior: malformed rows, missing required fields, calendar edge cases, and zip/directory switching in tests/integration/test_gtfs_ingestion.py

**Checkpoint**: Foundation complete; user stories can be implemented.

---

## Phase 3: User Story 1 - Plan a Route Between Two Stops (Priority: P1) 🎯 MVP

**Goal**: Deliver end-to-end journey planning from origin to destination using static GTFS data.

**Independent Test**: Submit origin/destination/date/time and verify route options (or explicit no-route message) with keyboard-only usability.

### Tests for User Story 1

- [ ] T015 [P] [US1] Add unit tests for earliest-arrival routing and transfer logic in tests/unit/test_route_planner.py
- [ ] T016 [P] [US1] Add integration tests for POST /api/v1/routes/plan in tests/integration/test_api_routes_plan.py
- [ ] T017 [P] [US1] Add web-flow integration tests for planner form and result states in tests/integration/test_web_planner_flow.py

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement stop-name search/disambiguation service in app/logic/stop_search.py
- [ ] T019 [US1] Implement route-planning engine using GTFS indexes in app/logic/route_planner.py
- [ ] T020 [US1] Implement planner web blueprint and form handling in app/blueprints/planner.py
- [ ] T021 [US1] Implement route-plan REST endpoint contract mapping in app/blueprints/api.py
- [ ] T022 [US1] Build planner UI and result rendering in app/html/local/planner.html
- [ ] T053 [US1] Add non-color route and alert differentiation (text labels or patterns) in app/html/local/planner.html and app/html/local/departures.html
- [ ] T023 [US1] Implement no-route and same-origin validation messages in app/logic/validators.py and app/html/local/planner.html
- [ ] T024 [US1] Implement default current date/time behavior in app/blueprints/planner.py and app/html/local/planner.html
- [ ] T025 [US1] Add keyboard/focus and aria-live result semantics in app/html/local/planner.html
- [ ] T026 [US1] Register planner blueprint in app/__init__.py

**Checkpoint**: User Story 1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - View Departures for a Stop (Priority: P2)

**Goal**: Provide stop-level departure board for selected date without requiring destination input.

**Independent Test**: Select a stop and date; verify departures list or explicit no-departures message.

### Tests for User Story 2

- [ ] T027 [P] [US2] Add unit tests for departures filtering/sorting in tests/unit/test_departures_service.py
- [ ] T028 [P] [US2] Add integration tests for GET /api/v1/departures in tests/integration/test_api_departures.py
- [ ] T029 [P] [US2] Add web-flow integration tests for departures page in tests/integration/test_web_departures_flow.py

### Implementation for User Story 2

- [ ] T030 [US2] Implement departures computation service in app/logic/departures_service.py
- [ ] T031 [US2] Implement departures web blueprint in app/blueprints/departures.py
- [ ] T032 [US2] Implement departures REST endpoint in app/blueprints/api.py
- [ ] T033 [US2] Build departures board template in app/html/local/departures.html
- [ ] T034 [US2] Add semantic table/list and screen-reader reading order for departures in app/html/local/departures.html
- [ ] T035 [US2] Register departures blueprint in app/__init__.py

**Checkpoint**: User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Data Freshness Transparency (Priority: P3)

**Goal**: Surface GTFS feed validity warnings to users and operators when query/startup dates are outside feed window.

**Independent Test**: Use out-of-window date and verify warning appears in planner results and feed status endpoint/view.

### Tests for User Story 3

- [ ] T036 [P] [US3] Add unit tests for feed-window validation states in tests/unit/test_feed_status.py
- [ ] T037 [P] [US3] Add integration tests for GET /api/v1/feed/status in tests/integration/test_api_feed_status.py
- [ ] T038 [P] [US3] Add integration tests for planner freshness-warning behavior in tests/integration/test_freshness_warning.py

### Implementation for User Story 3

- [ ] T039 [US3] Implement feed status service and warning message formatter in app/logic/feed_status.py
- [ ] T040 [US3] Implement feed status REST endpoint in app/blueprints/api.py
- [ ] T041 [US3] Integrate per-request freshness warning into planner responses in app/blueprints/planner.py and app/blueprints/api.py
- [ ] T042 [US3] Add visible warning banner component to base/planner templates in app/html/local/base.html and app/html/local/planner.html
- [ ] T043 [US3] Add screen-reader announcement semantics for warnings in app/html/local/planner.html

**Checkpoint**: All user stories are functional and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Harden contracts, performance, documentation, and release readiness.

- [ ] T044 [P] Add OpenAPI contract conformance tests against contracts/openapi.yaml in tests/contract/test_openapi_contract.py
- [ ] T045 [P] Add route-query performance smoke tests (p95 target check; baseline: ≤50 concurrent users, single metropolitan feed) in tests/integration/test_route_performance.py
- [ ] T046 [P] Add accessibility regression checks for planner/departures flows in tests/integration/test_web_accessibility.py
- [ ] T054 [P] Add accessibility checks verifying color is not the sole differentiator for route or alert states in tests/integration/test_web_accessibility.py
- [ ] T047 Update developer runbook and usage docs in README.md and specs/001-gtfs-route-planner/quickstart.md
- [ ] T048 Prepare CI test workflow for unit/integration/contract gates in .github/workflows/ci.yml
- [ ] T051 [P] Enforce FR-017 no-third-party-tracking: add automated assertions verifying no external scripts or tracking pixels load without explicit opt-in consent in tests/contract/test_no_tracking.py
- [ ] T052 [P] Add cross-browser compatibility validation for SC-007 (Chrome, Firefox, Safari, Edge last 2 stable; iOS 15+; Android 9+) in tests/integration/test_cross_browser.py

---

## Dependencies & Execution Order

1. Phase 1 (Setup) must complete before Phase 2.
2. Phase 2 (Foundational) blocks all user stories.
3. User Story execution order:
   - US1 (P1) first for MVP delivery.
   - US2 can start after Phase 2 and can run in parallel with late US1 hardening.
   - US3 depends on foundational feed status work and planner flow integration from US1.
4. Polish phase runs after desired stories are complete.

## Parallel Execution Opportunities

### US1
- Run T015, T016, T017 in parallel (different test files).
- Run T018 in parallel with test work before T019 consumes it.

### US2
- Run T027, T028, T029 in parallel.
- T033 and T034 can run in parallel once T031 blueprint contract is stable.

### US3
- Run T036, T037, T038 in parallel.
- T042 and T043 can run in parallel after T041 warning payload contract is defined.

### Cross-Story
- After Phase 2, US2 test implementation can begin while US1 UI polishing is finishing.

## Implementation Strategy

### MVP First (Recommended)
1. Complete Phase 1 and Phase 2.
2. Deliver US1 end-to-end (T015-T026).
3. Validate MVP against US1 independent test criteria.

### Incremental Delivery
1. Add US2 departures board (T027-T035) as release increment 2.
2. Add US3 freshness transparency (T036-T043) as release increment 3.
3. Complete polish tasks (T044-T048) before production release.
