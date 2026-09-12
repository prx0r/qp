"""Migration monitor (todos 9–11): exposure flips open CHALLENGEs,
new argmax opens dossiers, HBM graph frozen for future adjudication.

Watch rule, stated once: a node whose AI-exposure direction flips
between evaluations gets a CHALLENGE task (attack the flip, confirm or
kill it); a binding migration opens a dossier (candidate trade file).
Neither invents data — both route attention the fixtures already earned.
"""
from killfeed import swarm as _swarm
from seesaw import graph as _graph
from seesaw import jumps as _jumps


def watch(before: list, after: list, date: str) -> dict:
    """Compare two node sets (same ids). Returns flips, challenges,
    dossier-or-None. Deterministic."""
    bmap = {n["id"]: n for n in before}
    amap = {n["id"]: n for n in after}
    if set(bmap) != set(amap):
        raise ValueError("watch compares same node sets across an event")
    flips = []
    for nid in bmap:
        d0 = _graph.ai_exposure(bmap[nid])["direction"]
        d1 = _graph.ai_exposure(amap[nid])["direction"]
        if d0 != d1:
            flips.append({"node": nid, "from": d0, "to": d1})
    b_bind = _graph.binding_constraint(before)["binding"]
    a_bind = _graph.binding_constraint(after)["binding"]
    challenges = []
    for f in flips:
        challenges.extend(_swarm.jobs_from_lags(
            [{"id": f"watch-{date}", "t0": date,
              "vector": {}, "signs": {},
              "long_leg": [f["node"]] if f["to"] == "TIGHTENS" else [],
              "short_leg": [f["node"]] if f["to"] == "RELAXES" else [],
              "responses": {}, "t_star": None}],
            f"watch-{date}"))
    dossier = None
    if a_bind != b_bind:
        dossier = {"id": f"dossier-{date}", "date": date,
                   "before": b_bind, "after": a_bind,
                   "flips": flips}
    return {"date": date, "flips": flips, "challenges": challenges,
            "dossier": dossier}
