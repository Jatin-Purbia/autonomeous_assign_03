# Demonstration and viva guide

## Deliverables

- Recorded real browser walkthrough: `docs/demonstration/argument-lab-demo.webm`.
- Screenshots: `docs/screenshots/desktop-studio.png`, `mobile-studio.png`, `strategic-hiding.png`, `experiments.png`.
- Live app: `python server.py`, then http://127.0.0.1:8000.
- Regenerate video: `npm ci`, `npx playwright install chromium`, `npm run demo`.

The video is a 28.8-second overview with on-screen explanations and no audio. The following script supplies speaking notes for a live 5–7 minute demonstration.

## 1. Framework and defence (one minute)

Load **Book Figure 5.1 / Examples 5.5–5.6, 5.8**. Explain that an arrow represents attack, with no assumptions about the internal content of an argument. Point out the grounded graph colors and the fixed-point trace:

`empty -> {a3,a5} -> {a1,a3,a5}`.

Enter `a3, a5` into the test set. It is conflict-free and admissible, but not complete, because it defends a1 and has not included it. Click graph nodes to modify S.

## 2. Multiple viewpoints (one minute)

Load **Book Figure 5.2 / Examples 5.7–5.8**. Show three complete extensions: `{a3}`, `{a1,a3}`, `{a2,a3}`. Preferred and stable give two extensions. Grounded is `{a3}`. Switch acceptance semantics to preferred: a3 is skeptical; a1 and a2 are credulous. Show the three complete/legal labellings.

Load **Odd cycle** briefly: stable extensions need not exist. Stable acceptance is explicitly undefined rather than vacuously accepting every argument.

## 3. Profitable hiding (one minute)

Load **Book Example 5.10** and switch to Strategic playground. Ownership is x={a1,a4,a5}, y={a2}, z={a3}. Evaluate full reports: grounded={a1,a3}, utility vector=(1,0,1), applying the book erratum.

Replace reports with:

```json
{"x":["a4","a5"],"y":["a2"],"z":["a3"]}
```

Evaluate: grounded={a2,a4,a5}, utility vector=(2,1,0). Agent x gains by hiding a1. Show the best-response table and profitable-deviation witness. Explain that the global truthfulness audit considers every other-agent report combination, not just full revelation.

## 4. Sufficient does not mean necessary (one minute)

Load **Book Example 5.11**, return to Strategic playground and evaluate full reports. Grounded={a1,a4,a5,a6}. The added a6 attacks a3 and cancels the negative effect. Show **Strategyproof / Condition fails**. The code has checked all 192 agent/deviation comparisons (3 times 2^6) and returns no profitable deviation.

The odd-walk witness demonstrates an internal indirect defeat, but a structural-condition failure cannot establish manipulation. This distinction is central to the experiment.

## 5. Experiment evidence (one minute)

Open Experiments and load submitted results. Explain the 5,000 trials, seed, 6–8 argument range, ownership distribution, and default no-self-attack policy. Show strategyproof fractions for the five p values and the zero sufficient-condition violations. Select a converse example and open it in the studio. Download the full evidence JSON.

Run a small new job with 3 instances per probability to demonstrate progress and reproducibility without waiting for the full 5,000.

## 6. Engineering verification (one minute)

```powershell
python -m unittest discover -s tests -v
python scripts/audit_results.py
npm run test:e2e
```

Explain the two independent oracles: complete labellings versus extension algorithms, and integer-mask grounded propagation versus the production set-based mechanism. The saved 5,000-instance audit reports no disagreements. Open the Playwright HTML report and mobile screenshot.

## Likely viva questions

**Why does grounded iteration start with the empty set?** It constructs the least fixed point of the monotone characteristic function, avoiding unsupported acceptance.

**Can a set defend an argument it does not contain?** Yes. Defence and membership are separate; completeness requires accepting all defended arguments.

**Why use maximal rather than largest?** Preferred extensions and semi-stable ranges are compared by set inclusion. Incomparable maximal sets may have different sizes.

**How do cycles terminate in your condition check?** Each source explores at most two parity states per vertex. Revisiting the same vertex with the same parity adds no new reachability information.

**Does an odd walk prove profitable hiding?** No. It only falsifies a sufficient structural condition. The exhaustive utility comparison determines manipulation.

**Can revealing everything tie for best response?** Yes. Strategyproofness requires weak dominance, not a unique optimum.

**What is the computational limit?** Enumeration is exponential, deliberately capped at 12 arguments for this teaching app. Experiments use 6–8. The app favors exact, auditable answers over large-scale optimization.
