"""Pluggable belief updaters (beautyy.md §7–§8): dodge the ugly Bayesian
machinery without losing determinism. Every update records
{prior, evidence, updater+version, after} so a later formalism (II MU
or otherwise) competes on equal footing in CG/MWGYM — no architecture
change, just a new registry entry.
"""
import math

REGISTRY = {}


def updater(name: str, version: str = "1"):
    def wrap(fn):
        REGISTRY[name] = {"fn": fn, "version": version}
        return fn
    return wrap


def apply(name: str, prior: float, evidence: dict):
    """Run a named updater. Unknown names raise (never silently default)."""
    if name not in REGISTRY:
        raise ValueError(f"unknown updater {name}")
    return REGISTRY[name]["fn"](prior, evidence)


@updater("logodds", version="1")
def _logodds(prior: float, evidence: dict):
    """Default: odds multiply by LR. prior in (0,1), LR > 0."""
    assert 0.0 < prior < 1.0 and evidence["lr"] > 0
    lo = math.log(prior / (1 - prior)) + math.log(evidence["lr"])
    return 1.0 / (1.0 + math.exp(-lo))


@updater("beam", version="1")
def _beam(prior: float, evidence: dict):
    """Epistemic beam w in [-1,1]: additive shifts, clipped. Simple,
    auditable, no pretense of perfect Bayes. Delta in [-1,1]."""
    assert -1.0 <= prior <= 1.0
    d = evidence["delta"]
    assert -1.0 <= d <= 1.0
    return max(-1.0, min(1.0, prior + d))
