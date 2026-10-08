# Assignment requirements and evidence map

Source: **RED TEAM / APPLICATION SECURITY ASSIGNMENT**, eight pages, read in full
on 2026-10-08. Page numbers below are one-based PDF pages. The software assignment
ends with section 10 on page 7. Page 8 contains classroom notices and adds no
software requirement, report format, or submission deadline.

This file maps the document to the **completed functional/regression tests and
local ZAP baseline assessment** performed on 2026-10-08. It was initially prepared
before execution and has now been reconciled with final artifacts. The current
status column records actual results; earlier baseline/UI-quality evidence
remains historical context with its original date and source state. Detailed
results and limits appear in the [assessment report](../../docs/complete-test-report.md).

Read-only source inspection identified the implemented routes and four marked
weaknesses at UI-quality commit `a564617796a857dd482e8fe6daa7244d92ef484b`.
The original `vulnerable` tag remains
`d347eb7c2404001fae0a2f43706be6e682afc7d4`.

## Document requirements

| Source page / section | Requirement | Concrete evidence needed | Current status |
|---|---|---|---|
| pp. 2–3 / §3 Important Security Rule | Test only the owned application locally or in an instructor-approved lab; exclude public, university, production, classmates', and other internet targets. | User authorization and target statement; observed listener/launch settings; ZAP scope/configuration showing the fixed `http://127.0.0.1:8080` origin; target/source/database provenance; logs showing actual coverage and any excluded requests. | Verified: exact loopback scope, Protected mode, 529 active GET requests all to `127.0.0.1:8080`, zero discovered off-origin URLs. Original database/source/tag preserved and original server restored. See [scan record](zap/scan-record.json) and [restoration](restoration.json). |
| pp. 3–4 / §5 Application Requirements | Use an instructor-approved technology stack. Flask is an example, not evidence of approval. | Stack inventory and an instructor approval record, if available. | Flask/SQLite stack implemented. Instructor approval cannot be verified from the PDF or repository; record as unverified. |
| p. 4 / §5 Public functionality | Home, login, registration, product listing, search, and details must work. | New functional results for `/`, `/login`, `/register`, `/products`, `/search`, `/products/<id>`; ordinary search/result evidence; rendered screens and navigation; registration/login outcome. | Verified in regression, three independently reset smoke journeys, and browser checks. See [34-test summary](regression/regression-summary.json), [clean run record](smoke/clean-run-record.json), and [24 browser checks](browser/browser-results.json). |
| p. 4 / §5 Authenticated functionality | User profile, order history, and cart must work. | Logged-in profile and history; cart add/view/remove; the requested simulated checkout and resulting owned order; logout; appropriate anonymous access behavior; source-state-labelled screenshots or response records. | Verified normal cart add/view/remove, simulated checkout, profile/history, logout, guards, server totals, stock, and atomic rollback. Browser observed a correct ₹498.00 owned checkout; all three clean smoke journeys passed. The foreign-order weakness remains deliberately present. |
| p. 4 / §5 Administrative functionality | Admin login, product management, and either user management or user listing. | Admin sign-in; create/edit/delete an unused synthetic product; read-only user list; customer/anonymous rejection from management; referenced-product deletion behavior; current-run result records. | Verified admin login, unused-product create/edit/delete and read-only user listing. Customer access denied; invalid fields and deletion of referenced products reject safely. Regression, smoke, browser, and [ZAP session verification](regression/zap-auth-verification.json) establish appropriate access behavior. |
| pp. 4–5 / §6 Security Requirements | Implement at least four security issues from different categories. Recommended labels include A01, A03, A05, and A06. | Four-row category/location/impact matrix; source markers; observed validation for each issue; distinguish manual confirmation from ZAP detection and classify scanner findings separately. | Four retained deliberate conditions confirmed: foreign order HTTP 200, search counts 1/12/0, absent framing headers plus allowed iframe, and loaded jQuery 3.4.1. See [replay](replay/replay-20261008T070624147663Z.txt), [framing result](browser/browser-results.json), and report SS-01–SS-04. ZAP independently reports injection/framing/component; A01 is manual proof. |
| p. 5 / §6 Important note | Demonstrate weaknesses safely and explain impact; a weaponized exploit is not required. | Bounded local validation, synthetic records, narrowly scoped requests, and impact statements limited to observed behavior. | Completed bounded replay, loopback iframe, and selected GET-only ZAP checks. No writes/code execution are inferred from search comparisons; no completed clickjacking or browser CVE exploit is claimed. No extra exploit tooling was introduced. |
| pp. 5–6 / §7 Outdated Technology Requirement | Intentionally use at least one outdated dependency. Document component name, version used, latest identified version, why risky, and applicable advisory/CVE. | Inventory; actual loaded-asset/version observation; dated primary release/advisory references; affected-version and exploitation-prerequisite explanation; official acquisition source and local integrity check. | Verified active local jQuery 3.4.1, official latest 4.0.0 checked on 2026-10-08, CVE-2020-11022 patched in 3.5.0, and untrusted-HTML DOM-method prerequisite. Vendor checksums and live filtering/AJAX passed. See [dependency inventory](../../docs/dependency-inventory.md), replay, and regression logs. Affected component is confirmed; exploitability is not demonstrated. |
| p. 6 / §7 Package safety | Use legitimate packages from official repositories or instructor materials; do not download unknown malicious packages. | Dependency/vendor manifests and official origin references; ZAP acquisition provenance; no runtime external asset/service dependency. | Official jQuery origin and pinned packages are documented; a fresh clone installed pinned requirements successfully and `pip check`/vendor checksums passed. ZAP 2.17.0/add-ons recorded. Browser observed zero external request attempts. These are provenance/integrity checks, not an independent package security audit. |
| p. 6 / §8 Red Team Mission | Start from the application URL, explore as a tester initially unaware of bug locations, then demonstrate realistic impact within the approved lab. | UI discovery/route notes before targeted validation; roles and access actually used; ordered method log; disclosure of prior code knowledge and builder/tester overlap. | UI journeys preceded targeted validation and ZAP; anonymous/customer/admin coverage is recorded. **Limited alignment:** assessor built/reviewed the app and knew the four weaknesses; a fully blind assessment is not claimed. Method disclosure appears in the Markdown/PDF reports. |
| pp. 6–7 / §9 Phase 2 — OWASP ZAP Scan | Install/configure ZAP and perform an approved local scan. Record scan date, target URL, ZAP version, scan type, alert number, severity, affected URL, and evidence. | Actual ZAP version/configuration and scope; start/end times and completion status; passive/crawl/active phases actually performed; authenticated coverage where configured; raw JSON/HTML export or equivalent; alert counts with a defined counting method and affected URLs. | Complete: ZAP 2.17.0, 2026-10-08 12:38:49–12:43:54 IST, exact target, Protected mode; four spiders/five bounded active scans all 100%, passive queue 0. 270 alert records/10 types; H1/M97/L131/I41 records. [Scan record](zap/scan-record.json), [sanitized alerts](zap/alerts-sanitized.json), [inventory](zap/alert-inventory.json), and [verified role coverage](zap/spider-coverage.json) saved. |
| p. 7 / §9 Scanner interpretation | Investigate automated results instead of accepting them blindly. OWASP Top 10 is not a comprehensive testing standard. | Deduplicated alert inventory with confirmed/false-positive/unresolved classifications, investigation rationale and evidence; scanner limitations, tested roles/routes, and coverage omissions. | Completed per-type [classifications](zap/alert-classifications.json): affected SQL/component/header conditions confirmed; auth/session records informational; suspicious-comment sensitive disclosure false positive; nine potential-XSS hotspots unresolved with benign source-reviewed contexts. Server banner and `nosniff` omissions retained as additional observations. No guarantee only four defects exist. |
| p. 7 / §10 Phase 3 — Finding Investigation | For every significant finding, answer What, Where, Why, Impact, and Evidence. | One evidence-linked investigation per significant finding; exact URL/parameter/header/component/function; relevant source condition; bounded achievable impact; requests/responses, screenshots, advisory, or scanner evidence that support the conclusion. | Completed in [Markdown report](../../docs/complete-test-report.md) and [PDF report](../../output/pdf/SecureShop_Test_Report.pdf): SS-01–SS-04 investigations, full 10-type interpretation, additional environment/header observations, limitations, and future retest criteria. |

