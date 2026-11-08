"""Functional entry points for the assignment, alongside the object-oriented API."""

from .strategic import GroundedMechanism


def grounded_extension(framework):
    return framework.grounded_extension()


def complete_extensions(framework):
    return framework.complete_extensions()


def preferred_extensions(framework):
    return framework.preferred_extensions()


def stable_extensions(framework):
    return framework.stable_extensions()


def semi_stable_extensions(framework):
    return framework.semi_stable_extensions()


def legal_labellings(framework):
    return framework.legal_labellings()


def acceptance_status(framework, argument, semantics="grounded"):
    return framework.acceptance_status(argument, semantics)


def grounded_direct_mechanism(global_attacks, revealed_sets):
    """Take global attacks and one revealed argument set per agent; induce union."""
    from .engine import ArgumentationFramework

    arguments = set().union(*map(set, revealed_sets))
    return ArgumentationFramework(
        sorted(arguments), [(a, b) for a, b in global_attacks if a in arguments and b in arguments]
    ).grounded_extension()


def best_responses(framework, ownership, agent, other_reports):
    return GroundedMechanism(framework, ownership).best_responses(agent, other_reports)


def verify_theorem_53(framework, ownership):
    return GroundedMechanism(framework, ownership).theorem_53()


def check_theorem_54_condition(framework, ownership, include_self=True):
    return GroundedMechanism(framework, ownership).theorem_54_condition(include_self)
