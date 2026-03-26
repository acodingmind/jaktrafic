# Feature Specification: JakTrafic — GTFS Route Planner Web Application

**Feature Branch**: `001-gtfs-route-planner`  
**Created**: 2026-03-26  
**Status**: Draft  
**Input**: User description: "Build a soseki.io based web application — a public transport route planner based on static GTFS data stored in a `data` folder."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plan a Route Between Two Stops (Priority: P1)

A commuter opens JakTrafic, types their origin stop name and destination stop name, selects a travel date and departure time (or keeps the current date/time default), and receives a list of route options. Each option shows departure time, arrival time, total journey duration, the number of transfers, and the names of the lines and stops involved. The user picks their preferred option and can see the full stop-by-stop breakdown of the journey.

**Why this priority**: This is the core value proposition of the application. Without a working route planner, no other feature delivers meaningful value. Every other user story builds on or extends this capability.

**Independent Test**: Can be fully tested by entering a valid origin stop and a valid destination stop in the loaded GTFS data, submitting the query, and verifying that at least one route option is returned with correct departure and arrival times that match the GTFS timetable. Delivers a complete end-to-end journey-planning flow.

**Acceptance Scenarios**:

1. **Given** a user has opened the application and the GTFS feed validity period covers today's date, **When** the user enters a valid origin stop name, a valid destination stop name, and keeps the default current date/time, **Then** the system returns one or more route options within 2 seconds, each showing departure time, arrival time, total duration, number of transfers, and line names.
2. **Given** a user on the route planner page, **When** the user enters a stop name that partially matches multiple stops, **Then** the system presents a disambiguating list of matching stops for the user to choose from before calculating routes.
3. **Given** a valid origin and destination are entered, **When** no route exists between them in the GTFS data, **Then** the system displays a clear "no route found" message rather than an empty or broken result.
4. **Given** a valid origin and destination are entered but they are the same stop, **When** the user submits the query, **Then** the system displays an informative message indicating origin and destination cannot be the same.
5. **Given** the user has keyboard-only navigation, **When** filling in origin, destination, date, and time fields and submitting, **Then** all interactions are achievable without a mouse and focus management is correct throughout.

---

### User Story 2 - View Departures for a Stop (Priority: P2)

A traveller wants to know what buses or trams leave from a specific stop in the next hour. They search for a stop by name, select the correct stop from results, and see a departure board listing all upcoming trips from that stop for the chosen date — showing line name, direction/headsign, and scheduled departure time.

**Why this priority**: A departure board is a high-utility, standalone feature that serves users who already know their preferred line and just need timing information. It is independently deployable and valuable before multi-leg routing is fully refined.

**Independent Test**: Can be fully tested by searching for a known stop, selecting it, and verifying that the departure board lists all scheduled trips from that stop for the current date, matching the GTFS timetable, without requiring a destination to be entered.

**Acceptance Scenarios**:

1. **Given** a user searches for a stop by name, **When** the user selects a specific stop, **Then** the system displays a departure board showing all scheduled departures from that stop for the selected date, including line name, direction/headsign, and departure time.
2. **Given** a user is viewing a departure board, **When** the user changes the selected date, **Then** the departure list updates to reflect the timetable for the new date.
3. **Given** a stop has no scheduled departures on the selected date (e.g., the line does not operate that day), **When** the user views the departure board, **Then** the system shows an explicit "no departures on this day" message.
4. **Given** a screen reader user navigates to the departure board, **When** the board is displayed, **Then** departure rows are announced with line name, direction, and time in a logical reading order via semantic HTML.

---

### User Story 3 - Data Freshness Transparency (Priority: P3)

A user plans a trip for a date two weeks in the future. The system checks the loaded GTFS feed's validity period. If the requested travel date falls outside the feed's validity window, the user sees a prominent, accessible warning indicating that the schedule data may not cover their travel date and the results may be unreliable.

