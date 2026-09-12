"""Swarm job derivation (plan2 Layer 5): agents never decide truth.

From an evaluated snapshot, emit typed jobs only:
FILL (missing metric), REFRESH (stale source), CHALLENGE (attack a
WARNING's falsifiers), FALSIFY (probe thin TRUE margins). Jobs are
A-COM TASKs; their outputs are evidence, never verdicts.
"""
from acom import objects

FALSIFY_MARGIN = 5.0


def jobs_from_lags(store: list, bid: str, window_days: int = 90) -> list:
    """Waiting-room output becomes swarm input: every lagged or unobserved
    predicted constraint becomes a FALSIFY task aimed at the breakthrough.
    This is the standing wire between 'the market hasn't responded here'
    and 'go look here'. Deterministic given the store."""
    from seesaw import waiting
    jobs = []
    for lag in waiting.lag_candidates(store, bid, window_days):
        jobs.append(objects.make_task(
            "FALSIFY", bid,
            {"constraint": lag["constraint"], "status": lag["status"],
             "need": f"market-response evidence for {lag['constraint']}; "
                     f"confirm the move or kill the prediction"}))
    return jobs


def derive_jobs(world: dict, receipt: dict, snapshot: dict,
                falsify_margin: float = FALSIFY_MARGIN) -> list:
    """Emit typed jobs from an evaluated snapshot. Agents never decide
    truth here; they only get FILL/REFRESH/CHALLENGE/FALSIFY assignments
    whose outputs return as evidence, never verdicts."""
    cfg = world["config"]
    usable_metrics = {e["metric"] for e in snapshot["evidence"]}
    jobs = []
    details = receipt.get("_meta", {}).get("details", {})
    for name in ("NEED", "GAP", "LAG", "WTP", "NOSUB"):
        st = receipt["claim_states"][name]
        if st == "UNKNOWN":
            jobs.append(objects.make_task(
                "FILL", f"{world['world_id']}.{name.lower()}",
                {"need": "fresh accepted evidence for undecided predicate"}))
        det = details.get(name, {})
        if det.get("state") == "TRUE" and isinstance(det.get("margin"),
                                                     (int, float)):
            if det["margin"] < falsify_margin:
                jobs.append(objects.make_task(
                    "FALSIFY", f"{world['world_id']}.{name.lower()}",
                    {"need": f"breaker evidence; margin {det['margin']}"}))
        if det.get("state") == "FALSE":
            jobs.append(objects.make_task(
                "CHALLENGE", f"{world['world_id']}.{name.lower()}",
                {"need": "disconfirming hard evidence or accept the flip"}))
    if receipt.get("_meta", {}).get("stale"):
        for s in receipt["_meta"]["stale"][:3]:
            jobs.append(objects.make_task(
                "REFRESH", f"{world['world_id']}.{s}",
                {"need": "current-as-of replacement evidence"}))
    _ = usable_metrics, cfg
    return jobs
