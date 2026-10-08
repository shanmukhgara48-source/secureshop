# Dependency inventory

Inventory recorded on **2026-10-08**. Runtime packages are pinned in
`requirements.txt`; JavaScript assets are vendored locally. Package installation
and asset acquisition are setup-time operations. Serving and using the shop do
not contact external services.

## Intentional outdated component

| Component | Baseline version | Latest identified version | Why risky | Advisory / CVE | Prerequisites for exploitation |
|---|---|---|---|---|---|
| jQuery full compressed build | 3.4.1, loaded from `/static/vendor/jquery/jquery-3.4.1.min.js` | 4.0.0, confirmed from the official download page on 2026-10-08 | Falls within the advisory's affected range, `>=1.2 <3.5.0`; the first patched release was 3.5.0 | CVE-2020-11022; GHSA-gxr4-xjj5-5px2 | Untrusted HTML must reach affected jQuery DOM manipulation methods, including `.html()` or `.append()`. Library presence alone does not show that this condition exists in the shop. |

The baseline uses jQuery for live category filtering and AJAX Add to cart.
Feedback is inserted as text; HTML responses are escaped on the server and
parsed without passing untrusted HTML to jQuery DOM manipulation methods.
**No browser exploitation of this CVE is claimed.** This task verifies the
affected component, its role, and advisory prerequisites only.

The full compressed **4.0.0** build is stored at
`static/vendor/jquery/jquery-4.0.0.min.js` for the later fix phase. It is not
referenced by the vulnerable catalogue. The full build includes AJAX; the slim
build would not satisfy the feature requirement.

Primary sources:

- [Official jQuery download page](https://jquery.com/download/) identifies
  4.0.0 as the latest version at the recorded date. Recheck it on report day.
- [Maintainer advisory GHSA-gxr4-xjj5-5px2](https://github.com/jquery/jquery/security/advisories/GHSA-gxr4-xjj5-5px2)
  identifies CVE-2020-11022, affected versions, first patched release, and the
  untrusted-HTML condition.
- Official acquisition URLs:
  [jQuery 3.4.1 compressed full build](https://code.jquery.com/jquery-3.4.1.min.js)
  and [jQuery 4.0.0 compressed full build](https://code.jquery.com/jquery-4.0.0.min.js).
- `static/vendor/jquery/SHA256SUMS` records the downloaded file hashes. Compare
  that manifest when checking local file integrity; a locally recorded hash is
  not an independent security audit.

## Python packages

The following versions were verified against the local virtual environment on
2026-10-08. The latest-release/advisory investigation for this assignment is the
jQuery entry above. Other rows describe pinned runtime use and make no claim of
exhaustive vulnerability assessment or future latest-version status.

| Package | Installed and pinned version | Role |
|---|---|---|
| Flask | 3.1.3 | Server, routing, signed-cookie session integration |
| Flask-WTF | 1.3.0 | Shared server-side CSRF protection |
| Werkzeug | 3.1.9 | Password hashing/checking, request utilities, local development server |
| Jinja2 | 3.1.6 | Server-rendered templates with autoescape enabled |
| MarkupSafe | 3.0.4 | Template escaping dependency |
| itsdangerous | 2.2.0 | Signed session and CSRF token support |
| WTForms | 3.2.2 | Flask-WTF dependency |
| click | 8.5.0 | Flask command-line dependency |
| blinker | 1.9.0 | Flask signal dependency |

No ORM, frontend framework, CDN runtime reference, payment library, or external
service client is required. `tools/replay.py` uses Python's standard library.

## Runtime and local data

| Component | Observed version | Notes |
|---|---|---|
| CPython | 3.14.3 | Project requires Python 3.11 or newer; this is the runtime actually used for the baseline build. |
| SQLite | 3.51.3 | Supplied by the local Python runtime via standard-library `sqlite3`; versions can differ on another machine. |

Record Python and SQLite versions again on the demo machine. Their newest
upstream versions were not independently established by this inventory. Password
hashes are freshly salted after a reset; synthetic IDs, product values, and seed
order ownership remain deterministic.
