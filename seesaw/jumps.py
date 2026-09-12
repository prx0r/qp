"""Jump processes (beautyy.md §2, §17): breakthroughs arrive as
discrete vector shocks, not smooth trends. dS_i = mu dt + sigma dW +
J_i dN. This module is the J term: one breakthrough, many nodes.

An impact vector maps node → score delta (or the special FLIP value
forcing recompute). apply_jump returns before/after bindings plus the
alpha window record {t0, t_star, notes}: the job is minimizing
t_star - t0 for second/third-order consequences.
"""
from .graph import ai_exposure, binding_constraint


def apply_jump(nodes: list, impacts: dict, t0: str) -> dict:
    """impacts: {node_id: delta_S} added to each node's S-relevant demand.
    Returns migration report. Deterministic."""
    before = binding_constraint(nodes)
    after_nodes = []
    for n in nodes:
        n2 = dict(n)
        if n.get("id") in impacts:
            n2["demand"] = max(0.01, float(n["demand"]) + impacts[n["id"]])
        after_nodes.append(n2)
    after = binding_constraint(after_nodes)
    flipped = [nid for nid in impacts if impacts[nid] != 0]
    return {"t0": t0, "t_star": None, "before": before["binding"],
            "after": after["binding"], "migrated": before["binding"] != after["binding"],
            "flipped": sorted(flipped), "ranking": after["ranking"]}


def close_alpha_window(report: dict, t_star: str, notes: str = "") -> dict:
    """Record when consensus finished assimilating (t_star). The standing
    objective: minimize t_star - t0 across events."""
    report["t_star"] = t_star
    report["notes"] = notes
    return report


def exposure_map(nodes: list) -> dict:
    """AI exposure per node: the master quantity dλ/dA by node."""
    return {n.get("id", "?"): ai_exposure(n) for n in nodes}
