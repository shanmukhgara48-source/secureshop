# UI and code quality validation

Checked on 2026-10-08 on `codex/ui-code-quality`, before committing the quality
changes. The original `vulnerable` tag remains at
`d347eb7c2404001fae0a2f43706be6e682afc7d4`.

## Results

- 18 regression tests passed using temporary databases and explicit test keys.
  The final run took 4.953 seconds; output is in `development-checks.txt`.
- Ruff lint and format checks passed; 20 Python files conform. Dependency
  consistency and both local JavaScript syntax checks passed. Every Jinja
  template compiled, and Git whitespace checks passed.
- `browser-checks.json` records 74 page/viewport inspections and normal browser
  journeys. Sign-in, keyboard/mobile navigation, password visibility, category
  links/filtering, AJAX cart updates, checkout, and administrator CRUD passed.
  No console/page errors or external requests were observed.
- `accessibility-checks.json` records the final adjusted source: 45 page/menu
  states, all HTTP 200, zero detected violations, overflow, runtime errors,
  external requests, or navigation retries. All 28 incomplete rule instances
  concern contrast and retain manual-review details. This is limited automated
  coverage, not complete WCAG conformance.
- Twelve captures are recorded in `capture-refresh.json`. All 12 catalogue
  illustrations were decoded for the full-page captures. Their visible layout
  includes the contrast/landmark changes; the final nonvisual link-name
  refinement is verified separately by the accessibility audit.
- Three consecutive normal smoke journeys passed against one initially seeded
  temporary database. These were sequential runs, not three independently
  reset demonstrations.
- Replay preserved the four deliberate observations: foreign order disclosure,
  search result counts of 1/12/0, missing framing headers, and the active local
  jQuery 3.4.1 reference. No browser exploitation of the dependency CVE is claimed.

## Data and checkpoint preservation

Browser, replay, and smoke journeys used isolated temporary/copied databases.
The original `shop.db` SHA256 matched its pre-QA value after those servers
stopped and again after ordinary startup. The temporary QA database was removed.
`app-restart.json` records the normal `python app.py` launch on
`127.0.0.1:8080`, debug off, and successful public page responses.

The original tag, baseline evidence, final-evidence placeholder, and vendored
jQuery files were unchanged. No ZAP scan, remediation, deployment, or
external-target testing was performed.

See `docs/ui-code-quality.md` for the implementation changes and coverage limits.
