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

