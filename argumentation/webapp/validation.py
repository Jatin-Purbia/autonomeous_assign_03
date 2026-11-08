"""Validate JSON at the boundary before invoking domain algorithms."""

from dataclasses import dataclass
from typing import Any
from argumentation import ArgumentationFramework

JsonObject = dict[str, Any]
SEMANTICS = ("grounded", "complete", "preferred", "stable", "semi-stable")


def argument_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(a, str) for a in value):
        raise ValueError(f"{field} must be an array of argument names.")
    return value


def framework_from_json(data: JsonObject) -> ArgumentationFramework:
    arguments = argument_list(data.get("arguments"), "arguments")
    attacks = data.get("attacks")
    if not isinstance(attacks, list):
        raise ValueError("attacks must be an array of [source, target] pairs.")
    for edge in attacks:
        if (
            not isinstance(edge, list)
            or len(edge) != 2
            or any(not isinstance(a, str) for a in edge)
        ):
            raise ValueError("Each attack must be a [source, target] pair of names.")
    return ArgumentationFramework(arguments, attacks)


def reports_from_json(value: Any, field: str) -> dict[str, list[str]]:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{field} must be a nonempty object mapping agents to argument arrays.")
    for agent, arguments in value.items():
        if not isinstance(agent, str) or not agent.strip():
            raise ValueError("Agent names must be nonempty strings.")
        argument_list(arguments, f"{field}.{agent}")
    return value


@dataclass(frozen=True)
class ExperimentRequest:
    """Validated experiment parameters shared by the service and job runner."""

    count: int
    probabilities: tuple[float, ...]
    seed: int
    self_attacks: bool

    @classmethod
    def from_json(cls, data: JsonObject) -> "ExperimentRequest":
        count = data.get("count", 1000)
        probabilities = data.get("probabilities", [0.1, 0.3, 0.5, 0.7, 0.9])
        seed = data.get("seed", 2026)
        self_attacks = data.get("self_attacks", False)
        if type(count) is not int or not 1 <= count <= 1000:
            raise ValueError(
                "Browser runs support 1-1000 instances per probability; use CLI for larger runs."
            )
        if (
            not isinstance(probabilities, list)
            or not 1 <= len(probabilities) <= 5
            or any(type(p) not in (float, int) or not 0 <= p <= 1 for p in probabilities)
        ):
            raise ValueError("Provide 1-5 probabilities in [0, 1].")
        if type(seed) is not int:
            raise ValueError("Seed must be an integer.")
        if type(self_attacks) is not bool:
            raise ValueError("self_attacks must be true or false.")
        return cls(count, tuple(probabilities), seed, self_attacks)
