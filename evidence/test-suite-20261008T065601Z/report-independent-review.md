# Independent report review

Reviewed on **8 October 2026** against tested source
`a564617796a857dd482e8fe6daa7244d92ef484b`. Scope: read-only comparison of
final evidence, the [Markdown report](../../docs/complete-test-report.md), the
[assignment map](assignment-requirements.md), and extracted text from the latest
[10-page PDF report](../../output/pdf/SecureShop_Test_Report.pdf). This review made
no application changes or scan requests.

## Data accuracy

The final structured evidence agrees internally and with the report's principal
results:

- Regression: **34 passed** (18 existing and 16 additional isolated checks).
- Normal smoke journeys: **three passed**, independently seeded with the server
  stopped before each reset.
- Browser: **24 functional passes**, **75 responsive states**, **31 axe states**,
  one moderate best-practice violation and 11 incomplete contrast-rule instances.
- ZAP: **270 exported alert records**, **10 types**; record severities High 1,
  Medium 97, Low 131, Informational 41. Unique-type severity counts are 1/3/2/4.
- Active requests: **529**, consistent with phase counts 131 + 164 + 66 + 89 + 79.
  The saved scan record identifies all as GETs to the exact loopback target.
- Final restoration records an identical original-database checksum, unchanged
  application source, the preserved original vulnerable tag, and restored server.

Counts were independently recalculated from the [alert inventory](zap/alert-inventory.json)
and compared with the [scan record](zap/scan-record.json) and
[classifications](zap/alert-classifications.json). Regression, browser, smoke, and
restoration values were checked against their saved JSON files. The report
distinguishes alert records from independent vulnerabilities and informational
metadata from confirmed weaknesses.

## Corrected claim and finding identifiers

An earlier PDF stated that the search connection was query-only. Source inspection
showed an ordinary writable SQLite connection, so that claim was flagged. The
latest PDF now accurately states that the handler constructs one SELECT and
normal `sqlite3.execute()` accepts a single statement, **while the connection is
not read-only**. Fresh extraction confirms this correction. Finding identifiers
are aligned as **SS-01–SS-04**; old F01–F04 identifiers are absent.

No further contradictory factual claim was identified within this review's scope.
The reports retain the affected-library prerequisite limit, unresolved potential
XSS/contrast review, prior builder knowledge, unverified instructor approval, and
future remediation/retest boundary. PDF text extraction is this review's check;
the root assessor separately performed the visual and margin inspection.

## Final checksum gate

The final manifest is intentionally generated **after this note**. Manifest
creation, report-link rechecking, and collection-wide checksum verification are
the root assessor's subsequent gate. This note does **not** assert that the final
manifest or checksum verification has already passed.