## User-authorized scope and full-assignment boundary

The current user request adds full functional/regression testing and a local ZAP
baseline scan, with Markdown and PDF reporting. It explicitly excludes writing
fixes. Preserve the controlled four-weakness implementation, original tag,
existing evidence, vendor files, and original data. Use synthetic data and local
assets; redact signing keys, session cookies, CSRF values, and credentials from
scan/report exports.

The title on page 1 and learning objectives on page 2 also require remediation,
retesting, and before/after evidence for the **complete assignment**. Those are
future work outside this authorized assessment. The report must be labelled a
baseline assessment and must not claim that the whole assignment is complete.
There is no verified instructor deadline or required report template in the PDF.

## Verified results and remaining limits

- Actual execution passed 18 existing and 16 additional isolated tests, eight
  static/dependency checks, fresh-clone setup, three independently reset smoke
  journeys, and 24 browser checks. Browser inspection covered 75 responsive states
  without overflow. Python 3.14.3/macOS/Chromium were exercised; actual Python 3.11
  was not run. One initial expiry-test harness error was corrected and retained.
- `/orders` is owner-filtered; `/orders/<id>` intentionally omits ownership.
  Normal history tests and deliberate foreign-order validation answer different
  questions and should be reported separately.
- The intentionally constructed search SELECT is the one SQL exception. Observe
  its bounded comparison and ordinary searches; do not imply write access,
  operating-system access, or code execution from changed result counts.
