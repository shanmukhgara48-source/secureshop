# SecureShop: functional testing and local ZAP baseline assessment

**Assessment date:** 8 October 2026, Asia/Kolkata (UTC+05:30).  
**Report state:** functional, manual, and bounded ZAP baseline assessment complete; unresolved observations retained below.  
**Application state:** intentionally vulnerable; no remediation performed.

## 1. Assessment outcome and scope

SecureShop passed **34 regression tests**, **three independently reset customer/admin smoke journeys**, and a fresh-clone installation check. Browser testing passed **24 functional checks** and inspected **75 responsive states** without horizontal overflow. The four deliberately introduced weaknesses remain reproducible: foreign-order disclosure, search SQL injection, missing framing protection, and the loaded jQuery 3.4.1 component.

ZAP 2.17.0 completed four spiders and five bounded active scans, issuing 529 active requests, all GETs to the exact loopback target. Its final export contains **270 alert records across 10 alert types**: one High, 97 Medium, 131 Low, and 41 Informational records. Investigation confirms the SQL injection, missing framing/CSP protection, and affected jQuery component; the A01 disclosure is established manually rather than by a separate scanner alert. Other records describe header hardening, a development-server version banner, benign scanner metadata, a false-positive comment disclosure, and an unresolved potential-XSS hotspot.

Accessibility testing recorded one moderate `landmark-unique` best-practice finding and 11 color-contrast rule instances that require manual review. These are recorded separately from the four intentional security weaknesses. The original application was restored after assessment, its database checksum matched, source remained unchanged, and the original vulnerable tag was preserved.

The authorized target is **`http://127.0.0.1:8080`**, an owned local university lab application with synthetic records. A separate loopback fixture at `http://127.0.0.1:9000` was used only to demonstrate framing. No public, university, production, or third-party application was tested. Customer/admin mutations ran on an isolated fresh clone and database. The scan is a baseline assessment; fixes, remediation validation, and a comparative retest remain future work.

| Provenance item | Recorded state |
|---|---|
| Tested source commit | `a564617796a857dd482e8fe6daa7244d92ef484b` |
| Branch | `codex/ui-code-quality` |
| Original `vulnerable` tag | `d347eb7c2404001fae0a2f43706be6e682afc7d4` |
| New evidence directory | `evidence/test-suite-20261008T065601Z/` |
| Application source changes during assessment | None; final preservation check verified unchanged source |
| Runtime listener | `127.0.0.1:8080`; Flask debug and reloader disabled |
| Instructor approval of stack | Unverified; Flask being listed as an example does not establish approval |
| Final original-database restoration | Verified: identical before/after SHA-256; original application restored |

The assignment PDF was read in full, including all eight pages. Sections 3, 5, 6, 7, 8, 9, and 10 govern scope, functionality, deliberate weaknesses, dependency documentation, tester methodology, scanning, and finding investigation. Page 8 contains classroom notices. The document supplies no verified report template or deadline. The [requirements and evidence map](../evidence/test-suite-20261008T065601Z/assignment-requirements.md) records page and section references. The title and learning objectives also require fixing and retesting for the complete assignment; this baseline report does not claim that the full assignment is complete.

## 2. Application and environment

SecureShop is a server-rendered Flask monolith using raw `sqlite3`, Jinja templates, local CSS/JavaScript, and Flask signed-cookie sessions. Checkout creates a synthetic order without payments, email, shipping integrations, analytics, or runtime external services. The current UI-quality branch improves presentation and maintainability while preserving the vulnerable baseline and its historical evidence.

The seed contains three accounts, 12 products across Study, Carry, Everyday, and Tech, and six orders. Customer A owns order IDs 1–3; customer B owns 4–6. Seed resets restore deterministic application data; password hashes are regenerated. The regression check reported an empty foreign-key check and SQLite `integrity_check` of `ok`.

