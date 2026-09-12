"""Reflexivity loop (atunomousgoal §13): the market destroys what it finds.

Innovation → Bottleneck → Price → CapitalAllocation → Capacity →
BottleneckRelief, simulated as a discrete dynamical system over S_i
with lead time τ. Proves the loop shape in code: a discovered scarcity
with finite supply response always relaxes under its own proceeds.
Investors front-running the relief only change the clock speed.
"""
from . import graph


def step(nodes: list, alloc_efficiency: float = 0.5) -> list:
    """One period: high-S nodes attract allocation, allocation becomes
    capacity after lead time (modeled as immediate partial relief with
    response_time weighting — v0, explicit simplification)."""
    out = []
    for n in nodes:
        n2 = dict(n)
        s = graph.score_node(n)["S"]
        relief = alloc_efficiency * min(s / 100.0, 1.0)
        n2["capacity"] = float(n["capacity"]) * (1 + relief)
        out.append(n2)
    return out


def simulate(nodes: list, periods: int, alloc_efficiency: float = 0.5):
    """Run the loop. Returns per-period bindings: the bottleneck must
    weaken or migrate, never strengthen forever under finite response."""
    trace = []
    cur = nodes
    for _ in range(periods):
        b = graph.binding_constraint(cur)
        trace.append({"binding": b["binding"],
                      "top_S": b["ranking"][0]["S"]})
        cur = step(cur, alloc_efficiency)
    return trace
