"""Grounded direct mechanism with exhaustive truthfulness checks and witnesses."""

from collections import deque
from itertools import product
from .engine import powerset


class GroundedMechanism:
    def __init__(self, framework, ownership):
        self.framework = framework
        if not isinstance(ownership, dict) or not ownership:
            raise ValueError("Provide at least one named agent.")
        self.ownership = {str(i): framework.validate_set(s) for i, s in ownership.items()}
        seen = set()
        for s in self.ownership.values():
            if seen & s:
                raise ValueError("Each argument must belong to exactly one agent.")
            seen.update(s)
        if seen != framework.arguments:
            raise ValueError("Ownership must cover all arguments.")
        self.agents = list(self.ownership)
        self._outcomes = {}

    def outcome(self, reports):
        if set(reports) != set(self.agents):
            raise ValueError("Provide one report for every agent.")
        union = frozenset()
        for i in self.agents:
            report = self.framework.validate_set(reports[i])
            if not report <= self.ownership[i]:
                raise ValueError(f"{i} can only reveal its own arguments.")
            union |= report
        if union not in self._outcomes:
            self._outcomes[union] = self.framework.induced(union).grounded_extension()
        return self._outcomes[union]

    def utility(self, agent, accepted):
        if agent not in self.ownership:
            raise ValueError("Unknown agent.")
        return len(self.ownership[agent] & accepted)

    def best_responses(self, agent, others):
        if agent not in self.ownership:
            raise ValueError("Unknown agent.")
        if set(others) != set(self.agents) - {agent}:
            raise ValueError("Provide fixed reports for all other agents only.")
        rows = []
        for report in powerset(self.ownership[agent]):
            outcome = self.outcome({**others, agent: report})
            rows.append(
                {
                    "report": sorted(report),
                    "utility": self.utility(agent, outcome),
                    "grounded": sorted(outcome),
                }
            )
        best = max(r["utility"] for r in rows)
        return {
            "maximum_utility": best,
            "best_reports": [r for r in rows if r["utility"] == best],
            "all_reports": rows,
        }

    def check_strategyproof(self):
        """Truthful revelation must be a weak best response against EVERY others profile."""
        checked = 0
        for agent in self.agents:
            other_agents = [i for i in self.agents if i != agent]
            for profile in product(*(list(powerset(self.ownership[i])) for i in other_agents)):
                others = dict(zip(other_agents, profile))
                truthful = self.outcome({**others, agent: self.ownership[agent]})
                truthful_utility = self.utility(agent, truthful)
                for report in powerset(self.ownership[agent]):
                    checked += 1
                    deviation = self.outcome({**others, agent: report})
                    gain = self.utility(agent, deviation) - truthful_utility
                    if gain > 0:
                        return {
                            "strategyproof": False,
                            "comparisons": checked,
                            "witness": {
                                "agent": agent,
                                "other_reports": {i: sorted(s) for i, s in others.items()},
                                "truthful_report": sorted(self.ownership[agent]),
                                "deviation": sorted(report),
                                "truthful_outcome": sorted(truthful),
                                "deviation_outcome": sorted(deviation),
                                "truthful_utility": truthful_utility,
                                "deviation_utility": truthful_utility + gain,
                            },
                        }
        return {"strategyproof": True, "comparisons": checked, "witness": None}

    def theorem_53(self):
        return self.check_strategyproof()

    def theorem_54_condition(self, include_self=True):
        """No odd directed WALK between co-owned arguments.

        BFS in (vertex, parity) space terminates even on cycles. Repeated vertices
        are allowed: this is parity reachability, not simple-path enumeration.
        Include same-endpoint odd cycles by default (the quantified condition).
        Set include_self=False to examine the distinct-pair interpretation.
        """
        outgoing = {a: [] for a in self.framework.arguments}
        for a, b in sorted(self.framework.attacks):
            outgoing[a].append(b)
        for agent in self.agents:
            for start in sorted(self.ownership[agent]):
                queue = deque([(start, 0)])
                paths = {(start, 0): [start]}
                while queue:
                    vertex, parity = queue.popleft()
                    if (
                        parity == 1
                        and (include_self or vertex != start)
                        and vertex in self.ownership[agent]
                    ):
                        return {
                            "holds": False,
                            "interpretation": "odd directed walk; include_self="
                            + str(include_self),
                            "witness": {
                                "agent": agent,
                                "source": start,
                                "target": vertex,
                                "walk": paths[(vertex, parity)],
                                "length": len(paths[(vertex, parity)]) - 1,
                            },
                        }
                    for target in outgoing[vertex]:
                        state = (target, 1 - parity)
                        if state not in paths:
                            paths[state] = paths[(vertex, parity)] + [target]
                            queue.append(state)
        return {
            "holds": True,
            "interpretation": "odd directed walk; include_self=" + str(include_self),
            "witness": None,
        }
