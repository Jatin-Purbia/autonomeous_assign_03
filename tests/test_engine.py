import itertools
import unittest
from argumentation import ArgumentationFramework as AF, GroundedMechanism
from argumentation.engine import powerset
from argumentation.examples import EXAMPLES
from argumentation.experiments import run_experiments


def fixture(name):
    item = EXAMPLES[name]
    return AF(item["arguments"], item["attacks"])


def oracle_labellings(af):
    """Independent 3^n total labelling enumeration, using the local iff rules."""
    args = sorted(af.arguments)
    valid = []
    for labels in itertools.product(("in", "out", "undec"), repeat=len(args)):
        lab = dict(zip(args, labels))
        for a in args:
            attackers = [x for x, y in af.attacks if y == a]
            expected = (
                "out"
                if any(lab[x] == "in" for x in attackers)
                else "in" if all(lab[x] == "out" for x in attackers) else "undec"
            )
            if lab[a] != expected:
                break
        else:
            valid.append(lab)
    return valid


def oracle_grounded(arguments, attacks):
    """Independent in/out propagation, without calling characteristic()."""
    remaining = set(arguments)
    accepted = set()
    while remaining:
        unattacked = {
            a for a in remaining if not any(y == a and x in remaining for x, y in attacks)
        }
        if not unattacked:
            break
        accepted |= unattacked
        defeated = {y for x, y in attacks if x in unattacked}
        remaining -= unattacked | defeated
    return frozenset(accepted)


class BookTests(unittest.TestCase):
    def test_examples_55_56_58(self):
        af = fixture("book-5.1")
        for s in [[], ["a3"], ["a5"], ["a3", "a5"], ["a1", "a3", "a5"]]:
            self.assertTrue(af.is_admissible(s))
        self.assertTrue(af.defends(["a3", "a5"], "a1"))
        self.assertFalse(af.defends(["a3"], "a1"))
        self.assertFalse(af.is_complete(["a3", "a5"]))
        self.assertEqual(af.characteristic(["a3", "a5"]), {"a1", "a3", "a5"})
        self.assertEqual(af.grounded_trace(), [frozenset(), {"a3", "a5"}, {"a1", "a3", "a5"}])
        for semantics in ["grounded", "complete", "preferred", "stable", "semi-stable"]:
            self.assertEqual(af.extensions(semantics), [frozenset(["a1", "a3", "a5"])])

    def test_examples_57_58(self):
        af = fixture("book-5.2")
        self.assertEqual(
            set(af.complete_extensions()),
            {frozenset(["a3"]), frozenset(["a1", "a3"]), frozenset(["a2", "a3"])},
        )
        self.assertEqual(len(af.preferred_extensions()), 2)
        self.assertEqual(len(af.legal_labellings()), 3)
        self.assertEqual(af.acceptance_status("a3", "preferred"), "skeptically accepted")
        self.assertEqual(af.acceptance_status("a1", "preferred"), "credulously accepted")
        self.assertEqual(af.acceptance_status("a1", "grounded"), "rejected")

    def test_example_510_corrected_utilities(self):
        item = EXAMPLES["book-5.10"]
        m = GroundedMechanism(fixture("book-5.10"), item["ownership"])
        outcome = m.outcome(item["ownership"])
        self.assertEqual(outcome, {"a1", "a3"})
        self.assertEqual([m.utility(i, outcome) for i in ["x", "y", "z"]], [1, 0, 1])
        deviation = m.outcome({"x": ["a4", "a5"], "y": ["a2"], "z": ["a3"]})
        self.assertEqual(deviation, {"a2", "a4", "a5"})
        self.assertEqual(m.utility("x", deviation), 2)
        self.assertFalse(m.theorem_53()["strategyproof"])
        best = m.best_responses("x", {"y": ["a2"], "z": ["a3"]})
        self.assertEqual(best["maximum_utility"], 2)
        self.assertEqual(best["best_reports"][0]["report"], ["a4", "a5"])

    def test_example_511_all_profiles(self):
        m = GroundedMechanism(fixture("book-5.11"), EXAMPLES["book-5.11"]["ownership"])
        self.assertEqual(m.outcome(m.ownership), {"a1", "a4", "a5", "a6"})
        self.assertTrue(m.theorem_53()["strategyproof"])
        self.assertFalse(m.theorem_54_condition()["holds"])


