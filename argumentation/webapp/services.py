"""Use cases that translate validated JSON to reasoning-engine operations."""

from argumentation import GroundedMechanism
from .validation import JsonObject, SEMANTICS, argument_list, framework_from_json, reports_from_json


def analyse(data: JsonObject) -> JsonObject:
    af = framework_from_json(data)
    values = argument_list(data.get("set", []), "set")
    semantics = data.get("semantics", "grounded")
    if semantics not in SEMANTICS:
        raise ValueError("Unknown semantics.")
    # Reuse extension results for every acceptance query in this request.
    extensions = {name: af.extensions(name) for name in SEMANTICS}
    selected = extensions[semantics]

    def acceptance(argument: str) -> str:
        if not selected:
            return "undefined (no extensions)"
        if all(argument in extension for extension in selected):
            return "skeptically accepted"
        if any(argument in extension for extension in selected):
            return "credulously accepted"
        return "rejected"

    return {
        "framework": af.to_dict(),
        "extensions": {name: [sorted(s) for s in sets] for name, sets in extensions.items()},
        "grounded_trace": [sorted(s) for s in af.grounded_trace()],
        "labellings": af.legal_labellings(),
        "set_analysis": {
            "conflict_free": af.is_conflict_free(values),
            "admissible": af.is_admissible(values),
            "complete": af.is_complete(values),
            "defended": sorted(af.characteristic(values)),
        },
        "acceptance": {a: acceptance(a) for a in sorted(af.arguments)},
        "semantics": semantics,
    }


def strategic(data: JsonObject) -> JsonObject:
    af = framework_from_json(data)
    ownership = reports_from_json(data.get("ownership"), "ownership")
    reports = reports_from_json(data.get("reports", ownership), "reports")
    mechanism = GroundedMechanism(af, ownership)
    outcome = mechanism.outcome(reports)
    agent = data.get("agent", mechanism.agents[0])
    if not isinstance(agent, str) or agent not in ownership:
        raise ValueError("Unknown agent.")
    return {
        "outcome": sorted(outcome),
        "utilities": {i: mechanism.utility(i, outcome) for i in mechanism.agents},
        "strategyproofness": mechanism.theorem_53(),
        "condition": mechanism.theorem_54_condition(),
        "best_responses": mechanism.best_responses(
            agent,
            {i: report for i, report in reports.items() if i != agent},
        ),
    }
