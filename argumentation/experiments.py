"""Seeded, auditable random trials; each raw record contains the entire instance."""

import argparse
import csv
import json
import random
import time
from pathlib import Path
from .engine import ArgumentationFramework
from .strategic import GroundedMechanism


def run_experiments(
    count=1000,
    probabilities=(0.1, 0.3, 0.5, 0.7, 0.9),
    seed=2026,
    self_attacks=False,
    progress=None,
):
    if not isinstance(count, int) or not 1 <= count <= 10000:
        raise ValueError("Instances per probability must be between 1 and 10000.")
    probabilities = list(probabilities)
    if not probabilities or any(not 0 <= p <= 1 for p in probabilities):
        raise ValueError("Probabilities must be in [0, 1].")
    rng = random.Random(seed)
    records, summaries = [], []
    started = time.perf_counter()
    for p in probabilities:
        group = []
        for trial in range(count):
            n = rng.randint(6, 8)
            arguments = [chr(97 + j) for j in range(n)]
            attacks = [
                (a, b)
                for a in arguments
                for b in arguments
                if (self_attacks or a != b) and rng.random() < p
            ]
            # Uniformly assign each argument; reject until all three agents are nonempty.
            while True:
                owners = [rng.randrange(3) for _ in arguments]
                if len(set(owners)) == 3:
                    break
            ownership = {
                f"Agent {i+1}": [a for a, owner in zip(arguments, owners) if owner == i]
                for i in range(3)
            }
            af = ArgumentationFramework(arguments, attacks)
            mechanism = GroundedMechanism(af, ownership)
            strategy = mechanism.check_strategyproof()
            condition = mechanism.theorem_54_condition()
            record = {
                "id": f"p{p}-trial{trial+1}",
                "p": p,
                "n": n,
                **af.to_dict(),
                "ownership": ownership,
                **strategy,
                "condition": condition,
            }
            records.append(record)
            group.append(record)
            if progress and (trial + 1) % 25 == 0:
                progress(len(records), count * len(probabilities))
        sp = sum(r["strategyproof"] for r in group)
        summaries.append(
            {
                "p": p,
                "instances": count,
                "strategyproof": sp,
                "fraction": sp / count,
                "condition_holds": sum(r["condition"]["holds"] for r in group),
                "condition_holds_not_sp": sum(
                    r["condition"]["holds"] and not r["strategyproof"] for r in group
                ),
                "sp_condition_fails": sum(
                    r["strategyproof"] and not r["condition"]["holds"] for r in group
                ),
            }
        )
    return {
        "config": {
            "count_per_probability": count,
            "probabilities": probabilities,
            "seed": seed,
            "agents": 3,
            "n": [6, 8],
            "self_attacks": self_attacks,
            "ownership_sampling": "independent uniform assignment conditioned on all three nonempty",
            "odd_reachability": "directed walks, including same-endpoint odd cycles",
        },
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "summary": summaries,
        "records": records,
    }


def save_results(result, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "experiments.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (directory / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result["summary"][0]))
        writer.writeheader()
        writer.writerows(result["summary"])
    exceptions = [
        r for r in result["records"] if r["condition"]["holds"] and not r["strategyproof"]
    ]
    converse = [r for r in result["records"] if r["strategyproof"] and not r["condition"]["holds"]]
    (directory / "condition_counterexamples.json").write_text(
        json.dumps(exceptions, indent=2), encoding="utf-8"
    )
    (directory / "converse_examples.json").write_text(
        json.dumps(converse, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--probabilities", type=float, nargs="+", default=[0.1, 0.3, 0.5, 0.7, 0.9])
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--self-attacks", action="store_true")
    parser.add_argument("--output", default="results")
    args = parser.parse_args()
    result = run_experiments(
        args.count,
        args.probabilities,
        args.seed,
        args.self_attacks,
        lambda done, total: print(f"{done}/{total}", flush=True) if done % 500 == 0 else None,
    )
    save_results(result, args.output)
    print(json.dumps(result["summary"], indent=2))
