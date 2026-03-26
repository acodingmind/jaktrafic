# Phase 0 Research - JakTrafic GTFS Route Planner

## Decision 1: Application Framework
- Decision: Use soseki.io template app as the canonical project structure and runtime framework.
- Rationale: Constitution mandates soseki.io as the sole framework. Using template defaults minimizes bootstrapping risk and supports Principle IV (Simplicity & YAGNI).
- Alternatives considered: FastAPI + Jinja, Django, Flask. Rejected due to constitutional mismatch.

## Decision 2: Data Source Strategy
- Decision: Load static GTFS data from `data/` at startup; build in-memory indexes for stop lookup, stop_times traversal, and calendar/date filtering.
- Rationale: Meets static-only requirement and improves request latency without introducing a database.
- Alternatives considered: SQL persistence of GTFS tables, per-request CSV parsing. Rejected because unnecessary complexity or poor latency.

## Decision 3: Route Computation Approach
- Decision: Implement earliest-arrival journey search over GTFS trips with transfer-aware expansion and bounded candidate exploration.
- Rationale: Satisfies journey-planning requirements while remaining implementable in v1 complexity budget.
- Alternatives considered: RAPTOR/CSA full implementations and graph DB routing. Rejected as over-engineered for initial scope.

## Decision 4: Accessibility Implementation
- Decision: Build server-rendered templates with semantic landmarks, explicit form labels, keyboard-first controls, and aria-live regions for warnings/results.
- Rationale: Directly enforces WCAG 2.1 AA requirements from constitution and spec FR-011..FR-014.
- Alternatives considered: Heavy SPA UI with custom widgets. Rejected due to higher accessibility regression risk.

## Decision 5: API Contract Shape
- Decision: Expose REST endpoints under `/api/v1` for stop search, route planning, departures, and feed status; define OpenAPI contract in `contracts/openapi.yaml`.
- Rationale: Constitution requires REST + OpenAPI and specification FR-018 requires explicit contract coverage.
- Alternatives considered: GraphQL-only API, undocumented internal endpoints. Rejected due to constitution non-compliance.

## Decision 6: Privacy and Logging
- Decision: Treat planner/departure requests as stateless, avoid storing query payloads or user identifiers, and redact IP/user-agent from business logs.
- Rationale: Required by constitution Principle III and FR-015..FR-017.
- Alternatives considered: Full request body logging for analytics. Rejected due to privacy violation.

## Decision 7: Testing Pyramid
- Decision: Use pytest for unit/integration + contract checks against OpenAPI and Playwright for end-to-end accessibility-critical journeys.
- Rationale: Aligns with constitution testing requirements and keeps stack Python-first.
- Alternatives considered: Unit-tests only. Rejected because route correctness and accessibility require integration/E2E validation.