| Component | Version exercised or observed | Purpose |
|---|---|---|
| Python | 3.14.3 | Runtime used for this assessment |
| Flask | 3.1.3 | Application framework |
| SQLite | 3.51.3 | Local relational database |
| Flask-WTF | 1.3.0 | CSRF validation |
| Werkzeug | 3.1.9 | Password hashing and HTTP utilities |
| Jinja2 | 3.1.6 | Autoescaped HTML templates |
| jQuery, loaded catalogue asset | 3.4.1 | Category filtering and AJAX cart updates; deliberate outdated component |
| jQuery, unused local upgrade asset | 4.0.0 | Reserved for future remediation |
| Chromium | 151.0.7922.34 | Browser assessment |
| axe-core | 4.14.0 | Automated accessibility checks |
| OWASP ZAP | 2.17.0 | Authorized bounded local baseline assessment |
| Node.js | 24.19.0 | JavaScript syntax checks |
| Ruff, development only | 0.16.10 | Python lint and formatting checks |
| Host platform | macOS 26.6.2, arm64 | Actual assessment environment |

The declared minimum is Python 3.11+. Ruff targets Python 3.11 syntax, but an actual Python 3.11 runtime was not exercised. Dependency pins and vendor integrity checks passed; these checks establish reproducibility and consistency with recorded files, rather than proving that every dependency is free of vulnerabilities. Full package details appear in the [dependency inventory](dependency-inventory.md) and [regression summary](../evidence/test-suite-20261008T065601Z/regression/regression-summary.json).

## 3. Method and evidence boundaries

The assessment combined ordinary UI journeys, isolated regression/control checks, fresh-clone setup, a small fixed-target replay, a separate iframe demonstration, and the authorized ZAP baseline. The tester also built or reviewed parts of the application. UI exploration was performed, but this was not an independent blind test by someone unaware of the source or bug locations. That limitation matters when interpreting the assignment's Red Team mission.

Normal browser and smoke mutations used synthetic accounts, orders, and a temporary unreferenced product in the isolated QA database. The server was stopped and that database was seeded before each of the three smoke runs. ZAP activity was paused during browser mutations. The replay accepts only the exact loopback origin and rejects external targets or off-origin redirects. No additional exploit tooling or payload list was introduced for this assessment.

The four manual findings below report only the impact observed. Changed SQL result counts do not prove writes or operating-system access; successful embedding does not prove a completed clickjacking attack; and an affected library version does not establish that its exploitation prerequisite is reachable. Scanner observations will be classified independently rather than treated as automatic proof.

## 4. Functional and regression results

### 4.1 Automated regression and control checks

All **18 existing tests** and **16 additional isolated checks** passed: **34 passed, zero final failures**. Regression completion was recorded at 12:33:59 IST. Eighteen Jinja templates compiled, and 14 Python files passed syntax validation. All eight static/dependency checks exited successfully: four JavaScript syntax checks, `pip check`, Ruff lint, Ruff formatting, and vendor checksums.

| Coverage group | Verified behavior |
|---|---|
| Public and registration | Required public routes load; ordinary searches work; usernames/passwords/email limits enforced; synthetic `.invalid` emails required; duplicate account data rejected; supplied roles ignored and passwords hashed |
| Authentication and sessions | Generic errors; anonymous AJAX guard; database role changes and invalid sessions remove access; login rotates CSRF; logout clears authentication; failure throttle expires and successful authentication clears failures |
| CSRF and methods | Missing/expired tokens rejected without mutation; oversized forms rejected; mutations require POST |
| Customer data | Cart ownership enforced; invalid quantities/stock rejected; owner-filtered order history; server-calculated integer currency; order price snapshots survive later product edits |
| Checkout integrity | Multi-item checkout succeeds; insufficient stock fails safely; an isolated forced database error rolls back all checkout changes |
| Administrator | Role enforcement; valid create/edit/delete; invalid fields leave data unchanged; referenced products cannot be deleted; rendered product text escaped |
| Error handling and confinement | Generic 400/403/404/500 responses; no injected sentinel or traceback exposed; fixed loopback launch; external replay targets/redirects rejected without network contact |
| Seed and assets | Deterministic data reset, valid relationships, local references, known image paths/fallback, template compilation, and source syntax |

One initial isolated test run failed because its harness set a `timedelta` value unsupported by Flask-WTF 1.3.0's `CSRF_TIME_LIMIT`. The corrected harness left the application's normal 3,600-second configuration intact and used a backdated signed token to exercise expiry. The final 16-test run passed without changing application source. Initial failure logs and the revised helper are retained for traceability; this was classified as a harness error, not an application finding.

