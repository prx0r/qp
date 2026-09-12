"""H1–H5 empirical harness skeleton (atunomousgoal §20).

H1–H3 need live history we don't have yet: they are specified here as
runnable checks against fixture series so the moment real series land,
the same functions adjudicate. H4–H5 run TODAY on killfeed worlds.
A hypothesis that cannot fail is decoration; every function below can.
"""
from killfeed import engine


def h4_staged_discovery(world: dict) -> dict:
    """H4: price discovery occurs in stages (direct → suppliers →
    second-order → substituted). Proxy on fixtures: WARNING must precede
    KILLED, and the killing predicate must differ from the warning
    predicate (stages are distinct events, not one jump)."""
    receipts = engine.evaluate_world(world)
    states = [r["state_after"] for r in receipts]
    if "WARNING" not in states or "KILLED" not in states:
        return {"ok": False, "reason": "no staged progression"}
    w = next(r for r in receipts if r["state_after"] == "WARNING")
    k = next(r for r in receipts if r["state_after"] == "KILLED")
    warn_false = {p for p, v in w["claim_states"].items() if v == "FALSE"}
    kill_false = {p for p, v in k["claim_states"].items() if v == "FALSE"}
    staged = bool(kill_false - warn_false)
    return {"ok": staged, "warning_flips": sorted(warn_false),
            "kill_flips": sorted(kill_false)}


def h5_graph_beats_naive(world: dict) -> dict:
    """H5: structured dependency beats naive thematic association. Naive
    baseline: every predicate TRUE (thematic hype). Graph must disagree
    with naive on at least the kill snapshot (else it adds nothing)."""
    receipts = engine.evaluate_world(world)
    naive = {p: "TRUE" for p in ("NEED", "GAP", "LAG", "WTP", "NOSUB")}
    naive_trade = engine.evaluate_trade(naive)
    diffs = [r["as_of"] for r in receipts
             if r["state_after"] != naive_trade]
    return {"ok": bool(diffs), "naive_trade": naive_trade,
            "divergent_snapshots": diffs}


def h1_frequency_shape(series: list) -> dict:
    """H1: jumps-per-period non-decreasing over the observed window.
    series: [(period, count)]. Specified, awaiting live series."""
    if len(series) < 2:
        return {"ok": False, "reason": "insufficient history"}
    return {"ok": all(b >= a for (_, a), (_, b) in
                       zip(series, series[1:])),
            "periods": len(series)}


def h2_complexity_shape(vectors: list) -> dict:
    """H2: mean impact-vector breadth non-decreasing. vectors: list of
    impact dicts per event. Specified, awaiting live series."""
    if len(vectors) < 2:
        return {"ok": False, "reason": "insufficient history"}
    breadth = [sum(1 for v in vec.values() if v != 0) for vec in vectors]
    return {"ok": all(b >= a for a, b in zip(breadth, breadth[1:])),
            "breadths": breadth}


def h3_forecast_error_shape(errors: list) -> dict:
    """H3: consensus error around jumps not shrinking. errors: list of
    absolute errors in event order. Specified, awaiting live series."""
    if len(errors) < 2:
        return {"ok": False, "reason": "insufficient history"}
    return {"ok": errors[-1] >= errors[0], "first": errors[0],
            "last": errors[-1]}
