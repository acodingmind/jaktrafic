<!--
SYNC IMPACT REPORT
==================
Version change:    2.0.0 → 2.0.1
Bump rationale:    PATCH — Technical Constraints updated to specify soseki.io as the
                   web framework; replaced the generic "React or Next.js" placeholder.
                   Fixed stale "Principle V" reference in Development Workflow.

Principles modified: none
Sections changed:
  - Technical Constraints: Frontend constraint updated to soseki.io framework
  - Development Workflow: corrected stale "Principle V" → "Principle IV" reference

Templates reviewed:
  ✅ .specify/templates/plan-template.md   — no references to update.
  ✅ .specify/templates/spec-template.md   — no references to update.
  ✅ .specify/templates/tasks-template.md  — no references to update.
  ✅ .github/agents/*.agent.md             — no stale references found.

Deferred TODOs: none.
-->

# JakTrafic Constitution

## Core Principles

### I. Routing Accuracy (NON-NEGOTIABLE)

Route suggestions MUST be derived from authoritative GTFS static feed data. Results
MUST correctly reflect the scheduled timetables at the time of the query. Any route
result based on a feed whose validity period has expired MUST be labeled with a
data-freshness warning visible to the user. No route MUST be presented without a
validity-period check confirming the feed covers the requested travel date.

**Rationale**: A single wrong connection or missed departure destroys user trust in a
transit application immediately and irreversibly. Accuracy is the core product promise.

### II. Accessibility (NON-NEGOTIABLE)

All user-facing interfaces MUST meet WCAG 2.1 Level AA as a minimum. Interactive
elements MUST be fully keyboard-navigable. Route and departure information MUST be
compatible with screen readers (semantic HTML, ARIA labels where needed). Color MUST
NOT be the sole visual differentiator for transit lines or alert states — a text label
or pattern MUST accompany every color-coded element.

**Rationale**: Public transit is a public service. Accessibility is both a legal
obligation and an ethical baseline, not an enhancement.

### III. Privacy by Design

User location data MUST NOT be persisted on the server beyond the duration of a single
route-planning request (stateless processing). Route queries MUST NOT be logged against
identifiable user identifiers or IP addresses. Third-party analytics or tracking scripts
MUST NOT be loaded without explicit, informed user consent (opt-in). The minimum
location precision required for routing MUST be used — no sub-meter precision where
city-block precision suffices.

**Rationale**: Travel patterns are sensitive personal data. A transit application that
leaks location history is a surveillance tool by another name.

### IV. Simplicity & YAGNI

Every feature MUST be implemented as the simplest solution that satisfies a documented
user need. Speculative abstractions, premature generalizations, and over-engineered
patterns are prohibited without a written rationale explaining why a simpler approach
was insufficient. Complexity introduced MUST be tracked in the plan's Complexity
Tracking table. Dependencies MUST be justified — each new library or service MUST solve
a problem that cannot be reasonably solved with existing project tools.

**Rationale**: Transit data is already complex. The application layer MUST remain as
simple as possible to keep the system maintainable and the team productive.

## Technical Constraints

- **Framework**: soseki.io is the sole web framework for this project; no framework
  changes are permitted without a constitution amendment.
- **Data Standards**: GTFS static feeds are the sole canonical data source. Proprietary
  feed formats MUST be adapted to GTFS static format before entering the routing layer.
  GTFS-Realtime is out of scope.
- **API Style**: REST with OpenAPI documentation for all backend endpoints.
- **Performance Targets**: Route query response MUST complete in < 2 s (p95 under normal
  load); initial page load MUST complete in < 3 s on a median mobile connection (4G).
- **Browser Support**: Last 2 stable releases of Chrome, Firefox, Safari, and Edge;
  iOS 15+; Android 9+.
- **Testing**: Unit tests MUST cover all routing algorithms and data-feed parsers;
  integration tests MUST cover all GTFS/GTFS-RT connector boundaries; end-to-end tests
  MUST cover the primary route-planning user journey.
- **Feed Validity**: The application MUST validate GTFS feed_info.txt validity dates on
  startup and warn operators when served data is outside its validity window.

## Development Workflow

- **Branching**: Feature branches off `main`; all changes enter via pull request.
- **Review Gate**: Every PR MUST receive at least one peer review before merge.
- **Constitution Check**: Every PR description MUST include a Constitution Check section
  confirming compliance with each of the four Core Principles. A PR that cannot
  demonstrate compliance MUST NOT be merged.
- **Test Gate**: No PR with failing tests may be merged. New routing logic MUST be
  accompanied by tests in the same PR (TDD preferred: tests first, then implementation).
- **CI/CD**: Automated build, lint, and test pipeline MUST run on every PR and on every
  push to `main`. Staging deployment MUST precede every production release.
- **Dependency Review**: New runtime dependencies MUST be documented in the PR with a
  a justification per Principle IV (Simplicity & YAGNI).

## Governance

This constitution supersedes all other project practices and guidelines. In case of
conflict, the constitution prevails.

**Amendment procedure**:
1. Open a proposal (PR or issue) describing the change, its rationale, and the migration
   impact on existing features and templates.
2. Obtain approval from at least two maintainers.
3. Increment `CONSTITUTION_VERSION` per semantic versioning:
   - **MAJOR**: A principle is removed or its non-negotiable rules are redefined in a
     backward-incompatible way.
   - **MINOR**: A new principle or section is added, or guidance is materially expanded.
   - **PATCH**: Clarifications, wording improvements, or typo fixes with no semantic
     change.
4. Update `LAST_AMENDED_DATE` to the amendment date (ISO 8601: YYYY-MM-DD).
5. Propagate changes to dependent templates and agent files; mark each as updated in the
   Sync Impact Report embedded in the constitution header.

All design reviews and PR reviews MUST verify compliance with the Core Principles above.
Complexity introduced in violation of any principle MUST be explicitly documented and
justified before approval.

**Version**: 2.0.1 | **Ratified**: 2026-03-26 | **Last Amended**: 2026-03-26
