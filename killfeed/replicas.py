"""Five-replica agreement (plan2 Layer 6): diverge → localize, never vote.

Replicas evaluate the same snapshot independently. Identical outputs =
agreement. Any divergence triggers dispute bisection (killfeed/dispute.py)
to the minimal evidence subset preserving it. Majority vote is NOT a
resolution mechanism: a 4-1 split means one side is wrong about specific
bytes, and the subset names them.
"""
from . import dispute
from .engine import evaluate_snapshot


def agree(world: dict, snapshot: dict, variants: list):
    """variants: [{name, mutations}]. Returns agreement or divergence
    report with the localized minimal subset (first divergence found)."""
    results = []
    for v in variants:
        r = evaluate_snapshot(world, snapshot, v.get("mutations"))
        results.append((v.get("name", "?"), r))
    base = results[0][1]["claim_states"]
    for name, r in results[1:]:
        if r["claim_states"] != base:
            sub = dispute.localize(world, snapshot, variants[0], {"name": name,
                "mutations": next(x.get("mutations") for x in variants
                                  if x.get("name") == name)})
            return {"agreement": False, "divergent": name,
                    "claims_a": base, "claims_b": r["claim_states"],
                    "minimal_subset": sub}
    return {"agreement": True, "replicas": len(results),
            "claims": base}
