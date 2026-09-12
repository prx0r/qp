"""DAG-to-circuit compiler (postreview build #1): typed causal edges in,
executable claim circuits out. Bottleneck chains compile to AND (every
link must hold), substitution branches to OR (any path relieves), edges
whose delay exceeds the horizon are dropped with a note (they cannot
fire in time). Leaf claims stay symbolic for evidence binding later.
"""
from killfeed import circuit as _circuit


def compile(dag: dict, horizon_years: float = 5.0) -> dict:
    """dag: {nodes: [{id, op: AND|OR|LEAF}], edges: [{src, dst,
    elasticity, confidence, delay_years}]}. Returns {circuits: {node:
    circuit}, dropped: [...], notes}. Raises on cycles or unknown ops."""
    nodes = {n["id"]: n for n in dag.get("nodes", [])}
    if set(nodes) != {n["id"] for n in dag.get("nodes", [])}:
        raise ValueError("duplicate node ids")
    children = {}
    dropped = []
    for e in dag.get("edges", []):
        if e["src"] not in nodes or e["dst"] not in nodes:
            raise ValueError(f"edge to unknown node: {e}")
        if float(e.get("delay_years", 0)) > horizon_years:
            dropped.append({"edge": [e["src"], e["dst"]],
                            "reason": "delay exceeds horizon"})
            continue
        children.setdefault(e["dst"], []).append(e["src"])
    order, temp, perm = [], set(), set()

    def visit(nid):
        if nid in perm:
            return
        if nid in temp:
            raise ValueError(f"cycle at {nid}")
        temp.add(nid)
        for e in dag.get("edges", []):
            if e["dst"] == nid and e["src"] in children.get(nid, []):
                visit(e["src"])
        temp.remove(nid)
        perm.add(nid)
        order.append(nid)

    for nid in nodes:
        visit(nid)
    circuits = {}
    for nid in order:
        op = nodes[nid].get("op", "LEAF")
        kids = children.get(nid, [])
        if not kids:
            circuits[nid] = {"claim": nid}  # leaf state supplied at eval
        elif op == "AND":
            circuits[nid] = {"op": "AND",
                             "args": [{"claim": k} for k in kids]}
        elif op == "OR":
            circuits[nid] = {"op": "OR",
                             "args": [{"claim": k} for k in kids]}
        else:
            raise ValueError(f"unknown node op: {op}")
    return {"circuits": circuits, "dropped": dropped,
            "order": order}


def evaluate(compiled: dict, claims: dict) -> dict:
    """Evaluate every compiled circuit against supplied leaf states."""
    out = {}
    for nid in compiled["order"]:
        out[nid] = _circuit.evaluate(compiled["circuits"][nid], [],
                                     "2000-01-01", claims={**claims, **out})
    return out
