# Architecture and project readiness

Argument Lab is a college project built with maintainable engineering practices. It runs locally and keeps installation simple. The design separates responsibilities so that a reviewer can trace each assignment requirement to a small, testable module.

## Layers

```text
Browser UI (web/)
    | JSON over loopback HTTP
HTTP adapter (argumentation/webapp/http.py)
    | validated request shapes
Application services (services.py) / experiment job manager (jobs.py)
    | pure domain operations
ArgumentationFramework (engine.py) / GroundedMechanism (strategic.py)
    | seeded experiment orchestration
Experiments (experiments.py) -> auditable JSON / CSV
```

- `server.py` is a small CLI entry point. `--port` selects the local port; `--verbose` enables request logs.
- `webapp/validation.py` validates JSON types before the domain layer. Immutable experiment parameters prevent callers from changing an active request.
- `webapp/services.py` handles analysis and strategic use cases, reusing computed extensions for acceptance queries.
- `webapp/http.py` owns routes, JSON errors, resource lookup, payload limits, and response headers. `/api/health` provides a readiness probe.
- `webapp/jobs.py` owns locking, bounded result retention, progress, failures and snapshots. Every server gets its own manager, so test instances cannot leak state to each other.
- Domain algorithms know nothing about HTTP or the frontend. `argumentation/api.py` supplies functional adapters for the assignment.
- `scripts/audit_results.py` remains an independent implementation and imports no production reasoning code.

## Errors and lifecycle

Invalid requests return JSON with HTTP 400. Unknown routes/jobs return 404. Unexpected failures are logged and return a generic 500 message. Failed computations reach a terminal job state and allow a later run. A disconnected browser does not corrupt the job manager. Jobs live in memory and are intentionally not durable; users download results or run the CLI to save them.

## Repository readiness

- Pinned npm dependency versions in `package-lock.json`; `npm ci` reproduces the browser-test installation. Node.js 20+ is required by the installed Playwright version.
- Standard-library Python runtime; no install step for the app or Python tests.
- Cross-platform GitHub Actions: Python 3.10 and 3.12 on Linux, Python 3.12 on Windows, and desktop/mobile Chromium E2E on Linux.
- Independent graph-space and full experimental audits; failure traces and HTML browser reports.
- UTF-8, line-ending and indentation conventions in `.editorconfig` and `.gitattributes`.
- Git excludes dependencies, local caches, environment files, raw browser recordings, duplicate submission archives and the supplied textbook. Source, report, final demo, and experimental evidence are tracked.

## Evaluation boundaries

The server binds to loopback and the exact solver caps graphs at 12 arguments. These are deliberate project constraints. Durable queues, distributed workers, user accounts and a public deployment are outside the assignment. The structural Theorem 5.4 convention and provisional probability values remain documented in README.md and REPORT.md.
