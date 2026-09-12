"""Reflexivity loop (atunomousgoal §13): the market destroys what it finds.

Innovation → Bottleneck → Price → CapitalAllocation → Capacity →
BottleneckRelief, simulated as a discrete dynamical system over S_i
with lead time τ. Proves the loop shape in code: a discovered scarcity
with finite supply response always relaxes under its own proceeds.
Investors front-running the relief only change the clock speed.
"""
from . import graph


def step(nodes: list, alloc_efficiency: float = 0.5, queues=None):
    """One period with lead times: allocation decided today materializes
    after each node's lead_periods (restart soon, fab late). Queues carry
    in-flight capacity; pass the returned queues back in."""
    queues = queues or {}
    out = []
    for n in nodes:
        nid = n.get("id", "?")
        n2 = dict(n)
        s = graph.score_node(n)["S"]
        relief = alloc_efficiency * min(s / 100.0, 1.0)
        q = queues.setdefault(nid, [])
        q.append((int(n.get("lead_periods", 0)), relief))
        due = sum(r for t, r in q if t <= 0)
        queues[nid] = [(t - 1, r) for t, r in q if t > 0]
        n2["capacity"] = float(n["capacity"]) * (1 + due)
        out.append(n2)
    return out, queues


def simulate(nodes: list, periods: int, alloc_efficiency: float = 0.5):
    """Run the loop. Returns per-period bindings: the bottleneck must
    weaken or migrate, never strengthen forever under finite response."""
    trace, queues, cur = [], {}, nodes
    for _ in range(periods):
        b = graph.binding_constraint(cur)
        trace.append({"binding": b["binding"],
                      "top_S": b["ranking"][0]["S"]})
        cur, queues = step(cur, alloc_efficiency, queues)
    return trace
