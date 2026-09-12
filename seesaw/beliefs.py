"""Belief layer (bayesian.md): BELIEF vs FACT, waves, EI scoring.

Two node kinds, never confused:
- BELIEF: open probabilistic state, log-odds updated per evidence item
  (L_t = L_{t-1} + log LR). Reopenable forever.
- FACT: epoch-finalized verdict, immutable. New epochs append new
  FACTs; history is never rewritten. Updating a finalized FACT raises.

Dependency DAG gives truth-maintenance waves: when a basis node moves,
downstream beliefs recompute in topo order and the wave (ordered
before/after deltas) is returned. EI = P(E) x Impact ranks research.
"""
import math

from acom.canonical import obj_id


def _odds(p: float) -> float:
    p = min(max(p, 1e-9), 1 - 1e-9)
    return p / (1 - p)


def _prob(logodds: float) -> float:
    return 1.0 / (1.0 + math.exp(-logodds))


class Graph:
    """Belief/FACT dependency graph. Deterministic; no I/O."""

    def __init__(self):
        self.nodes = {}
        self.edges = []  # (supporter -> dependent)

    def belief(self, bid: str, prior: float, impact: float = 0.0) -> dict:
        """Open a BELIEF at prior odds. Reopenable forever; finality only
        arrives via finalize(), which mints a separate FACT."""
        assert 0.0 < prior < 1.0
        n = {"kind": "BELIEF", "id": bid, "p": prior,
             "logodds": math.log(_odds(prior)), "impact": impact,
             "updates": []}
        self.nodes[bid] = n
        return n

    def support(self, source: str, dependent: str, lr_on_true: float,
                lr_on_false: float):
        """FACT/claim `source` feeds BELIEF `dependent`: if the source
        evaluates TRUE apply lr_on_true, if FALSE lr_on_false, if
        UNKNOWN skip (no information). Edges are data, re-runnable."""
        assert lr_on_true > 0 and lr_on_false > 0
        if (source, dependent) not in [(s, d) for s, d, _, _ in self.edges]:
            self.edges.append((source, dependent, lr_on_true, lr_on_false))

    def update(self, bid: str, evidence_id: str, lr: float) -> dict:
        """One Bayesian step. LR > 1 supports, < 1 undermines."""
        n = self.nodes[bid]
        if n["kind"] != "BELIEF":
            raise ValueError("finalized FACTs never reopen; append a new epoch")
        assert lr > 0
        n["logodds"] += math.log(lr)
        n["p"] = _prob(n["logodds"])
        n["updates"].append({"evidence": evidence_id, "lr": lr, "p": n["p"]})
        return n

    def finalize(self, bid: str, epoch: int, verdict: str, evidence_root: str,
                 gate_hash: str, proof_hash: str = "") -> dict:
        """Clamp one epoch's verdict into an immutable FACT. History is
        never reopened; later epochs append new FACTs."""
        n = self.nodes[bid]
        assert verdict in ("TRUE", "FALSE")
        fact = {"kind": "FACT", "id": f"{bid}@epoch-{epoch}",
                "claim": bid, "verdict": verdict, "epoch": epoch,
                "evidence_root": evidence_root, "gate_hash": gate_hash,
                "proof_hash": proof_hash}
        fact["digest"] = obj_id("fact", fact)
        self.nodes[fact["id"]] = fact
        return fact

    def propagate(self, claim_states: dict, evidence_id: str) -> list:
        """Truth-maintenance wave: evaluated claim states (TRUE/FALSE/
        UNKNOWN, e.g. from killfeed circuits) flow along support edges
        into dependent BELIEFs. Topological order, each dependent updated
        at most once per wave. Returns ordered {id, before, after} deltas
        for every belief that actually moved."""
        order, seen = [], {s for s in claim_states}
        pending = [(s, d, lt, lf) for s, d, lt, lf in self.edges
                   if s in claim_states]
        while pending:
            # A dependent is ready when every supporter is either a
            # claim-state or an already-emitted node.
            ready = [e for e in pending
                     if all((p in claim_states) or (p in seen)
                            for p, q, _, _ in self.edges if q == e[1])]
            if not ready:  # cycle: emit in registration order, no hang
                ready = pending[:1]
            for e in ready:
                seen.add(e[1])
                order.append(e[1])
                pending.remove(e)
                for s2, d2, lt2, lf2 in self.edges:
                    if s2 == e[1] and d2 not in seen and \
                            (s2, d2, lt2, lf2) not in pending:
                        pending.append((s2, d2, lt2, lf2))
        wave = []
        for d in order:
            node = self.nodes.get(d)
            if node is None or node["kind"] != "BELIEF":
                continue
            before = node["p"]
            for s, dd, lt, lf in self.edges:
                if dd != d or s not in claim_states:
                    continue
                st = claim_states[s]
                if st == "TRUE":
                    self.update(d, evidence_id, lt)
                elif st == "FALSE":
                    self.update(d, evidence_id, lf)
            if node["p"] != before:
                wave.append({"id": d, "before": round(before, 4),
                             "after": round(node["p"], 4)})
        return wave

    def expected_impact(self, bid: str, p_event: float) -> float:
        """EI = P(E) x Impact: what to research next."""
        return p_event * self.nodes[bid].get("impact", 0.0)
