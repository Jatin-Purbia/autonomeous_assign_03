"""Dung semantics. Exhaustive enumeration is intentional for small teaching graphs."""

from itertools import combinations


def powerset(items):
    items = sorted(items)
    return (frozenset(c) for n in range(len(items) + 1) for c in combinations(items, n))


class ArgumentationFramework:
    MAX_ARGUMENTS = 12

    def __init__(self, arguments, attacks):
        arguments = list(arguments)
        if any(not isinstance(a, str) or not a.strip() for a in arguments):
            raise ValueError("Arguments must be nonempty strings.")
        if len(set(arguments)) != len(arguments):
            raise ValueError("Argument names must be unique.")
        if len(arguments) > self.MAX_ARGUMENTS:
            raise ValueError("At most 12 arguments are supported by the exact solver.")
        self.arguments = frozenset(arguments)
        pairs = []
        for edge in attacks:
            if not isinstance(edge, (list, tuple)) or len(edge) != 2:
                raise ValueError("Each attack must contain a source and a target.")
            a, b = edge
            if a not in self.arguments or b not in self.arguments:
                raise ValueError(f"Unknown attack endpoint: {a} -> {b}.")
            pairs.append((a, b))
        self.attacks = frozenset(pairs)
        self.attackers = {
            a: frozenset(x for x, y in self.attacks if y == a) for a in self.arguments
        }

    def validate_set(self, values):
        values = frozenset(values)
        if not values <= self.arguments:
            raise ValueError("Set contains unknown arguments.")
        return values

    def attacked_by(self, values):
        values = self.validate_set(values)
        return frozenset(b for a, b in self.attacks if a in values)

    def is_conflict_free(self, values):
        values = self.validate_set(values)
        return not bool(values & self.attacked_by(values))

    def defends(self, values, argument):
        if argument not in self.arguments:
            raise ValueError("Unknown argument.")
        return self.attackers[argument] <= self.attacked_by(values)

    def characteristic(self, values):
        attacked = self.attacked_by(values)
        return frozenset(a for a in self.arguments if self.attackers[a] <= attacked)

    def is_admissible(self, values):
        values = self.validate_set(values)
        return self.is_conflict_free(values) and values <= self.characteristic(values)

    def is_complete(self, values):
        values = self.validate_set(values)
        return self.is_conflict_free(values) and values == self.characteristic(values)

    def grounded_trace(self):
        trace = [frozenset()]
        while True:
            nxt = self.characteristic(trace[-1])
            if nxt == trace[-1]:
                return trace
            trace.append(nxt)

    def grounded_extension(self):
        return self.grounded_trace()[-1]

    def complete_extensions(self):
        return [s for s in powerset(self.arguments) if self.is_complete(s)]

    def preferred_extensions(self):
        complete = self.complete_extensions()
        return [s for s in complete if not any(s < t for t in complete)]

    def stable_extensions(self):
        return [
            s
            for s in powerset(self.arguments)
            if self.is_conflict_free(s) and s | self.attacked_by(s) == self.arguments
        ]

    def semi_stable_extensions(self):
        complete = self.complete_extensions()
        ranges = {s: s | self.attacked_by(s) for s in complete}
        return [s for s in complete if not any(ranges[s] < ranges[t] for t in complete)]

    def extensions(self, semantics):
        methods = {
            "grounded": lambda: [self.grounded_extension()],
            "complete": self.complete_extensions,
            "preferred": self.preferred_extensions,
            "stable": self.stable_extensions,
            "semi-stable": self.semi_stable_extensions,
        }
        if semantics not in methods:
            raise ValueError("Unknown semantics.")
        return methods[semantics]()

    def legal_labellings(self):
        # Complete extensions correspond bijectively to complete/legal labellings.
        return [
            dict(
                in_=sorted(s),
                out=sorted(self.attacked_by(s)),
                undec=sorted(self.arguments - s - self.attacked_by(s)),
            )
            for s in self.complete_extensions()
        ]

    def acceptance_status(self, argument, semantics="grounded"):
        if argument not in self.arguments:
            raise ValueError("Unknown argument.")
        extensions = self.extensions(semantics)
        if not extensions:
            return "undefined (no extensions)"
        if all(argument in s for s in extensions):
            return "skeptically accepted"
        if any(argument in s for s in extensions):
            return "credulously accepted"
        return "rejected"

    def induced(self, arguments):
        arguments = self.validate_set(arguments)
        return ArgumentationFramework(
            sorted(arguments),
            [(a, b) for a, b in self.attacks if a in arguments and b in arguments],
        )

    def to_dict(self):
        return {
            "arguments": sorted(self.arguments),
            "attacks": [list(e) for e in sorted(self.attacks)],
        }
