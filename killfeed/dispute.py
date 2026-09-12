"""Dispute bisection, Verde-style: smallest evidence subset preserving a
verdict difference (plan2 Layer 6). Never re-argue the whole world.

minimize(): ddmin over evidence for a target (predicate, state).
localize(): minimal subset where variant-A and variant-B evaluations
disagree. Empty subset or failure returns [] (no false localizations).
"""
import itertools


def _verdict(world, snapshot, evidence, predicate, mutations, from_engine):
    snap = dict(snapshot, evidence=list(evidence))
    r = from_engine(world, snap, mutations)
    return r["claim_states"][predicate]


def minimize(world, snapshot, predicate, target_state, mutations=None):
    """Smallest subset still scoring target_state (greedy ddmin)."""
    from . import engine as _e
    items = list(snapshot["evidence"])
    if _verdict(world, snapshot, items, predicate, mutations,
                _e.evaluate_snapshot) != target_state:
        return []
    changed = True
    while changed and len(items) > 1:
        changed = False
        for i in range(len(items)):
            trial = items[:i] + items[i + 1:]
            if _verdict(world, snapshot, trial, predicate, mutations,
                        _e.evaluate_snapshot) == target_state:
                items = trial
                changed = True
                break
    return [e["evidence_id"] for e in items]


def localize(world, snapshot, variant_a, variant_b):
    """Minimal subset where A and B disagree on any claim state."""
    from . import engine as _e
    ma, mb = variant_a.get("mutations"), variant_b.get("mutations")
    ra = _e.evaluate_snapshot(world, snapshot, ma)["claim_states"]
    rb = _e.evaluate_snapshot(world, snapshot, mb)["claim_states"]
    diffs = [p for p in ra if ra[p] != rb.get(p)]
    if not diffs:
        return []
    items = list(snapshot["evidence"])
    changed = True
    while changed and len(items) > 1:
        changed = False
        for i in range(len(items)):
            trial = items[:i] + items[i + 1:]
            sa = _e.evaluate_snapshot(world, dict(snapshot, evidence=trial),
                                      ma)["claim_states"]
            sb = _e.evaluate_snapshot(world, dict(snapshot, evidence=trial),
                                      mb)["claim_states"]
            if any(sa.get(p) != sb.get(p) for p in diffs):
                items = trial
                changed = True
                break
    return {"predicates": diffs,
            "evidence": [e["evidence_id"] for e in items]}
