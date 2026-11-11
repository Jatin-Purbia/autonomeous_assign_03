# Argument Lab

A local web application for abstract and strategic argumentation: interactive attack graph, exact semantics, strategyproofness checks and seeded experiments.

## Run the application

Requires Python 3.10+. No packages to install and no internet needed.

```powershell
git clone https://github.com/Jatin-Purbia/autonomeous_assign_03.git
cd autonomeous_assign_03
python server.py
```

Open **http://127.0.0.1:8000** in your browser. Stop with Ctrl+C.

- Port in use: `python server.py --port 8001`
- Windows shortcut: double-click `run.bat`

## Run the tests

Python tests (no installation needed):

```powershell
python -m unittest discover -s tests -v
```

Browser tests (needs Node.js 20+):

```powershell
cd web
npm ci
npx playwright install chromium
npm run test:e2e
```

## Project layout

```text
argumentation/   Python engine, strategy, experiments, web API layers
web/             Browser app (src/), Playwright tests, Node tooling
tests/           Python tests
scripts/         Result audit, report generator
results/         Saved experiment data
docs/            Report, demo guide, screenshots, demo video
server.py        Entry point
```
