# Vulnerable baseline validation

Recorded on 2026-10-08. The implementation checks below ran on Stage 4's
working tree before the `vulnerable` tag. Timestamped helper logs state their
then-current HEAD (`48e7510`) and modified status rather than implying a clean
commit was tested. Python 3.14.3 and SQLite 3.51.3 were used.

## Observed deliberate weaknesses

| Check | Actual outcome |
|---|---|
| A01 | customer_a fetched customer_b's order 4: HTTP 200, foreign owner data present |
| A03 | Notebook search counts: normal 1, true comparison 12, false comparison 0 |
| A05 | CSP and X-Frame-Options absent on Home and Products; port-9000 iframe displayed the catalogue |
| A06 | Catalogue loaded local jQuery 3.4.1; category filtering and AJAX Add to cart worked |

The A06 observation confirms the affected library's presence, not exploitation
of CVE-2020-11022. Both official downloaded assets passed their recorded SHA-256
checksums; jQuery 4.0.0 remains unreferenced.

## Normal functionality

Three independent smoke runs passed after stopping the app, resetting the seed,
and restarting it. Every run used a new cookie client and registered a new
synthetic account, then completed login, ordinary search, product detail, cart
add/remove, checkout with the expected ₹498.00 total, own history/profile, and
logout. Every run also completed admin login, create/edit/delete of an unused
product, user listing, and logout.

- `smoke-20261008T054048818749Z.txt`
- `smoke-20261008T054436108400Z.txt`
- `smoke-20261008T054436905732Z.txt`

`browser-checks.json` records headless Chromium checks using the real app:
jQuery 3.4.1, three visible Study cards after filtering, AJAX cart count 1
without navigation, no horizontal overflow at widths 320, 375, and 1440, admin
pages, and permitted cross-origin iframe embedding. No browser console/page
errors or external requests occurred. The accompanying PNG files capture the
catalogue on desktop/mobile, admin product list, and iframe observation.

## Controls outside the four deliberate weaknesses

A focused independent review used isolated temporary seed databases and real
CSRF validation. These checks passed:

- Registration ignored a supplied admin role and stored a password hash.
- Order history remained owner-filtered; foreign order detail remained the
  intentional exception.
- Customer requests to every admin management route were denied, including
  POSTs with a valid customer CSRF token. The database role was authoritative.
- Missing/invalid CSRF failed across all 10 POST endpoints. Mutation-only routes
  rejected GET. Foreign cart removal left that cart unchanged.
- Quantity/stock checks and failed-checkout atomicity held. Checkout calculated
  prices and totals on the server, ignoring supplied money fields.
- Deletion of referenced products failed, product text was escaped, user lists
  omitted hashes, and malformed search errors exposed no SQL or traceback.
- Cookies retained HttpOnly and SameSite=Lax; debug was off; rendered assets
  remained local. Offline helper mocks rejected external targets and redirects.

Compilation, dependency consistency (`pip check`), and Git whitespace checks
passed. Direct server starts confirmed loopback port 8080 and debug off. These
are focused checks, not an exhaustive security assessment or a ZAP scan.

The final local database reset restored 3 users, 12 products, 6 seeded orders,
and 0 cart items. Test servers were stopped. No fixes, ZAP run, external-target
tests, or final retest evidence were produced.
