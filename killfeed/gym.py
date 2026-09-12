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
    """Hide unread metrics: the strategy sees only what it paid for."""
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
    """One gym task against the full-evidence verdict as ground truth.
    Deterministic: same strategy and budget always score identically."""
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
    """Rank all strategies: accuracy first, spend breaks ties. Cheapest
    adequate circuit wins — that is the routing policy earning promotion."""
    rows = [run_task(world, snapshot_idx, s, budget)
            for s in STRATEGIES]
    rows.sort(key=lambda r: (-r["accuracy"], r["spent"]))
    return rows


def oring_leverage(stages: list) -> list:
    """O-ring screen (postreview): multiplicative chain where every stage
    must hold. System success = product of stage success. Returns stages
    ranked by leverage = dP/dcost     (fix the highest-leverage stage first).
    Each stage: {id, p_success 0..1, fix_cost > 0}."""
    rows = []
    for s in stages:
        p, c = s["p_success"], s["fix_cost"]
        assert 0.0 < p < 1.0 and c > 0
        others = 1.0
        for o in stages:
            if o["id"] != s["id"]:
                others *= o["p_success"]
        leverage = others * (1.0 - p) / c
        rows.append({"id": s["id"], "leverage": round(leverage, 6),
                     "system_p_if_fixed": round(others, 4)})
    rows.sort(key=lambda r: -r["leverage"])
    return rows
