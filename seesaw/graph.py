"""Seesaw graph math (seesaw.md, illustrative v0 formalization).

Node: {id, marginal_value M, demand D, response_time T, capacity C,
        alternatives A (0..1 availability), demand_effect, destruction_effect}.
  S_i = M * D * T / (C * A)
  CP_b (constraint pressure) = D / C
  AI exposure = demand_effect - destruction_effect  (central equation)

Positive exposure: constraint tightens as AI improves (power, validation).
Negative: AI destroys it (routine coding, now frontier math search).
Migration test: recompute S across an event; the argmax moving IS the
trade signal. Magnitudes are illustrative; ORDERINGS are the assertions.
"""
from killfeed import circuit as _circuit


def score_node(node: dict) -> dict:
    m, d, t = (float(node[x]) for x in
               ("marginal_value", "demand", "response_time"))
    c = float(node["capacity"])
    a = float(node.get("alternatives", 1.0))
    if c <= 0 or a <= 0:
        raise ValueError(f"non-positive capacity/alternatives: {node.get('id')}")
    cp = d / c
    s = m * d * t / (c * a)
    return {"id": node.get("id", "?"), "CP": round(cp, 4),
            "S": round(s, 4)}


def ai_exposure(node: dict) -> dict:
    de = float(node.get("demand_effect", 0.0))
    cd = float(node.get("destruction_effect", 0.0))
    x = de - cd
    return {"id": node.get("id", "?"), "exposure": round(x, 4),
            "direction": "TIGHTENS" if x > 0 else
                         "RELAXES" if x < 0 else "NEUTRAL"}


def binding_constraint(nodes: list) -> dict:
    """Argmax S: where is the binding constraint RIGHT NOW."""
    scored = sorted((score_node(n) for n in nodes),
                    key=lambda r: r["S"], reverse=True)
    return {"binding": scored[0]["id"], "ranking": scored}


def evaluate_event_claims(claims: dict, evidence: list, date: str) -> dict:
    """Claims A–E style boolean circuits over boolean metric evidence.
    claims: {claim_id: circuit}. Returns {claim_id: TRUE|FALSE|UNKNOWN}."""
    out = {}
    for cid, node in claims.items():
        v = _circuit.evaluate(node, evidence, date)
        if v is True:
            v = "TRUE"
        elif v is False:
            v = "FALSE"
        out[cid] = v
    return out
