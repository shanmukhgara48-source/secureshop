# SecureShop browser test results

Source commit: `a564617796a857dd482e8fe6daa7244d92ef484b`. Browser: Chromium `151.0.7922.34`. Test window: 2026-10-08T07:06:48.166Z to 2026-10-08T07:07:57.882Z (UTC).

The server used the freshly seeded isolated clone at `.instance/full-suite/fresh-clone`, bound only to `127.0.0.1:8080`. Root confirmed that ZAP spider and active scans were paused during browser mutations. The separate framing fixture was `127.0.0.1:9000`. The original application database was not used. No app code, security fixes, or Git changes were made by this browser task.

| Check | Result |
|---|---|
| Normal functional checks | 24 passed; zero failures |
| Required responsive matrix | 14 route/role pages × 5 widths = 70 states passed |
| Additional populated-cart matrix | 5 states passed |
| Viewport widths | 320, 375, 768, 1024, 1440 px |
| Horizontal overflow | None in 75 states |
| Form/navigation semantics | 75 state checks passed |
| axe-core 4.14.0 | 31 states; one moderate best-practice violation; no serious/critical violations |
| Automated incomplete accessibility checks | 11 color-contrast rule instances retained for manual review |
| Focused computed contrast | 30 closed/default states; zero failures against nearest solid CSS background |
| JavaScript exceptions | Zero |
| Unexpected console errors | Zero; four expected HTTP 400/403/404 resource logs preserved |
| Failed network requests / external attempts | Zero / zero |
| Screenshots | 23 |

## Functional coverage

The normal customer journey registered a synthetic account, signed in, checked empty states, searched, viewed details, added and removed items, performed AJAX additions, checked server-calculated ₹498.00 totals, placed a simulated order, viewed history and profile, and signed out. All four category filters displayed three products each and updated the URL. A customer received a generic 403 on the administrator management route.

The administrator journey signed in, created an unreferenced synthetic product, edited its name/price/stock, deleted it, viewed the synthetic account listing without password hashes, and signed out. Core login/add/remove/logout forms also passed with JavaScript disabled.

Additional checks covered required-field and quantity validation, generic failed-login messages, invalid synthetic email rejection, empty search/filter results, generic 404 behavior, password visibility, keyboard tab order, mobile menu opening/outside-click/Escape/focus behavior, and successful catalogue embedding in the loopback iframe fixture. The embedding observation confirms the intentional framing omission; it does not claim a completed clickjacking attack.

## Accessibility finding

**Moderate best-practice finding: unnamed complementary landmarks.** At desktop `/admin/products/new`, `.admin-sidebar` and `.editor-note-card` are both unnamed `<aside>` landmarks. Axe rule `landmark-unique` reports that their accessible names should distinguish them. This is an accessibility naming issue, not an additional confirmed security vulnerability. No fix was made. Future improvement: give the two complementary sections distinct names or review whether both should be landmarks.

The best-practice tag was included in this suite; do not compare its one finding directly with earlier narrower WCAG-tag runs as if the app regressed.

## Contrast limits and visual review

The 11 automated incomplete contrast-rule instances remain incomplete in the raw results. The focused computed check found no failures across 30 closed/default page states, but it uses the nearest solid CSS background and cannot certify every pixel behind SVG-backed text. Visual review of the home, catalogue, login, open mobile menu, cart, editor, and framing screenshots found clear caption margins and readable UI text. The opaque open menu intentionally covers the underlying story text and restores access when closed. This bounded review is not a WCAG conformance claim and does not silently convert incomplete results into automated passes.

## Evidence

- [Structured browser results](browser-results.json)
- [Home](home-desktop.png), [desktop login](login-desktop.png), [mobile login](login-mobile.png)
- [Catalogue](catalogue-desktop.png), [mobile cart](cart-mobile.png), [order detail](order-detail-desktop.png)
- [Admin products](admin-products-desktop.png), [product editor](admin-product-editor.png), [user listing](admin-users-desktop.png)
- [Framing observation](framing-allowed.png)

These tests created one temporary synthetic customer and order, left a normal test item in customer A's isolated cart, and created/deleted one temporary admin product. All browser contexts were closed, and root was notified to reset the clone before security scanning. The ephemeral runner stays under ignored `.instance/`; it is ordinary functional QA rather than exploit tooling.