**Why this priority**: Without this safeguard, users could plan a journey based on outdated or out-of-scope timetable data and miss their connection. This is a non-negotiable constitutional requirement and must be implemented alongside the route planner (P1), but is listed as P3 because it is a guardrail on top of an already validated P1 flow rather than a standalone journey.

**Independent Test**: Can be fully tested by setting the requested travel date to a date outside the GTFS feed's `feed_info.txt` validity range and verifying that a visible warning is shown on the results page, and that no route result is displayed without that warning.

**Acceptance Scenarios**:

1. **Given** the user requests a route for a date that falls outside the GTFS feed's validity period, **When** results are displayed, **Then** a visible, accessible data-freshness warning appears informing the user the schedule may not cover their travel date.
2. **Given** the user requests a route for a date within the GTFS feed's validity period, **When** results are displayed, **Then** no warning is shown.
3. **Given** the application starts up with a GTFS feed whose validity window has already expired, **When** an operator queries the `GET /api/v1/feed/status` endpoint, **Then** the response contains a machine-readable operator-visible warning indicating the feed is outside its validity window.
4. **Given** the data-freshness warning is present, **When** a screen reader user encounters it, **Then** the warning is announced as a prominent notification with sufficient context about what action the user may take.

---

### Edge Cases

- What happens when no route exists between origin and destination in the GTFS data? → System displays a clear "no route found" message; no blank or broken UI.
- How does the system handle a travel date outside the GTFS feed's validity period? → Visible data-freshness warning is shown; routing may still be attempted but results are labeled as potentially unreliable.
- What if the `data` folder contains malformed or incomplete GTFS files (e.g., missing required fields)? → Application fails startup with an explicit, logged error message identifying the offending file; no partially-loaded data is served to users.
- What if a stop name search matches zero stops? → System displays a "no stops found" message with a suggestion to try a different search term.
- What if a stop name search matches more than 10 stops? → System returns the top matches (ordered by relevance/alphabetical) with a note that results are limited; user can refine their search.
- What happens when origin and destination are the same stop? → System displays an informative error preventing the query from executing.
- What if the GTFS feed contains multiple calendar entries and a particular date has no service? → Departure board shows "no departures on this day" and route planner returns "no route found" with a note that no service operates on that date.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a route planner interface where users can enter an origin stop, a destination stop, a travel date, and a departure time, then submit the query to receive route options.
- **FR-002**: The system MUST calculate route options using exclusively the static GTFS data located in the `data` folder; no external routing services or real-time feeds may be used.
- **FR-003**: Each route option returned MUST include: departure time from origin, arrival time at destination, total journey duration, number of transfers, and the name/identifier of each line and boarding/alighting stop for every leg.
- **FR-004**: The system MUST validate the GTFS feed validity period (from `feed_info.txt`) against the requested travel date and display a user-visible data-freshness warning whenever the requested date falls outside the feed's validity window.
- **FR-005**: The system MUST validate GTFS feed validity dates on application startup and present an operator-visible warning when the loaded feed is outside its validity window.
- **FR-006**: The system MUST allow users to search for stops by name and present a disambiguation list when multiple stops match the search input.
- **FR-007**: The system MUST provide a departure board view for any selected stop, listing all scheduled departures for a user-selected date, including line name, direction/headsign, and scheduled departure time.
- **FR-008**: The system MUST display a clear message when no route is found between origin and destination rather than an empty or undefined state.
- **FR-009**: The system MUST display a clear message when no departures are scheduled from a stop on the selected date.
- **FR-010**: The system MUST default the travel date and time to the current date and current time when the user has not selected otherwise.
- **FR-011**: All user-facing interfaces MUST meet WCAG 2.1 Level AA accessibility requirements.
- **FR-012**: All interactive elements (stop search, date/time picker, route results, departure board) MUST be fully operable via keyboard alone.
- **FR-013**: All route and departure information MUST be programmatically associated with semantic HTML elements and ARIA labels to be accessible to screen readers.
- **FR-014**: Every transit line or alert state that uses color coding MUST also display an accompanying text label or pattern so that color is never the sole differentiator.
- **FR-015**: The system MUST NOT persist user-provided origin, destination, or location data on the server beyond the duration of processing a single request.
- **FR-016**: The system MUST NOT log route queries against identifiable user identifiers or IP addresses.
- **FR-017**: Third-party analytics or tracking scripts MUST NOT be loaded without explicit, informed user opt-in consent.
- **FR-018**: The system MUST expose a REST API for the route planner and departure board endpoints, documented with an OpenAPI specification.
- **FR-019**: If the `data` folder contains malformed or incomplete GTFS files, the system MUST fail startup with an explicit error message identifying the offending file rather than serving partial data.

