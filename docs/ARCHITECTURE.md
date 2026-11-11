# Architecture

Argument Lab is a local web application. A dependency-free Python backend computes everything exactly; a plain HTML/CSS/JavaScript frontend only displays the results.

```text
Browser (web/src)  --JSON over HTTP-->  webapp (adapter)  -->  argumentation (domain)
```

Dependencies point one way: the domain knows nothing about HTTP, and the frontend knows nothing about the algorithms.

## Layers

### Domain: `argumentation/`

Pure Python, standard library only, no I/O.

| Module | Responsibility |
| --- | --- |
| `engine.py` | `ArgumentationFramework`: conflict-free, defence, characteristic function, admissible, complete, grounded, preferred, stable and semi-stable extensions, legal labellings, acceptance status. Exhaustive enumeration, capped at 12 arguments. |
| `strategic.py` | `GroundedMechanism`: agent ownership, revealed reports, induced grounded outcome, utilities, best responses, the exhaustive strategyproofness check (Theorem 5.3) and the odd-walk structural condition (Theorem 5.4). |
| `experiments.py` | Seeded random instance generation and the batch runner that produces the saved results. |
| `examples.py` | Named fixtures (textbook figures and examples) served to the UI. |
| `api.py` | Functional wrappers around the classes, for use from scripts. |

### Application: `argumentation/webapp/`

Turns HTTP requests into domain calls.

| Module | Responsibility |
| --- | --- |
| `validation.py` | Parses and validates request JSON into domain objects. Rejects bad input with clear messages. |
| `services.py` | Use cases: `analyse` (extensions, labellings, set checks, acceptance) and `strategic` (outcome, utilities, verdicts, best responses). |
| `jobs.py` | Runs experiments in a background thread; one active job, five retained, polled by the browser. |
| `http.py` | `ThreadingHTTPServer` handler: routing, size and content-type limits, same-origin check on POST, static file serving. Binds to `127.0.0.1` only. |

`server.py` is the command-line entry point that builds and starts the server.

### Frontend: `web/`

| Path | Responsibility |
| --- | --- |
| `src/index.html`, `style.css`, `app.js` | The whole UI: framework studio, strategic playground, experiments. No framework, no build step; `server.py` serves these files directly. |
| `tests/e2e/` | Playwright tests, run on desktop and mobile viewports. |
| `scripts/demo.cjs` | Records the demonstration video and screenshots. |
| `package.json` | Development tooling only (Playwright, Prettier). Not needed to run the app. |

## HTTP API

| Route | Purpose |
| --- | --- |
| `GET /api/health` | Readiness and version. |
| `GET /api/examples` | Fixture frameworks with ownership. |
| `POST /api/analyse` | Analyse a framework and optionally a test set. |
| `POST /api/strategic` | Evaluate reports, utilities, strategyproofness, best responses. |
| `POST /api/experiments` | Start an experiment job; returns a job id. |
| `GET /api/jobs/<id>` | Poll job progress and result. |
| `GET /api/saved-experiments` | The submitted 5,000-instance results from `results/experiments.json`. |

## Data and results

`results/` holds the saved experiment output (raw records, summary CSV, counterexample lists) and the independent audit. `scripts/audit_results.py` re-verifies every saved decision with a separate bitmask algorithm.

## Testing

- `tests/test_engine.py`: textbook fixtures and edge cases; independent checks over all 512 directed three-node graphs.
- `tests/test_api.py`, `tests/test_webapp.py`: validation, HTTP behaviour, job management.
- `web/tests/e2e/`: the full UI against a real server.
- `.github/workflows/ci.yml`: runs all of the above on Linux and Windows.

## Design decisions

- **Exact, not approximate.** Every semantics is enumerated, which is why graphs are small (at most 12 arguments).
- **No runtime dependencies.** Python's standard library is enough; nothing to install, no internet needed.
- **Local only.** The server binds to loopback and is not meant to be exposed publicly.
- **Thin adapter.** All validation and orchestration lives in `webapp/`, so the domain stays testable on its own.
