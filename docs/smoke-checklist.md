# SecureShop smoke and demo checklist

This checklist is for the local vulnerable baseline. It does not run ZAP, scan
other applications, or implement remediation. Record actual outcomes; an
unchecked box is not a passing test. `tools/smoke.py` supplies a repeatable local
functional check, while browser steps verify JavaScript and presentation.

## Prepare a clean run

- [ ] Activate `.venv`, stop the existing server, and run `python seed.py`.
- [ ] Run `python app.py`. Confirm it listens only at `127.0.0.1:8080`, with debug
  and the reloader disabled.
- [ ] Open a fresh browser context at `http://127.0.0.1:8080`; keep the browser
  console and Network panel available for checks.
- [ ] Record the tested commit, date/time, Python version, and SQLite version.
- [ ] Confirm only local assets load; no CDN, analytics, or external service
  requests occur during the journey.

## Customer journey

1. [ ] Open Home, then Create account. Register `learner01` using the synthetic
   address `learner01@example.invalid` and a lab-only password of 10–128
   characters. The account must be a customer.
2. [ ] Sign in with that account. Navigation must show Shop, Orders, Cart,
   Profile, and Sign out.
3. [ ] Search for `notebook`. Confirm a matching product and a meaningful result
   count; open its product detail page.
4. [ ] Add one unit to the cart. Confirm the product, quantity, unit price, and
   total appear correctly. Remove it, verify the empty cart, then add it again.
5. [ ] Place a demo order. Confirm a new order detail, correct account, line item,
   total, date, and status; the cart must become empty and stock decrease once.
6. [ ] Open order history, then the order detail and read-only profile. They must
   show the new customer's own records and synthetic profile.
7. [ ] Sign out. Protected pages must require login and the navigation must return
   to the public state. Reload any previously open private page to confirm the
   current logged-out state.

## Catalogue JavaScript

- [ ] Sign in as `customer_a` and open `/products`. Confirm the loaded file is
  local `jquery-3.4.1.min.js`.
- [ ] Select Study, Carry, Everyday, and Tech. Each category has three seeded
  products. Return to All collections and confirm 12 visible products.
- [ ] Click Add to cart on a product. The request must be AJAX to `/cart/add`,
  include a CSRF token, and update feedback/cart count without a full navigation.
- [ ] Open Cart and confirm the same item exists. Confirm no browser console
  error during category filtering or AJAX submission.

## Administrator journey

1. [ ] Sign out, visit public `/admin/login`, and sign in as the seeded admin.
2. [ ] Open `/admin/products`. Create an unreferenced synthetic product named
   `Lab postcard`, category Study, price ₹79.00, stock 5.
3. [ ] Edit it to `Campus postcard` and ₹85.75. Confirm the catalogue reflects the
   saved values and preserves the exact two-decimal price.
4. [ ] Delete that newly created product. Confirm it disappears and the normal
   seeded catalogue remains available.
5. [ ] Open `/admin/users`. Confirm the synthetic accounts and roles appear;
   password hashes must not be displayed.
6. [ ] Sign out using the POST form.

## Controls that remain enforced

- [ ] As anonymous, customer pages require login; admin management pages direct
  to the admin login. `/admin/login` itself remains the public exception.
- [ ] As a customer, admin management GET requests return 403. Management POSTs
  with a valid customer CSRF token still return 403 and change no data.
- [ ] A POST without a valid CSRF token returns 400 and changes no data, including
  login, registration, cart, checkout, logout, and admin actions.
- [ ] GET requests to mutation-only routes return 405 and perform no action.
- [ ] Customer A's history, profile, and cart remain limited to that account.
  Removing another account's cart item is rejected and leaves it intact.
- [ ] Checkout ignores client-supplied totals/prices; totals come from stored
  product prices. Invalid quantities and insufficient stock are rejected.
- [ ] Deleting a product referenced by a cart or order is rejected with the
  explanatory message; existing records remain intact.
- [ ] Registration ignores any supplied role and requires a synthetic `.invalid`
  email. Wrong credentials give generic errors. Passwords are stored as hashes.
- [ ] User and admin-entered text is escaped, never executed as page markup.
- [ ] Session cookies retain HttpOnly and SameSite=Lax. `Secure` is deliberately
  off because this lab uses loopback HTTP; do not present that as production
  configuration.
- [ ] Errors show a generic page or message, never a traceback/debug console.

## Four controlled baseline observations

- [ ] Run `python tools/replay.py` against its fixed loopback target. Save its
  timestamped output under `evidence/baseline/`.
- [ ] A01: customer A receives customer B's order 4 with a 200 response, while
  customer A's history excludes orders 4–6.
- [ ] A03: the one harmless search comparison prints differing result counts;
  ordinary product searches still work.
- [ ] A05: framing-related headers are absent. Serve the fixture using
  `python -m http.server 9000 --bind 127.0.0.1 --directory tools` and open
  `http://127.0.0.1:9000/iframe_test.html`. The catalogue is visibly embedded.
  Stop this helper server after the observation.
- [ ] A06: the catalogue references/loads jQuery 3.4.1, matching the recorded
  checksum. jQuery 4.0.0 is stored locally but remains unreferenced. Do not claim
  CVE browser exploitation.

## Pre-demo gate

- [ ] Repeat the entire customer and administrator demo path three times from
  clean seed/browser state; record each run rather than relying on cached state.
- [ ] Confirm the chosen presentation resolution is readable and navigation
  works on every page.
- [ ] Preserve synthetic baseline evidence and a screenshot backup.
- [ ] Record any failure or additional suspected flaw separately; checks do not
  guarantee the absence of other vulnerabilities.
- [ ] Commit the baseline and create Git tag `vulnerable` only after the agreed
  checks pass. **Stop at this tag.** No ZAP scan, fixes, `fixed` tag, or final
  retest evidence is produced in this task.
