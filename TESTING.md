# Verification record

Final checks executed on 8 November 2026, on Windows with Python 3.12.4, Node.js 22.23.2, and Playwright 1.65.0 / Chromium.

## Results

| Verification | Final result | Evidence |
| --- | --- | --- |
| Python unit and HTTP integration suite | 33 passed; zero failures/errors/skips | `results/python-tests.json`, `results/python-tests.txt` |
| Browser E2E: desktop 1440 x 1080 | 12 passed | `results/e2e-results.json`, `playwright-report/index.html` |
| Browser E2E: mobile iPhone 13 viewport, Chromium | 12 passed | Same Playwright evidence |
| Independent experimental strategyproofness audit | 5,000 audited; zero disagreements | `results/independent-audit.json` |
| Random experiment | 5,000 instances; 1,000 at each p | `results/experiments.json`, `results/summary.csv` |
| JavaScript syntax | Passed `node --check web/app.js` | Run command provided below |
| Visual QA | Desktop/mobile screenshots and PDF pages inspected | `docs/screenshots/`, `output/pdf/assignment-03-report.pdf` |
| Recorded demo | Playable 28.8-second VP9 WebM, 1440 x 1000, no audio | `docs/demonstration/argument-lab-demo.webm` |

The recorded video is a short overview; `DEMONSTRATION.md` supplies the longer 5-7 minute live presentation script.

## Independent checks

For every one of the 512 directed graphs on three arguments (including self-attacks), the test oracle enumerates all 27 total labellings and validates the local in/out equivalences. It compares the resulting complete extensions, undecided-set minima, and stable labellings with the production algorithms. Preferred sets are checked against maximal admissible sets; grounded is checked with an independent in/out propagation algorithm.

Strategyproofness is independently tested on the same complete 512-graph space under a fixed two-argument/singleton/empty ownership partition. Separately, the saved 5,000 random instances, each with three nonempty agents, are exhaustively audited by integer-mask propagation that imports no production engine. Every profile and deviation is compared. All 769 converse cases have per-agent maximum hiding gain 0 recorded in `all_converse_case_audits` in the audit JSON.

## End-to-end coverage

Each of these 12 scenarios runs in both desktop and mobile Chromium:

1. Textbook defence, admissibility, incompleteness, characteristic function, and fixed-point iterations.
2. Three complete extensions, three legal labellings, and semantics-specific acceptance.
3. Pointer and keyboard graph-node selection.
4. Odd cycle, absent stable extensions, and undefined stable acceptance.
5. Corrected Example 5.10 utilities and profitable hiding.
6. Example 5.11 strategyproofness despite a failed sufficient condition.
7. Invalid attack syntax/endpoints and forbidden report ownership.
8. Downloaded framework JSON and imported graph/ownership round trip.
9. Empty frameworks and self-attacks.
10. Background experiment job, progress, raw download, and saved-graph reopening.
11. Submitted 5,000-trial loading and exceptional-case filtering.
12. Responsive layout, no horizontal page overflow, runtime errors, and screenshots.

The mobile project emulates a phone viewport and input in Chromium; it is not a claim of physical iPhone or Safari testing. The app's standard-library HTTP server is tested through real requests, not mocked API responses.

The application-layer readiness suite also checks strict JSON shapes and booleans, malformed payloads, response headers, the health endpoint, job progress, concurrent-start rejection, bounded retention, isolated result snapshots, logged failure/recovery, and independent state across server instances. GitHub Actions is configured to repeat Python verification on Linux/Windows and browser tests on Linux; its hosted status is recorded by GitHub rather than assumed from local results.

## Issues found and resolved

Initial browser execution revealed that decorative navigation icons were part of accessible button names. Those spans now use `aria-hidden`, making navigation names clear and stable. Per-test video encoding also caused teardown timeouts on this workstation; the suite retains failure traces/screenshots, while video is captured once by the separate demo recorder. The subsequent full suite passed all 24 tests, including another full run against the refactored application. Exact timings are retained in the JSON evidence. No failed tests were skipped or removed.

## Reproduce

```powershell
python scripts/test_python.py
node --check web/app.js
python scripts/audit_results.py
npm ci
npx playwright install chromium
npm run test:e2e
```

To use an existing Chromium-based browser, set `E2E_BROWSER_PATH` as explained in README.md. Run `npm run test:e2e:report` to inspect the actual assertions, timings, and screenshots. A fresh suite replaces the previous machine-readable and HTML test reports.
