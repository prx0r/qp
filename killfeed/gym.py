"""Circuit-design gym (circuitboard2.md): what circuit SHOULD you build?

Game: a hidden snapshot, a per-metric read price list, a budget. A
strategy orders metric reads; unread metrics are missing (UNKNOWN).
Score candidates on predicate accuracy vs the full-evidence verdict,
cost spent, and proof maintained. Deterministic: same strategy and
budget always score identically. This is where routing policies earn
promotion instead of asserting it.
"""
from . import engine

DEFAULT_COSTS = {"demand": 0.02, "supply": 0.02, "intensity": 0.005,
                 "relevant": 0.005, "close": 0.01, "horizon": 0.01,
                 "price": 0.005, "qty": 0.005, "share": 0.01,
                 "redesign": 0.01}


def _suffix(metric: str) -> str:
    return metric.split("_")[-1]


def mask(snapshot: dict, allowed: set) -> dict:
    return dict(snapshot, evidence=[e for e in snapshot["evidence"]
                                   if e["metric"] in allowed])


STRATEGIES = {
    "full": lambda metrics, budget, costs: list(metrics),
    "gap-first": lambda metrics, budget, costs: sorted(
        metrics, key=lambda m: (0 if _suffix(m) in ("demand", "supply")
                                else 1, m)),
    "need-first": lambda metrics, budget, costs: sorted(
        metrics, key=lambda m: (0 if _suffix(m) in ("intensity", "relevant")
                                else 1, m)),
    "cheap-first": lambda metrics, budget, costs: sorted(
        metrics, key=lambda m: (costs.get(_suffix(m), 0.01), m)),
}


def run_task(world: dict, snapshot_idx: int, strategy: str, budget: float,
             costs: dict = None):
    """One gym task. Returns score dict (deterministic)."""
    costs = costs or DEFAULT_COSTS
    snap = world["timeline"][snapshot_idx]
    truth = engine.evaluate_snapshot(world, snap)["claim_states"]
    metrics = sorted({e["metric"] for e in snap["evidence"]})
    order = STRATEGIES[strategy](metrics, budget, costs)
    allowed, spent = set(), 0.0
    for m in order:
        c = costs.get(_suffix(m), 0.01)
        if spent + c > budget + 1e-9:
            break
        allowed.add(m)
        spent += c
    got = engine.evaluate_snapshot(world, mask(snap, allowed))
    states = got["claim_states"]
    agree = sum(1 for p in states if states[p] == truth[p])
    return {"strategy": strategy, "budget": budget,
            "spent": round(spent, 4), "read": sorted(allowed),
            "accuracy": agree / 5, "trade": got["state_after"],
            "truth_trade": engine.evaluate_trade(truth)}


def compare(world: dict, snapshot_idx: int, budget: float):
    """Rank all strategies on one task. Cheapest adequate circuit wins."""
    rows = [run_task(world, snapshot_idx, s, budget)
            for s in STRATEGIES]
    rows.sort(key=lambda r: (-r["accuracy"], r["spent"]))
    return rows
