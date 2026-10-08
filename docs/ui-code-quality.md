# SecureShop UI and code quality checkpoint

This work lives on `codex/ui-code-quality`. It improves the local storefront and
maintainability while retaining the assignment's four deliberate weaknesses.
The original `vulnerable` tag still points to
`d347eb7c2404001fae0a2f43706be6e682afc7d4`; its source and evidence are preserved.
No remediation, ZAP run, security scan, or external-target testing is included.

## Storefront and interaction changes

- Warm ivory and forest-green styling, editorial headings, reusable spacing and
  responsive layouts across public, customer, and administrator pages.
- Seventeen project-authored local SVG illustrations: 12 seeded products, four
  collection fallbacks for newly created products, and a desk hero illustration.
  No runtime image downloads or third-party fonts are required.
- Shared Jinja macros for CSRF fields, trusted inline icons, status labels, and
  administrator navigation. Product names and other data remain autoescaped;
  no `safe` filter is applied to user data.
- A single mobile navigation menu with an expanded-state indicator and Escape
  handling, labelled password visibility buttons, and product-delete
  confirmation. Forms retain their ordinary server-rendered behavior.
- Collection links initialize the catalogue filter. Category filtering, AJAX
  cart submission, feedback, and cart-count updates still use the local
  **jQuery 3.4.1** asset. The empty filter state and feedback are explicit.
- Illustrated cart rows with a summary sidebar, order cards and line-item
  summaries, a profile overview, and readable product/user management cards.
  Synthetic-data notices remain concise; no payment or delivery service was
  added.

## Shared application code

- Credential verification, database-role authorization, and the login throttle
  are centralized in `auth.py`. Failed-attempt state belongs to an individual
  Flask app instance instead of a module-global dictionary.
- Money formatting uses integer paise throughout, including display formatting;
  no binary floating-point conversion is needed. Dates and local illustration
  selection use shared presentation helpers.
- Catalogue categories and form limits are shared between validation and
  templates. Cart-count lookup is reused by navigation and AJAX feedback.
- Test configuration is applied before local signing-key initialization, so an
  explicit test key does not require creating the normal private key file.
- Invalid Host headers now return the intended HTTP 400 response. Their error
  handling avoids rendering navigation before a URL adapter is available.

The app still binds only to `127.0.0.1:8080` with debug/reload off. Registration
always creates a customer; passwords are hashed, POST forms require CSRF, and
management routes authorize the database role. Checkout still calculates totals
server-side and updates stock/order/cart data atomically. Referenced-product
deletion remains blocked.

## Deliberate weaknesses remain

| Finding | Retained behavior |
|---|---|
| A01 Broken Access Control | Logged-in order detail loads by ID without ownership verification; order history remains owner-filtered. |
| A03 Injection | The one product-search SELECT still interpolates raw search input. |
| A05 Security Misconfiguration | HTML still omits CSP framing protection, X-Frame-Options, and additional security headers. |
| A06 Outdated Component | Catalogue pages still load local jQuery 3.4.1; the 4.0.0 asset remains unreferenced. |

The intentional comments, route contracts, CSRF fields, and validation-script
markers are preserved. Component presence is recorded without claiming browser
exploitation of CVE-2020-11022. Planned fixes remain in
[the vulnerability matrix](vulnerability-matrix.md).

## Verification and evidence

[The final development checks](../evidence/ui-quality/development-checks.txt)
record **18 passing regression tests** in 4.953 seconds, passing Ruff lint and
formatting checks, and no broken Python requirements. Local JavaScript syntax
checks also passed. It uses temporary databases and explicit test keys;
it does not reset or modify the live lab database. The checks cover account
validation and roles, generic login failures, CSRF and POST-only actions,
owner-scoped carts, stock and checkout totals, admin CRUD, history filtering,
local configuration, exact currency formatting, local image paths, and throttle
isolation. These are regression tests, not vulnerability-scanning results.

Run from the project directory with the virtualenv activated:

```sh
pip install -r requirements-dev.txt
python -m unittest discover -v
ruff check .
ruff format --check .
```

Ruff 0.16.10 is a pinned development dependency. With Node.js available, optional
script syntax checks are:

```sh
node --check static/js/site.js
node --check static/js/catalogue.js
```

[Browser checks](../evidence/ui-quality/browser-checks.json) record **74
page/viewport inspections**: six public, four customer, and four administrator
pages at widths 320, 375, 768, 1024, and 1440 pixels, plus four capture
inspections. The inspected pages returned HTTP 200, with no horizontal overflow,
broken images, or POST forms missing their CSRF fields. Browser functional
checks passed for sign-in, password visibility, the mobile menu and Escape
handling, live category filtering and category links, AJAX add-to-cart, checkout,
and administrator create/edit/delete. The run recorded no console/page errors
or external requests. This first browser pass preceded the final accessibility
label and contrast refinements; the adjusted source is covered separately below.

[The quality-branch replay](../evidence/ui-quality/replay-20261008T062547610483Z.txt)
records foreign-order disclosure, search counts of 1/12/0, absent framing
headers, and the local jQuery 3.4.1 reference. All four deliberate behaviors
remain; component loading does not establish exploitation of the jQuery CVE.
Three consecutive normal smoke journeys also passed in an isolated temporary
database. These were sequential runs against the same initially seeded test
database, rather than three independently reset demonstrations.

[The final accessibility check](../evidence/ui-quality/accessibility-checks.json)
ran axe-core 4.14.0 against a fresh process serving the adjusted source. Across
**45 page states**, it detected zero violations at any severity, horizontal
overflow, runtime errors, external requests, or navigation retries. Its coverage
includes 11 pages at desktop/mobile widths, six public pages at 320 pixels, and
menu variants; the artifact records viewports, selected WCAG/best-practice tags,
and a source-file fingerprint.

Axe left **28 incomplete rule instances, all for color contrast**, requiring
manual review. These can include multiple elements; reported targets include
headings, product-art labels, the search field, badges, and account/admin text.
The selectors and review details remain in the artifact. Zero detected
violations therefore does not establish a complete accessibility assessment.

[The capture refresh](../evidence/ui-quality/capture-refresh.json) records 12
screenshots after the contrast and landmark corrections. A subsequent link-name
refinement changed hidden context and ARIA labels only; the final accessibility
run verifies that refinement separately. All 12 catalogue illustrations decoded
successfully during the refresh. The recorded browser, page sets, and widths
define the coverage of these checks.

These results describe the quality branch's **working tree before commit**.
The QA used isolated temporary/copied databases. After its server stopped, the
original `shop.db` SHA-256 matched its pre-QA value; the temporary QA database
was deleted. The normal app was then started at `127.0.0.1:8080` with debug off.

New artifacts are stored in `evidence/ui-quality/`. Original
`evidence/baseline/` artifacts describe the original vulnerable-tag UI and remain
preserved; `evidence/final/` has no remediation results.

The existing replay and smoke helpers retain their default baseline-output
location. Preserve old files, then copy newly generated quality-branch logs into
`evidence/ui-quality/`. The normal smoke journey changes synthetic shop data;
follow the documented stop/reset/restart sequence when preparing a clean demo.
`evidence/final/` remains reserved for an authorized remediation phase.