Evidence: [aggregate regression result](../evidence/test-suite-20261008T065601Z/regression/regression-summary.json), [existing-test log](../evidence/test-suite-20261008T065601Z/regression/unittest.log), [focused-control log](../evidence/test-suite-20261008T065601Z/regression/focused-controls.log), [initial harness failure](../evidence/test-suite-20261008T065601Z/regression/focused-controls.initial-harness-failure.log), and [focused-check summary](../evidence/test-suite-20261008T065601Z/regression/focused-summary.json).

### 4.2 Fresh-clone setup

An isolated clone checked out the exact tested commit, created its own virtual environment, installed the pinned requirements, passed `pip check`, seeded the database, and imported the application factory. All seven setup stages completed successfully. The clone had a separate database and signing key; debug was disabled, the trusted host was `127.0.0.1`, and cookie settings retained HttpOnly and SameSite=Lax. The original database's SHA-256 matched before and after this setup/regression phase.

Evidence: [fresh-clone summary](../evidence/test-suite-20261008T065601Z/regression/fresh-clone-summary.json), [installation log](../evidence/test-suite-20261008T065601Z/regression/fresh-install.log), [seed log](../evidence/test-suite-20261008T065601Z/regression/fresh-seed.log), and [import/isolation check](../evidence/test-suite-20261008T065601Z/regression/fresh-import-and-separation.log).

### 4.3 Three clean smoke journeys

All three normal smoke runs passed after separate resets. Each covered registration → login → ordinary search → product detail → add to cart → remove → re-add → simulated checkout → order history/profile → logout. Each also covered admin login → create → edit → delete an unreferenced product → user listing → logout. These runs tested normal functionality; the deliberate weaknesses were checked separately by replay.

Evidence: [reset/run provenance](../evidence/test-suite-20261008T065601Z/smoke/clean-run-record.json), [run 1](../evidence/test-suite-20261008T065601Z/smoke/smoke-20261008T070534555309Z.txt), [run 2](../evidence/test-suite-20261008T065601Z/smoke/smoke-20261008T070543061809Z.txt), and [run 3](../evidence/test-suite-20261008T065601Z/smoke/smoke-20261008T070555570314Z.txt).

### 4.4 Browser, responsive, and accessibility checks

Browser checks ran from 12:36:48 to 12:37:57 IST against the isolated clone. All **24 functional checks** passed. They included registration/login, generic errors and access denial, empty states, all four category filters and URL selection, search/details, AJAX cart updates, cart removal, correctly calculated ₹498.00 checkout, order/history/profile, admin product CRUD/user listing, logout, and core form behavior with JavaScript disabled. The separate iframe fixture successfully embedded the catalogue.

The browser inspected **75 responsive states** at five widths: 14 baseline route/role combinations and five populated-cart states. There was no horizontal overflow. It recorded 75 semantic inspections, 30 computed contrast checks, and 23 screenshots. There were **zero JavaScript exceptions, unexpected failed requests, or external request attempts**. Four console messages were expected HTTP responses produced by negative checks: login 400, registration 400, missing route 404, and customer access to admin products 403.

Accessibility status is **partially verified, with outstanding review**. Across 31 axe states, one moderate best-practice violation was reported on `/admin/products/new` at desktop width: `.admin-sidebar` and `.editor-note-card` are two unnamed complementary landmarks. Eleven color-contrast rule instances were incomplete and require manual review, including cases where image backgrounds prevented automatic determination. The 30 computed solid-background checks had no failures, but they do not settle image/overlap contrast or establish full WCAG conformance. No accessibility fixes were made during this baseline assessment. This observation is not classified as a fifth deliberate security flaw.

Evidence: [browser result record](../evidence/test-suite-20261008T065601Z/browser/browser-results.json), [catalogue desktop](../evidence/test-suite-20261008T065601Z/browser/catalogue-desktop.png), [catalogue mobile](../evidence/test-suite-20261008T065601Z/browser/catalogue-mobile.png), [populated mobile cart](../evidence/test-suite-20261008T065601Z/browser/cart-mobile.png), [admin editor](../evidence/test-suite-20261008T065601Z/browser/admin-product-editor.png), and [allowed framing](../evidence/test-suite-20261008T065601Z/browser/framing-allowed.png).

