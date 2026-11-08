# Argument Lab - Autonomous Systems Assignment 03

[![Project checks](https://github.com/Jatin-Purbia/autonomeous_assign_03/actions/workflows/ci.yml/badge.svg)](https://github.com/Jatin-Purbia/autonomeous_assign_03/actions/workflows/ci.yml)

A local application for abstract and strategic argumentation, with an interactive attack graph, exact semantics, exhaustive truthfulness checks, seeded experiments, and desktop/mobile browser tests.

Built for college evaluation with separate domain, application, validation, job-management and HTTP layers. See [architecture and readiness](docs/ARCHITECTURE.md) for the module boundaries and engineering decisions.

## Run

Requires Python 3.10+ (tested with 3.12.4). **The application has no external Python dependencies and needs no internet connection.**

Clone the repository first, or extract the submission ZIP:

```powershell
git clone https://github.com/Jatin-Purbia/autonomeous_assign_03.git
cd autonomeous_assign_03
```

```powershell
python server.py
```

Open **http://127.0.0.1:8000**. On Windows you can also double-click `run.bat`. Stop with Ctrl+C. If the port is occupied, use `python server.py --port 8001`. No account or API key is needed. This is a local coursework application; it is not cloud-deployed.

For request logging, run `python server.py --verbose`. `GET /api/health` returns readiness and the application version.

## What is included

- Framework studio: custom arguments/attacks, directed SVG graph, node selection, JSON import/export.
- Conflict-free, defence, characteristic function, admissible and complete-set checks.
- Grounded, all complete, preferred, stable, and semi-stable extensions.
- All legal in/out/undec labellings and semantics-specific acceptance status.
- Strategic playground: ownership, revealed subsets, induced grounded outcome, utilities, all tied best responses.
- Theorem 5.3: exhaustive dominance check with an explicit profitable-deviation witness.
- Theorem 5.4: separately reported structural condition with a cycle-safe odd-walk witness.
- Seeded experiments with progress, CSV/JSON evidence, and saved-instance inspection.
- Exact textbook fixtures, report, genuine recorded browser demonstration, screenshots, unit/API tests and Playwright E2E tests.

## Tests

Run the Python suite (no test dependency installation):

```powershell
python -m unittest discover -s tests -v
```

The suite checks the textbook and edge cases, API validation, independent total-labelling semantics on **all 512 directed three-node graphs**, and an independent strategyproofness oracle on those graphs. Self-attacks are included in this exhaustive graph space.

For browser tests, install Node.js 20+ and run:

```powershell
npm ci
npx playwright install chromium
npm run test:e2e
npm run test:e2e:report
```

Playwright starts and stops its own test server on port 8137. It runs desktop and mobile Chromium projects. Use an existing browser if browser downloads are unavailable:

```powershell
$env:E2E_BROWSER_PATH = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
npm run test:e2e
```

The generated HTML report is `playwright-report/index.html`; machine-readable results are `results/e2e-results.json`. Failed tests retain traces and screenshots under `test-results/`. The separate demo recorder captures video. Submitted screenshots are in `docs/screenshots/`.

GitHub Actions runs the Python suite and full saved-result audit on Linux (Python 3.10/3.12) and Windows (Python 3.12), plus desktop/mobile Chromium E2E on Linux. Run artifacts retain the verification output. Local verification is documented in [TESTING.md](TESTING.md); the badge reflects the actual hosted workflow status.

## Experiments

The submitted run contains **5,000 instances: 1,000 per p**, for p = 0.1, 0.3, 0.5, 0.7, 0.9, seed 2026. The pasted brief omitted the p values; these are explicit provisional choices, not claimed instructor-specified values. The textbook was supplied and its examples are implemented exactly using ASCII `a1` for alpha_1.

```powershell
python -m argumentation.experiments --count 1000 --seed 2026
python scripts/audit_results.py
```

Custom configuration:

```powershell
python -m argumentation.experiments --count 1000 --probabilities 0.1 0.2 0.4 --seed 42 --output results/custom
python -m argumentation.experiments --count 1000 --self-attacks --output results/with-self-attacks
```

Each instance has a uniformly sampled argument count in {6,7,8}. Each ordered attack is included independently with probability p. Default excludes self-attacks but allows arbitrary directed cycles. Each argument is independently assigned to one of three agents, rejecting assignments with an empty agent. This is uniform over surjective assignments, not uniform over possible size vectors. The same seeded PRNG stream continues across probability groups, so changing their order changes subsequent samples.

`results/experiments.json` retains every framework, ownership partition, both checks, and manipulation witnesses. `summary.csv` contains aggregate results; `condition_counterexamples.json` contains all sufficient-condition violations (empty in the submitted run); `converse_examples.json` contains every strategyproof instance whose structural condition fails. `independent-audit.json` verifies all 5,000 decisions through a separate bitmask algorithm and records example-by-example utility audits.

Browser experiments run in a background thread with polling, permit one active job and retain up to five jobs in memory. Refreshing the browser does not save newly generated results to disk; download JSON to preserve them. CLI runs write the submitted result files. The browser's “Load submitted 5,000 trials” reads the default `results/experiments.json`.

## Python API

```python
from argumentation import ArgumentationFramework, GroundedMechanism
from argumentation.api import grounded_direct_mechanism

af = ArgumentationFramework(['a', 'b', 'c'], [('a', 'b'), ('b', 'c')])
assert af.is_conflict_free({'a', 'c'})
assert af.defends({'a'}, 'c')
assert af.characteristic({'a'}) == {'a', 'c'}
assert af.grounded_extension() == {'a', 'c'}

m = GroundedMechanism(af, {'x': ['a'], 'y': ['b'], 'z': ['c']})
print(m.outcome({'x': ['a'], 'y': ['b'], 'z': ['c']}))
print(m.best_responses('x', {'y': ['b'], 'z': ['c']}))
print(m.theorem_53())
print(m.theorem_54_condition())
print(grounded_direct_mechanism(af.attacks, [{'a'}, {'b'}, {'c'}]))
```

Functional entry points for each extension type are also available in `argumentation/api.py`. Sets returned by the engine are `frozenset`; web output serializes them as sorted lists.

## Requirement mapping

| Assignment requirement | Implementation |
| --- | --- |
| Framework class | `ArgumentationFramework` in `engine.py` |
| Conflict-free / defence / F(S) | `is_conflict_free`, `defends`, `characteristic` |
| Admissibility / completeness | `is_admissible`, `is_complete` |
| Grounded / complete / preferred / stable / semi-stable | Separate methods in `engine.py`, functional adapters in `api.py` |
| Legal labellings / acceptance | `legal_labellings`, `acceptance_status` |
| Grounded direct mechanism | `GroundedMechanism.outcome`, `api.grounded_direct_mechanism` |
| Best response enumeration | `GroundedMechanism.best_responses` |
| Theorem 5.3 | `check_strategyproof`, `theorem_53` |
| Theorem 5.4 condition / cycles | `theorem_54_condition` |
| Random instances / results | `experiments.py`, `results/` |
| Textbook tests | `BookTests` in `tests/test_engine.py` |
| E2E | `tests/e2e/application.spec.js` |
| Report / demonstration | `REPORT.md`, `output/pdf/assignment-03-report.pdf`, `DEMONSTRATION.md`, `docs/demonstration/argument-lab-demo.webm` |

## Design conventions and limits

- Semi-stable maximizes range **by set inclusion**, not by cardinality. Preferred also uses set inclusion.
- Legal labellings mean complete labellings satisfying both iff rules in textbook Definition 5.6. `in_` is the JSON/Python field name for the in set.
- Skeptical status is displayed before credulous status to make the UI categories exclusive. A skeptical argument is also credulously accepted in the usual inclusive definition.
- If no stable extension exists, stable acceptance is **undefined (no extensions)**. We avoid vacuous universal acceptance.
- Theorem 5.4 uses odd **directed walk** reachability: vertices may repeat. BFS uses `(vertex, parity)` states and includes same-endpoint odd cycles by default, following the unrestricted quantified pair in the theorem. This conservative convention is stated explicitly because “path” can instead mean a simple path. `include_self=False` exposes the distinct-pair variant; it is not used for submitted results. A failed sufficient condition never substitutes for the exhaustive check.
- Exact enumeration is exponential. Graphs are capped at 12 arguments; requested experiment graphs have 6–8. The browser caps experiments at 1,000 per probability; CLI at 10,000. No claim of scalability to large argumentation networks is made.
- Ownership must be disjoint and cover the framework. Reports may only contain owned arguments. Utility is `|grounded outcome intersect true ownership|`, never the total number of globally accepted arguments.
- No graph edits are automatically saved. Export JSON before closing. The app binds only to loopback; it is intended for a trusted local workstation, not a public server.

## Book and corrections

Gerhard Weiss (ed.), *Multiagent Systems*, second edition, MIT Press, 2013, Chapter 5. The supplied PDF is `book/multiagent-systems_compress.pdf`; printed pages 181–185 and 199–201 correspond to PDF pages 230–234 and 248–250.

Implemented fixtures cover Figure 5.1 / Examples 5.5, 5.6, 5.8; Figure 5.2 / Examples 5.7, 5.8; and Examples 5.10, 5.11. The structured-argument and dialogue-game examples elsewhere in the chapter concern other mechanisms and are outside this abstract-framework assignment.

Example 5.10's full-report utilities are **x=1, y=0, z=1**; the book swaps y/z ownership in that utility sentence. In the discussion after Example 5.11, **a6**, not a5, neutralizes the self-defeat. The UI and tests apply both corrections.

Related primary source: Rahwan and Larson, [Mechanism Design for Abstract Argumentation (AAMAS 2008)](https://cs.uwaterloo.ca/~klarson/papers/RahwanLarsonAAMAS2008.pdf). The supplied textbook is the authority for the numbered theorems; the earlier paper uses different numbering.

## Project structure

```text
argumentation/       Pure Python engine, strategy, fixtures, functional API, experiments
  webapp/            HTTP adapter, request validation, use-case services, isolated jobs
web/                Accessible HTML/CSS/JavaScript browser application
server.py           CLI entry point and local-server launch
tests/              Unit/API tests and desktop/mobile Playwright E2E tests
scripts/            Independent result audit, demo recorder, report generator
results/            Raw experiments, summaries, case notes, test evidence
docs/               Screenshots and recorded demonstration
output/pdf/         Submission report
.github/workflows/  Cross-platform Python checks and browser E2E CI
```

To regenerate the demonstration, run `npm run demo` after installing Playwright. Report regeneration uses `python scripts/build_report.py` and requires `reportlab`; it does not affect application dependencies.

Optional developer tools: `python -m pip install -r requirements-dev.txt`. Format Python with `python -m black argumentation server.py tests scripts` and frontend sources with `npm run format`. `npm run format:check` verifies the frontend conventions without rewriting files. These tools are optional for running the app and Python tests.
