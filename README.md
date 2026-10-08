# SecureShop

Local faculty assignment: Build → Attack → Identify → Fix → Retest.

## Setup and run

Python 3.11 or newer. From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
```

Open http://127.0.0.1:8080. Direct execution always uses that address and port with debug and reload off.
No external services or external runtime assets are used.

Stop the server before resetting. `python seed.py` recreates the known synthetic state.
Passwords are freshly hashed on each reset; record IDs and application data stay deterministic.

## Synthetic demo credentials

| Username | Password | Role |
|---|---|---|
| customer_a | CustomerA!2026 | Customer |
| customer_b | CustomerB!2026 | Customer |
| admin | AdminDemo!2026 | Administrator |

All emails use the reserved `.invalid` domain. Orders 1–3 belong to customer_a; 4–6 belong to customer_b.
Money is stored as integer paise and displayed as rupees.

The signing key is generated locally in Git-excluded `.instance/session.key`. Database, virtualenv, and private runtime files are excluded from Git.
The `Secure` cookie attribute is disabled for this loopback HTTP lab; HttpOnly and SameSite=Lax are explicit.

## Customer and administrator journeys

- Customer: register → sign in → search → product → add to cart → remove or place a demo order → order history → sign out.
- Administrator: open `/admin/login` → create, edit, or delete a product → inspect `/admin/users` → sign out.
- `/admin/login` is the confirmed public exception. Every management route enforces the database admin role.
- Registration accepts synthetic `.invalid` email addresses only and always creates a customer account.
- Catalogue category filtering and AJAX Add to cart use local **jQuery 3.4.1**. Without JavaScript, ordinary cart forms still work.
- Product prices are entered in rupees, stored as integer paise, and used by the server to calculate checkout totals.
- Referenced products cannot be deleted, preserving carts and historical order prices. Create an unused demo product to demonstrate deletion.
- All mutation routes use POST and server-validated CSRF. The shared login throttle allows five failed attempts per minute; restart or wait a minute if it is reached during a manual demonstration.

## Four controlled weaknesses

| Finding | Intentional location | Observation |
|---|---|---|
| A01 Broken Access Control | `routes/customer.py`, order detail | customer_a can view customer_b's seeded order 4; history remains owner-filtered |
| A03 Injection | `routes/public.py`, search | raw search input changes a single SELECT's predicate |
| A05 Security Misconfiguration | `app.py`, response hook | HTML lacks CSP framing protection and X-Frame-Options; no additional security headers are added |
| A06 Outdated Component | `templates/public/catalogue.html` | catalogue loads local jQuery 3.4.1, within CVE-2020-11022's affected range |

Each location has an `INTENTIONAL` comment. See [the vulnerability matrix](docs/vulnerability-matrix.md) for impact, validation, and **planned** fixes.
No application secure-mode switch or remediation implementation exists in this baseline.
The latest jQuery version confirmed on 2026-10-08 was **4.0.0**, from [the official download page](https://jquery.com/download/).
Its local full build is stored for the later fix phase and is not referenced by any application page.
[The dependency inventory](docs/dependency-inventory.md) records the advisory, exploitation prerequisites, and package versions.
The application avoids untrusted HTML sinks; loading 3.4.1 does not establish browser exploitation of the CVE.

## Validation helpers

With the application running in one terminal, use a second terminal in this directory:

```sh
source .venv/bin/activate
python tools/replay.py
python tools/smoke.py
```

Replay performs only the agreed order-detail check, one harmless search comparison, response-header observations, and the loaded-library observation.
It refuses any target other than `http://127.0.0.1:8080`, checks redirects, and ignores environment proxies.
The same script can be run unchanged after later remediation; it records observations rather than asserting that weaknesses must remain present.
Its logs are saved to `evidence/baseline/replay-<UTC timestamp>.txt`. Console timestamps include Asia/Kolkata.
It prints no passwords, session cookies, CSRF values, or signing keys.

Smoke walks the normal customer and administrator journeys. It **changes the synthetic database** by registering a user and placing an order.
Stop the app, run `python seed.py`, and restart it before each clean demo or any later scan.
The manual checklist is in [docs/smoke-checklist.md](docs/smoke-checklist.md); the full demo must pass three clean runs.

For the plain local iframe fixture only, serve the tools directory in a third terminal:

```sh
python -m http.server 9000 --bind 127.0.0.1 --directory tools
```

Open `http://127.0.0.1:9000/iframe_test.html`. The vulnerable catalogue should be visible inside the frame.
The fixture uses no overlay, deceptive controls, or scripts. Stop the fixture server when finished.

Verify downloaded asset integrity from the vendor directory:

```sh
cd static/vendor/jquery
shasum -a 256 -c SHA256SUMS
```

## Checkpoint and evidence

The four build stages are committed separately on `codex/vulnerable-baseline`; the completed checkpoint is tagged **`vulnerable`**.
Check the recorded source commit and working-tree status in validation logs when comparing results.
Baseline evidence belongs in `evidence/baseline/`. `evidence/final/` contains only its placeholder at this gate.
Recorded outcomes and their limits are in [the baseline validation summary](evidence/baseline/validation-summary.md).
This project stops here: no fixes, ZAP installation/run, automated security scan, or external-target testing is included.
The absence of HTTPS-only cookie attributes and additional security headers may create later lab alerts; investigate and classify them rather than claiming zero alerts.

## Design shortcuts

Single-process local Flask server, raw SQLite, fixed seed data, four catalogue categories, read-only profiles, and simulated checkout.
There is no payment, shipping, email, cloud integration, frontend framework, or separate API service.
The HTML returned to AJAX is parsed in an inert document; only text is inserted into the visible page.
Application error pages are generic, templates are autoescaped, password hashes are never listed, and all other user-input SQL uses parameters.