## 5. Manual investigation of the four deliberate weaknesses

The replay ran at **12:36:24 IST**, on a fresh seed at the tested commit. Its working-tree marker reads `modified` because earlier checks had produced untracked evidence; the clean-run record and regression source check confirm that tracked application source remained unchanged. The replay records observations without asserting that a vulnerable result must continue after future fixes.

| Finding | OWASP 2021, assignment label | OWASP 2025 cross-reference | Manual status |
|---|---|---|---|
| SS-01: foreign-order disclosure | A01 Broken Access Control | A01 Broken Access Control | Confirmed |
| SS-02: interpolated search SQL | A03 Injection | A05 Injection | Confirmed |
| SS-03: framing protection omitted | A05 Security Misconfiguration | A02 Security Misconfiguration | Confirmed |
| SS-04: affected jQuery component | A06 Vulnerable and Outdated Components | A03 Software Supply Chain Failures | Confirmed affected component; exploitability not demonstrated |

The mappings are classification aids, not proof or a comprehensive testing standard. See the [vulnerability matrix](vulnerability-matrix.md) for the planned remediation design.

### SS-01 — Customer can view another customer's order

**What:** an authenticated customer can retrieve a foreign order by changing the numeric detail URL.

**Where:** `GET /orders/<id>`, specifically `/orders/4` when signed in as `customer_a`; [`order_detail` in customer routes](../routes/customer.py), at the marked intentional A01 query.

**Why:** the detail route requires authentication but selects the order by ID alone. It omits the logged-in user's ID from the ownership condition. The ordinary `/orders` list remains owner-filtered.

**Impact:** customer A received customer B's synthetic order details, including its owner, items, amounts, status, and date. This demonstrates cross-account disclosure. Order modification or administrative access was not demonstrated.

**Evidence:** `/orders/4` returned HTTP **200** and `foreign_order_data_returned=true` in the [current replay](../evidence/test-suite-20261008T065601Z/replay/replay-20261008T070624147663Z.txt). Seed invariants independently establish customer B owns order 4.

**Future remediation and retest:** constrain the lookup to the order ID and session user's ID; deny foreign access. Retest the same request while retaining successful own-order access and owner-filtered history. Not implemented here.

### SS-02 — Search input changes the SQL predicate

**What:** raw search input is concatenated into SQL and can change which product rows the SELECT returns.

**Where:** `GET /search?q=...`; [`search` in public routes](../routes/public.py), marked `INTENTIONAL A03 - fix in remediation phase`.

**Why:** the query interpolates the raw `q` value into `LIKE` expressions rather than binding it as a parameter. It remains a single read-only SELECT executed through normal `sqlite3.execute()`; all other application SQL is parameterized.

**Impact:** a bounded boolean comparison changed results from one matching product to all 12 products or zero products. It demonstrates control of the search predicate. Database writes, stacked statements, credential extraction, and operating-system access were not tested or established.

**Evidence:** all three replay requests returned HTTP **200**: ordinary `notebook` returned **1**, the true comparison returned **12**, and the false comparison returned **0**. The unchanged small replay helper and [timestamped output](../evidence/test-suite-20261008T065601Z/replay/replay-20261008T070624147663Z.txt) preserve the exact comparison.

**Future remediation and retest:** parameterize the two search values. The same comparison should then be treated as literal search text, while normal searches still work. Not implemented here.

### SS-03 — Catalogue can be embedded in a separate frame

**What:** HTML responses omit framing restrictions, allowing a separate origin to embed the catalogue.

**Where:** `/` and `/products` response headers; intentional A05 omission in the [`after_request` hook](../app.py).

**Why:** neither `Content-Security-Policy` with `frame-ancestors` nor `X-Frame-Options` is sent. This omission is deliberately retained.

**Impact:** the `127.0.0.1:9000` fixture successfully displayed the `127.0.0.1:8080` catalogue in an iframe. Embedding is the demonstrated condition; a completed clickjacking interaction was not attempted or claimed.