- Missing framing headers can be confirmed by response headers. A permitted
  iframe confirms embedding, not a completed clickjacking attack.
- jQuery 3.4.1 presence is an affected-component finding. The documented CVE
  needs untrusted HTML reaching affected DOM methods; this app's text updates
  do not themselves prove that exploitation prerequisite is met.
- All three ZAP user sessions were independently verified, and saved responses
  confirm appropriate authenticated customer/admin routes. Four spiders and five
  active phases completed. Active coverage was non-recursive and limited to GET
  search/order/profile/admin-products targets with 14 selected built-in rules;
  there was no AJAX spider or automated mutation testing.
- Report unexpected scanner alerts even when they are outside the four planned
  issues. Record whether they are additional confirmed issues, duplicates of a
  planned weakness, false positives, or unresolved observations. Make no
  guarantee that there are only four possible defects.
- Distinguish unique alert types, affected instances, and severity totals so
  duplicate URLs or repeated scan phases do not silently inflate counts.
- The 31-state axe run has one moderate unnamed-landmark best-practice observation
  and 11 incomplete color-contrast instances requiring manual review. These are
  accessibility observations, not a fifth deliberate security weakness.
- Instructor stack approval remains unverified; the assessor's prior code
  knowledge limits the PDF's blind-tester scenario. Remediation, fixed tagging,
  equivalent retesting and before/after results remain future authorized work.
- Final restoration verified the original database checksum, unchanged
  application source and original vulnerable tag, stopped temporary servers,
  and restored the normal loopback application. See [restoration](restoration.json).

## Completed baseline report structure

1. **Scope and provenance:** local target and ownership, explicit user scope,
   unverified instructor stack approval, assessment dates/timezone, source
   commit/working-tree state, synthetic database isolation, and exclusions.
2. **Application and dependency inventory:** architecture, required journey
   coverage, versions actually observed, outdated library/advisory/release
   sources, and source locations of the four intentional weaknesses.
3. **Method and functional results:** UI discovery with prior-knowledge
   disclosure; actual automated/manual/browser checks; pass/fail/skipped counts;
   normal customer/admin journeys and evidence; preserved-data checks.
4. **ZAP baseline scan record:** version and add-ons, effective scope/mode/policy,
   dates, phases and completion, roles/routes actually covered, exclusions,
   exports, alert totals/counting convention, and severity breakdown.
5. **Finding investigation:** one subsection per significant ZAP or manual
   finding using the format below. Separate scanner claims from validation.
6. **Coverage limits and next phase:** unresolved findings and prerequisite
   limits; no claim of comprehensive testing; planned remediation/retest remain
   future scope. Do not present proposed fixes as applied or retested.
7. **Evidence index:** actual relative artifact paths, timestamps, source state,
   and checksum/manifest where available. Include only files that exist.

### Investigation format

| Field | Required content |
|---|---|
| Identifier and status | Stable finding ID; confirmed, false positive, or unresolved; whether intentional/manual/scanner-reported; confidence supported by evidence. |
| What? | The weakness actually observed, plus ZAP alert name/plugin ID when applicable. |
| Where? | Affected URL, parameter, header, component/version, or functionality; exact source location where relevant. |
| Why? | The implementation/configuration/advisory condition explaining the weakness; separate facts from inference. |
| Impact? | What the local observations demonstrate an attacker could achieve; prerequisites and untested impacts. |
| Evidence? | Referenced real request/response, result count, screenshot, loaded asset, advisory, or scan artifact with date/source state. |
| Mapping | Assignment-primary OWASP 2021 category; optional OWASP 2025 cross-reference. A mapping is classification, not proof. |
| Future action | Planned fix and retest criterion clearly labelled not implemented in this task. |

Use **confirmed** when the evidence establishes the stated condition; describe
unproven impact separately. Use **false positive** only with contradictory or
inapplicability evidence, not merely because the alert is inconvenient. Use
**unresolved** when prerequisites, coverage, or reproduction remain uncertain.
A scanner not reporting a known issue does not establish its absence.

## Completion state for this file

The assignment mapping has been reconciled with the completed current-suite
functional results, ZAP metadata/alerts, investigations, restoration check, and
Markdown/PDF reports. The current authorized baseline assessment is complete;
instructor approval is unverified and the full assignment's remediation/retest
objectives remain future scope. This mapping subtask inspected evidence and
updated documentation only; it made no application changes or commits.
