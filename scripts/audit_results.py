"""Independently audit every saved strategyproofness claim using bitmask propagation.

This intentionally imports no application solver. It uses unattacked-node peeling,
then compares every agent/report/profile using integer masks.
"""

import json
from pathlib import Path
from itertools import product


def subsets(mask):
    result = [mask]
    value = mask
    while value:
        value = (value - 1) & mask
        result.append(value)
    return result


def audit(record):
    args = record["arguments"]
    index = {a: 1 << i for i, a in enumerate(args)}
    incoming = [0] * len(args)
    outgoing = [0] * len(args)
    for a, b in record["attacks"]:
        incoming[args.index(b)] |= index[a]
        outgoing[args.index(a)] |= index[b]
    outcomes = []
    for mask in range(1 << len(args)):
        remaining, accepted = mask, 0
        while remaining:
            initial = 0
            for i in range(len(args)):
                if remaining & (1 << i) and not incoming[i] & remaining:
                    initial |= 1 << i
            if not initial:
                break
            accepted |= initial
            defeated = 0
            for i in range(len(args)):
                if initial & (1 << i):
                    defeated |= outgoing[i]
            remaining &= ~(initial | defeated)
        outcomes.append(accepted)
    owners = [sum(index[a] for a in s) for s in record["ownership"].values()]
    strategyproof = True
    details = []
    for agent, own in zip(record["ownership"], owners):
        others = [s for s in owners if s != own]
        # Trials have nonempty, disjoint ownership, so mask identity is unique.
        worst_delta = 100
        maximum_gain = -100
        full_utilities = []
        for profile in product(*(subsets(s) for s in others)):
            other_union = 0
            for s in profile:
                other_union |= s
            full_u = (outcomes[other_union | own] & own).bit_count()
            best_u = max((outcomes[other_union | s] & own).bit_count() for s in subsets(own))
            full_utilities.append(full_u)
            worst_delta = min(worst_delta, full_u - best_u)
            maximum_gain = max(maximum_gain, best_u - full_u)
            if best_u > full_u:
                strategyproof = False
        details.append(
            {
                "agent": agent,
                "other_profiles": len(full_utilities),
                "truthful_utility_min": min(full_utilities),
                "truthful_utility_max": max(full_utilities),
                "maximum_hiding_gain": maximum_gain,
            }
        )
    if strategyproof != record["strategyproof"]:
        raise AssertionError(f'Independent audit disagrees on {record["id"]}')
    return details


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = json.loads((root / "results/experiments.json").read_text())
    cases = []
    all_converse_audits = []
    selected = set()
    for record in result["records"]:
        details = audit(record)
        if record["strategyproof"] and not record["condition"]["holds"]:
            all_converse_audits.append({"id": record["id"], "agent_audit": details})
        if (
            record["strategyproof"]
            and not record["condition"]["holds"]
            and record["p"] not in selected
        ):
            cases.append(
                {
                    "id": record["id"],
                    "p": record["p"],
                    "arguments": record["arguments"],
                    "attacks": record["attacks"],
                    "ownership": record["ownership"],
                    "odd_walk": record["condition"]["witness"],
                    "agent_audit": details,
                }
            )
            selected.add(record["p"])
    output = {
        "audited_instances": len(result["records"]),
        "disagreements": 0,
        "method": "Independent integer-mask in/out propagation; exhaustive profiles and deviations",
        "representative_converse_cases": cases,
        "all_converse_case_audits": all_converse_audits,
    }
    (root / "results/independent-audit.json").write_text(json.dumps(output, indent=2))
    print(f'Independently audited {len(result["records"])} instances: zero disagreements.')