**Evidence:** replay reports both headers **absent** on home and catalogue. The browser's separate-loopback framing check passed, with [framing screenshot](../evidence/test-suite-20261008T065601Z/browser/framing-allowed.png) and [browser result](../evidence/test-suite-20261008T065601Z/browser/browser-results.json).

**Future remediation and retest:** add CSP `frame-ancestors 'none'` and `X-Frame-Options: DENY`; repeat the same header and iframe checks. Not implemented here.

### SS-04 — Catalogue loads jQuery 3.4.1

**What:** the catalogue actively uses an affected, outdated jQuery release.

**Where:** `/products` references `/static/vendor/jquery/jquery-3.4.1.min.js`; the intentional A06 reference is marked in the [catalogue template](../templates/public/catalogue.html). An unused local 4.0.0 file is present for the future fix phase.

**Why:** version 3.4.1 was intentionally retained. CVE-2020-11022 affects jQuery versions from 1.2 up to, but excluding, 3.5.0; the advisory identifies 3.5.0 as patched. The relevant prerequisite is untrusted HTML reaching affected DOM manipulation methods such as `.html()` or `.append()`. See the [official jQuery advisory](https://github.com/jquery/jquery/security/advisories/GHSA-gxr4-xjj5-5px2).

**Impact:** the deployed local catalogue is dependent on an affected component. Browser execution through this CVE was **not demonstrated**. The application's text updates and use of escaped, inert fragments do not by themselves prove that the advisory's untrusted-HTML prerequisite is reachable.

**Evidence:** replay recorded the local 3.4.1 script path; browser category filters and AJAX cart updates exercised its actual use; recorded vendor checksums passed. The [official download page](https://jquery.com/download/) was checked on **8 October 2026** and identified **jQuery 4.0.0** as the latest release. Component origin, version, risk, advisory, and prerequisites are documented in the [dependency inventory](dependency-inventory.md).

**Future remediation and retest:** switch the active asset to the current approved release and test category filtering, AJAX cart updates, and JavaScript-disabled fallbacks again. Recheck the latest release on the remediation/report date. Not implemented here.

## 6. OWASP ZAP baseline scan record

The authorized ZAP **2.17.0** scan ran from **12:38:49 to 12:43:54 IST** against the exact tested loopback origin. The effective configuration was Protected mode, context ID 3 (`SecureShop baseline 2026-10-08`), and policy `SecureShop bounded GET baseline`. The include expression was `^http://127[.]0[.]0[.]1:8080(?:/.*)?$`; mutation routes were excluded. Spider form processing and posting were disabled. The bounded active policy enabled 14 selected built-in rules; operating-system command, time-based SQL, external callback, XML-expansion, and cloud-metadata rules were excluded.

All **four traditional spiders** and **five active phases** reached 100%, and the passive queue reached **zero**. The active phases were non-recursive: two search passes as anonymous, an owned order as customer A, profile as customer B, and product management as admin. The first search pass at LOW SQL-rule strength did not raise injection; expanding the general built-in SQL rule to HIGH produced the SQL alert. This demonstrates a scanner coverage/strength limit, rather than contradicting the manual replay.

Authentication was independently verified for customer A, customer B, and admin using ZAP's private sessions and direct loopback GETs: all profiles returned 200 with the expected authenticated identity; customer access to the admin user list returned 403; admin access returned 200. The anonymous profile request redirected to login. Saved spider responses also establish authenticated 200 coverage of customer profiles/orders and admin product/user/new/edit pages. This is stronger evidence than configured usernames alone, while still not claiming every route/role received every active rule.

| Required scan field | Final recorded result |
|---|---|
| Date and source | 8 October 2026; source `a564617796a857dd482e8fe6daa7244d92ef484b` |
| Target | `http://127.0.0.1:8080` only |
| Start | 07:08:49 UTC / 12:38:49 IST |
| Finish and final completion | 07:13:54 UTC / 12:43:54 IST; COMPLETE; passive queue 0 |
| ZAP version and add-ons | 2.17.0; installed add-on and rule inventories saved |
| Scan type | Traditional spider and passive analysis; bounded GET-only active checks |
| Mode/context/policy | Protected; context 3; bounded GET policy |
| Automated mutation exclusions | `/logout`, `/checkout`, product-delete routes; spider form processing/posting off |
| Verified authenticated coverage | Customer A, customer B, and admin sessions verified; role-specific successful responses recorded |
| Active request count | 529; all GET; all `127.0.0.1:8080` |
| Spider coverage rows | Anonymous 40; customer A 55; customer B 58; admin 70; these include redirects, assets, and negative paths |
| Recorded history messages | 811; this is broader than active-request count and is not an alert count |
| Discovered off-origin URLs | 0 |
| Unique alert types / alert records | 10 types / 270 records; not 270 independent vulnerabilities |
| Severity by records | High 1; Medium 97; Low 131; Informational 41 |
| Severity by unique types | High 1; Medium 3; Low 2; Informational 4 |

Evidence: [scan record](../evidence/test-suite-20261008T065601Z/zap/scan-record.json), [effective active policy](../evidence/test-suite-20261008T065601Z/zap/effective-active-policy.json), [installed add-ons](../evidence/test-suite-20261008T065601Z/zap/autoupdate-installedAddons.json), [installed active rules](../evidence/test-suite-20261008T065601Z/zap/installed-active-rules.json), [authentication verification](../evidence/test-suite-20261008T065601Z/regression/zap-auth-verification.json), and [spider response coverage](../evidence/test-suite-20261008T065601Z/zap/spider-coverage.json).

### Scanner interpretation and counting

The count of 270 is the number of exported ZAP alert records. The inventory groups these into 10 names/plugin IDs. Several records affect related URLs or repeated responses; they are not treated as 270 independent defects. The sanitized inventory contains affected URLs and stable alert/message IDs. Scanner severity and confidence are reported as assigned by ZAP, rather than converted into invented CVSS scores. Investigation uses these statuses:

- **Confirmed:** observations establish the stated condition; unproven impact remains explicitly limited.
- **False positive:** contradictory evidence or an inapplicable prerequisite is documented.
- **Unresolved:** reproduction, prerequisites, authentication, or coverage are insufficient to settle the claim.

| ZAP alert / plugin | Severity; records | Classification and investigation |
|---|---|---|
| SQL Injection / `40018` | High; 1 | **Confirmed**, Medium scanner confidence. `/search`, parameter `q`; raw SQL interpolation and replay's 1/12/0 comparison independently confirm SS-02. The stronger SQL pass detected it; no database write or code execution is established. |
| Missing Anti-clickjacking Header / `10020` | Medium; 43 | **Confirmed**, SS-03. Home, catalogue, customer, and admin HTML responses omit framing protection. Header replay and the successfully embedded catalogue establish the stated condition. |
| Content Security Policy Header Not Set / `10038` | Medium; 53 | **Confirmed header omission**, related to SS-03. CSP is absent on HTML/error responses. Lack of a broader CSP is a hardening observation; this does not itself establish an XSS exploit. |
| Vulnerable JS Library / `10003` | Medium; 1 | **Confirmed affected component**, SS-04. The local jQuery 3.4.1 asset is active and covered by the advisory. Browser exploitation and its untrusted-HTML prerequisite are not demonstrated. |
| Server Leaks Version Information via Server Header / `10036` | Low; 71 | **Confirmed additional environment observation.** Werkzeug's local development server exposes `Werkzeug/3.1.9 Python/3.14.3` on application, asset, and error responses. This supports fingerprinting; no vulnerable server exploit is established. |
| X-Content-Type-Options Header Missing / `10021` | Low; 60 | **Confirmed additional header-hardening observation**, within the deliberately omitted-header configuration. `nosniff` is absent on HTML and local assets. No MIME-confusion exploit was demonstrated. |
| User Controllable HTML Element Attribute (Potential XSS) / `10031` | Informational; 9 | **Unresolved as potential XSS**, Low scanner confidence. Eight category records and one search record identify reflection hotspots, not script execution. Source review finds category selection restricted to existing option values and search text autoescaped in a quoted input value. No executable sink or context-break reproduction was established; retain for targeted review rather than counting it as confirmed XSS. |
| Session Management Response Identified / `10112` | Informational; 26 | **Confirmed informational identification**, not a vulnerability. The scanner recognized the intended session cookie; token presence alone is not session compromise. Cookie flags, session transitions, and CSRF received separate checks. |
| Authentication Request Identified / `10111` | Informational; 5 | **Confirmed informational identification**, not a vulnerability. These are expected local login requests used for normal authentication and verified scan sessions. |
| Information Disclosure — Suspicious Comments / `10027` | Informational; 1 | **False positive as sensitive disclosure.** The match is the public jQuery implementation keyword `username` in its XHR configuration, not an application credential or private comment. The outdated-library concern is already separately recorded. |

There is **no separate ZAP alert proving SS-01**. Its manual two-customer comparison is necessary because a scanner reaching an order page cannot infer ownership from an HTTP 200 response alone. The three header alert types relate to the deliberately omitted-header configuration but describe distinct conditions; the server banner is an additional environment observation. None was silently discarded to force a four-alert total.

For the two additional low-risk observations, **What** is the missing `nosniff` header or explicit server banner; **Where** is the affected response inventory; **Why** is the deliberate absence of added security headers or Werkzeug's development-server behavior; **Impact** is a possible MIME-hardening gap or easier stack fingerprinting, without demonstrated exploit; **Evidence** is the exported alert inventory, response-derived server version, and corresponding source configuration. Any hardening change remains future work.

Evidence: [sanitized alert records](../evidence/test-suite-20261008T065601Z/zap/alerts-sanitized.json), [grouped alert inventory with affected URLs](../evidence/test-suite-20261008T065601Z/zap/alert-inventory.json), [machine-readable classifications](../evidence/test-suite-20261008T065601Z/zap/alert-classifications.json), and [observed URLs](../evidence/test-suite-20261008T065601Z/zap/observed-urls.json). Cookies, credentials, CSRF values, API keys, raw attacks, and response bodies are omitted from shared exports; nonordinary query values are represented as `[scanner-input]`. Exact requests remain in the private Git-ignored local ZAP session. A missed scanner alert does not negate manual proof, and this assessment cannot guarantee that only four defects exist.

## 7. Preservation, limitations, and next phase

Final preservation was checked at **12:45:28 IST**. The original database's before/after SHA-256 was identical; the original application was restored at `127.0.0.1:8080` with debug disabled, and its anonymous health response returned 200. The temporary fixture and clone server were stopped. Tracked application source remained unchanged, the original `vulnerable` tag still points to `d347eb7c2404001fae0a2f43706be6e682afc7d4`, and the private completed ZAP session was saved while preserving the previous session. Historical baseline and UI-quality evidence were preserved; current artifacts were written to the new assessment directory. Evidence: [restoration record](../evidence/test-suite-20261008T065601Z/restoration.json).

The post-scan clone still had the fresh seed's three users, 12 products, empty cart, six orders, and six order items, with no foreign-key violations and SQLite integrity `ok`. This supports the bounded GET scan's data-preservation claim. It is distinct from proving that arbitrary injection could never mutate a database. Evidence: [post-scan database check](../evidence/test-suite-20261008T065601Z/zap/post-scan-database.json).

The results establish the tested normal journeys and specific control behavior on Python 3.14.3/macOS and Chromium. They do not establish compatibility with every Python 3.11+ environment, exhaustive browser coverage, full WCAG conformance, independent blind discovery, or comprehensive application security. ZAP deliberately excludes mutation workflows from automation; those workflows received functional and isolated control tests rather than unrestricted scanner coverage. The affected jQuery component is documented without claiming a browser exploit.

Instructor stack approval remains unverified. The moderate accessibility observation, 11 incomplete contrast instances, and low-confidence potential-XSS hotspot remain open for review. ZAP used a traditional spider rather than an AJAX spider, 14 selected active rules, and only four GET route families for active testing. Role-specific crawl coverage is verified, but complete authenticated attack coverage is not claimed. After a separate start instruction, a remediation phase can fix each deliberate issue, preserve per-fix commits and a fixed tag, rerun the same validation and normal journeys, and produce before/after scan evidence. None of those fixes or retests has been performed in this assessment.

## 8. Evidence index

| Evidence | Main purpose |
|---|---|
| [Assignment requirements](../evidence/test-suite-20261008T065601Z/assignment-requirements.md) | PDF page/section mapping and assignment boundaries |
| [Regression summary](../evidence/test-suite-20261008T065601Z/regression/regression-summary.json) | Counts, environment, control coverage, source state, harness history |
| [Fresh-clone summary](../evidence/test-suite-20261008T065601Z/regression/fresh-clone-summary.json) | Installation, seed, isolation, and original-database preservation |
| [Clean smoke provenance](../evidence/test-suite-20261008T065601Z/smoke/clean-run-record.json) | Three independently reset normal journeys |
| [Timestamped replay](../evidence/test-suite-20261008T065601Z/replay/replay-20261008T070624147663Z.txt) | Four deliberate weakness observations |
| [Browser results](../evidence/test-suite-20261008T065601Z/browser/browser-results.json) | Functional, responsive, accessibility, network, console, and screenshot records |
| [ZAP scan record](../evidence/test-suite-20261008T065601Z/zap/scan-record.json) | Completed scan configuration, roles, phases, timestamps, request/counting boundaries |
| [ZAP policy](../evidence/test-suite-20261008T065601Z/zap/effective-active-policy.json) | Effective enabled/disabled checks |
| [ZAP authentication verification](../evidence/test-suite-20261008T065601Z/regression/zap-auth-verification.json) | Successful private sessions and appropriate customer/admin response checks |
| [ZAP alert inventory](../evidence/test-suite-20261008T065601Z/zap/alert-inventory.json) | Ten alert types, 270 records, severity and affected URL grouping |
| [ZAP alert classifications](../evidence/test-suite-20261008T065601Z/zap/alert-classifications.json) | One investigation/status per alert type, with bounded impact and prerequisites |
| [Sanitized ZAP alerts](../evidence/test-suite-20261008T065601Z/zap/alerts-sanitized.json) | Alert IDs, plugin IDs, confidence, descriptions, affected paths; sensitive fields omitted |
| [Final preservation](../evidence/test-suite-20261008T065601Z/restoration.json) | Original database/source/tag and restored-server verification |
| [Dependency inventory](dependency-inventory.md) | Versions, official sources, CVE, and prerequisites |
| [Vulnerability matrix](vulnerability-matrix.md) | Intentional issue locations, mappings, impact, and future fixes |

The PDF source is **RED TEAM / APPLICATION SECURITY ASSIGNMENT.pdf**, eight pages, supplied by the user. Primary external sources used for the dependency finding are the [official jQuery download page](https://jquery.com/download/) and [maintainer CVE advisory](https://github.com/jquery/jquery/security/advisories/GHSA-gxr4-xjj5-5px2). The result is a completed bounded baseline assessment with documented unresolved observations; it is not a remediation result or a claim that the full Build → Attack → Identify → Fix → Retest assignment is finished.

## 9. Shareable report and normal check commands

The [PDF report](../output/pdf/SecureShop_Test_Report.pdf) is a ten-page summary with screenshots and scan/finding tables. The [evidence manifest](../evidence/test-suite-20261008T065601Z/manifest-sha256.json) records SHA-256 checksums; private scan sessions and signing keys are excluded.

For a fresh clone, create a virtualenv, install `requirements.txt`, run `python seed.py`, then `python app.py`. In a second terminal run `python tools/smoke.py` for the normal journey or `python tools/replay.py` for the agreed observations. Stop the app before resetting the database and repeat smoke from a fresh seed for each clean demo. Existing regression tests run with `python -m unittest discover -v`; optional Ruff checks use the pinned `requirements-dev.txt`. The additional isolated checks are preserved as `regression/focused-helper-source.txt` in the evidence directory.

To repeat equivalent ZAP coverage, use Protected mode and the exact saved include/exclude rules, configure form authentication and recognized `csrf_token` handling, verify each role first, keep form submission disabled during crawling, and use the 14-rule policy with non-recursive GET targets recorded in `zap/scan-record.json`. This assessment did not run AJAX spider or unrestricted active scanning. Preserve each new run in a separate evidence directory.