### Key Entities

- **Stop**: A transit stop or station with a unique identifier, a human-readable name, and a geographic position (latitude/longitude). Serves as origin, destination, or transfer point.
- **Route (Line)**: A named public transport line (bus, tram, metro, rail, etc.) identified by a code/short name and long name, associated with a transit agency.
- **Trip**: A specific scheduled run of a Route on a given day, following a defined sequence of stops with scheduled arrival and departure times.
- **Journey**: A planned travel path from origin stop to destination stop for a specific date/time, composed of one or more Legs.
- **Leg**: A single uninterrupted segment of a Journey on one vehicle/line, starting at a boarding stop and ending at an alighting stop.
- **Transfer**: The act of a user changing between two Legs at a shared stop, characterised by the waiting time between alighting and re-boarding.
- **GTFS Feed**: The static data set in the `data` folder, with a defined validity period declared in `feed_info.txt`, acting as the sole authoritative source of schedule and network data.
- **Departure**: A single scheduled departure event for a Trip at a Stop on a given calendar date.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can enter an origin and destination and receive at least one valid route option (or a clear "no route" message) within 2 seconds for 95% of queries under normal load.
- **SC-002**: Users are never presented with a route or departure result derived from an expired or out-of-scope feed without a visible, accessible data-freshness warning.
- **SC-003**: All user-facing pages pass automated WCAG 2.1 Level AA accessibility audits with zero critical violations.
- **SC-004**: All primary user interactions — entering stops, selecting dates, viewing results — are fully completable via keyboard alone, with no dead-end focus traps.
- **SC-005**: No personally identifiable location data or query history is retained on the server after a route or departure query has been fulfilled.
- **SC-006**: The application's initial page renders and is interactive within 3 seconds on a median 4G mobile connection.
- **SC-007**: The application functions correctly on the last 2 stable versions of Chrome, Firefox, Safari, and Edge on desktop, and on iOS 15+ and Android 9+ on mobile.
- **SC-008**: Users can view all stops and departures without creating an account or providing any personal information.

## Assumptions

- The `data` folder contains a single GTFS static feed (or one logically merged feed) covering a defined geographic transit network; management of multiple independent feeds is out of scope.
- User accounts, saved journeys, and personalisation features are out of scope for this specification.
- Real-time vehicle tracking and live arrival/departure updates (GTFS-Realtime) are explicitly out of scope; only static scheduled data is used.
- A map-based stop picker UI is a nice-to-have enhancement and is not required for the core route planner or departure board to deliver value; if included, it uses a publicly available tile provider.
- Stop names and route labels are displayed in the language present in the GTFS feed files; multi-language or translation support is out of scope.
- The application is a read-only public tool; no administrative UI for managing or uploading GTFS data is in scope for this specification.
- Internet connectivity is assumed for users accessing the web application; offline or progressive-web-app offline mode is out of scope.
- The routing algorithm used will be the simplest algorithm that satisfies the journey-planning requirements (respecting the YAGNI principle); advanced optimisations are deferred unless benchmarks show they are necessary.