class EdgeCaseTests(unittest.TestCase):
    def test_functional_entry_points(self):
        from argumentation import api

        af = fixture("chain")
        for name in [
            "grounded_extension",
            "complete_extensions",
            "preferred_extensions",
            "stable_extensions",
            "semi_stable_extensions",
            "legal_labellings",
        ]:
            self.assertEqual(getattr(api, name)(af), getattr(af, name)())
        self.assertEqual(
            api.grounded_direct_mechanism(af.attacks, [["a"], ["b"], ["c"]]), {"a", "c"}
        )
        self.assertEqual(api.grounded_direct_mechanism(af.attacks, []), set())
        ownership = {"x": ["a"], "y": ["b"], "z": ["c"]}
        self.assertTrue(api.verify_theorem_53(af, ownership)["strategyproof"])
        self.assertTrue(api.check_theorem_54_condition(af, ownership)["holds"])

    def test_empty_framework_and_empty_agent(self):
        af = AF([], [])
        for semantics in ["grounded", "complete", "preferred", "stable", "semi-stable"]:
            self.assertEqual(af.extensions(semantics), [frozenset()])
        self.assertEqual(af.legal_labellings(), [{"in_": [], "out": [], "undec": []}])
        self.assertTrue(GroundedMechanism(af, {"x": []}).check_strategyproof()["strategyproof"])

    def test_self_attack_and_no_stable(self):
        af = AF(["a"], [("a", "a")])
        self.assertFalse(af.is_conflict_free(["a"]))
        self.assertEqual(af.stable_extensions(), [])
        self.assertEqual(af.acceptance_status("a", "stable"), "undefined (no extensions)")
        self.assertEqual(af.legal_labellings()[0]["undec"], ["a"])
        m = GroundedMechanism(af, {"x": ["a"]})
        self.assertFalse(m.theorem_54_condition()["holds"])
        self.assertTrue(m.theorem_54_condition(include_self=False)["holds"])

    def test_cycle_parity_witness(self):
        af = AF(["a", "b", "c", "d"], [("a", "b"), ("b", "c"), ("c", "a"), ("c", "d")])
        m = GroundedMechanism(af, {"x": ["a", "d"], "y": ["b", "c"]})
        result = m.theorem_54_condition(include_self=False)
        self.assertFalse(result["holds"])
        w = result["witness"]["walk"]
        self.assertEqual((len(w) - 1) % 2, 1)
        self.assertTrue(all((a, b) in af.attacks for a, b in zip(w, w[1:])))

    def test_tied_best_responses(self):
        m = GroundedMechanism(AF(["a", "b"], [("a", "b")]), {"x": ["a", "b"], "y": []})
        best = m.best_responses("x", {"y": []})
        self.assertEqual(len(best["best_reports"]), 3)
        self.assertTrue(m.check_strategyproof()["strategyproof"])

    def test_validation(self):
        for args, attacks in [
            (["a", "a"], []),
            ([""], []),
            (["a"], [("a", "b")]),
            (["a"], [["a"]]),
        ]:
            with self.assertRaises(ValueError):
                AF(args, attacks)
        with self.assertRaises(ValueError):
            fixture("chain").is_complete(["unknown"])
        with self.assertRaises(ValueError):
            GroundedMechanism(fixture("chain"), {"x": ["a", "b"], "y": ["b", "c"]})
        with self.assertRaises(ValueError):
            GroundedMechanism(fixture("chain"), {"x": ["a"]})
        m = GroundedMechanism(fixture("chain"), {"x": ["a"], "y": ["b", "c"]})
        with self.assertRaises(ValueError):
            m.outcome({"x": ["b"], "y": ["c"]})
        with self.assertRaises(ValueError):
            m.best_responses("unknown", {})


class ExhaustiveOracleTests(unittest.TestCase):
    def test_all_512_three_node_graphs_against_independent_labellings(self):
        args = ["a", "b", "c"]
        edges = list(itertools.product(args, repeat=2))
        for bits in range(512):
            af = AF(args, [edge for j, edge in enumerate(edges) if bits & (1 << j)])
            with self.subTest(graph=bits):
                oracle = oracle_labellings(af)
                complete = {frozenset(a for a, v in l.items() if v == "in") for l in oracle}
                self.assertEqual(set(af.complete_extensions()), complete)
                stable = {
                    frozenset(a for a, v in l.items() if v == "in")
                    for l in oracle
                    if "undec" not in l.values()
                }
                self.assertEqual(set(af.stable_extensions()), stable)
                self.assertEqual(af.grounded_extension(), oracle_grounded(args, af.attacks))
                self.assertEqual(af.grounded_extension(), frozenset.intersection(*complete))
                admissible = [s for s in powerset(args) if af.is_admissible(s)]
                preferred = {s for s in admissible if not any(s < t for t in admissible)}
                self.assertEqual(set(af.preferred_extensions()), preferred)
                undec_sets = [frozenset(a for a, v in l.items() if v == "undec") for l in oracle]
                semi = {
                    frozenset(a for a, v in l.items() if v == "in")
                    for l, u in zip(oracle, undec_sets)
                    if not any(v < u for v in undec_sets)
                }
                self.assertEqual(set(af.semi_stable_extensions()), semi)

    def test_strategyproofness_on_every_three_node_graph(self):
        args = ["a", "b", "c"]
        edges = list(itertools.product(args, repeat=2))
        ownership = {"x": ["a", "b"], "y": ["c"], "z": []}
        choices = {i: list(powerset(s)) for i, s in ownership.items()}
        for bits in range(512):
            af = AF(args, [e for j, e in enumerate(edges) if bits & (1 << j)])
            m = GroundedMechanism(af, ownership)
            expected = True
            for profile in itertools.product(*choices.values()):
                reports = dict(zip(ownership, profile))
                union = set().union(*reports.values())
                outcome = oracle_grounded(union, af.attacks)
                for i in ownership:
                    full_union = union | set(ownership[i])
                    full = oracle_grounded(full_union, af.attacks)
                    if len(set(ownership[i]) & outcome) > len(set(ownership[i]) & full):
                        expected = False
            with self.subTest(graph=bits):
                self.assertEqual(m.check_strategyproof()["strategyproof"], expected)
                if m.theorem_54_condition()["holds"]:
                    self.assertTrue(expected)

    def test_experiment_reproducibility(self):
        a = run_experiments(5, [0.1, 0.9], 42)
        b = run_experiments(5, [0.1, 0.9], 42)
        self.assertEqual(a["records"], b["records"])
        self.assertEqual(a["summary"], b["summary"])
        for row in a["records"]:
            self.assertIn(row["n"], [6, 7, 8])
            self.assertTrue(all(row["ownership"].values()))
            self.assertFalse(any(x == y for x, y in row["attacks"]))


if __name__ == "__main__":
    unittest.main()
