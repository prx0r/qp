"""Replica, run-receipt, swarm, settle, and WASM tests."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acom import runs  # noqa: E402
from killfeed import dispute, engine, replicas, settle, swarm  # noqa: E402
from killfeed import validators as V  # noqa: E402


def _agg(w, snap, prefix):
    usable, _, _ = engine.admissible(
        snap["evidence"], snap["date"], w["config"].get("max_age_days", 400))

    def rng(metric):
        vs = [e["value"] for e in usable if e.get("metric") == metric]
        lows = [v["low"] if isinstance(v, dict) else v for v in vs]
        highs = [v["high"] if isinstance(v, dict) else v for v in vs]
        return (min(lows), max(highs)) if lows else (None, None)

    (dl, dh) = rng(f"{prefix}_demand")
    (sl, sh) = rng(f"{prefix}_supply")
    return dl, dh, sl, sh


def test_replicas_agree_all_worlds():
    for wid in V.WORLDS:
        w = V.load_world(wid)
        roots = set()
        for _ in range(3):  # nodes A, B, C: independent evaluations
            roots.add(engine.world_state_root(engine.evaluate_world(w)))
        assert len(roots) == 1, wid


def test_five_replicas_localize_divergence():
    w = V.load_world("dram-1987")
    snap = w["timeline"][0]
    variants = [{"name": f"v{i}"} for i in range(4)] + [
        {"name": "v4-mut", "mutations": {"GAP": {"invert": True}}}]
    rep = replicas.agree(w, snap, variants)
    assert not rep["agreement"] and rep["divergent"] == "v4-mut"
    assert rep["minimal_subset"], "divergence must localize, not just flag"


def test_dispute_minimize():
    w = V.load_world("dram-1987")
    snap = w["timeline"][2]  # KILLED via GAP FALSE
    sub = dispute.minimize(w, snap, "GAP", "FALSE")
    assert sub, "minimizer found nothing"
    assert len(sub) <= len(snap["evidence"])


def test_run_receipt_binds_and_verifies():
    r = runs.build({"id": "task:t"}, "hermes3:8b", "prompt:abc",
                   [{"tool": "vote"}], [{"in": 1}], [{"out": 2}], 0.01,
                   [{"e": 1}])
    assert runs.verify(r)["ok"]
    assert runs.verify(r, outputs=[{"out": 3}])["ok"] is False


def test_swarm_jobs_typed():
    w = V.load_world("dram-1987")
    receipts = engine.evaluate_world(w)
    snap = w["timeline"][1]
    jobs = swarm.derive_jobs(w, receipts[1], snap)
    kinds = {j["task_kind"] for j in jobs}
    assert kinds <= {"FILL", "REFRESH", "CHALLENGE", "FALSIFY"}
    assert jobs, "WARNING snapshot should emit challenge work"


def test_settle_anchor_roundtrip(tmp_path):
    p = str(tmp_path / "anchor.jsonl")
    a = settle.anchor(p, 1, "state:1", "ev:1", "rules:1")
    assert a["ok"]
    assert settle.verify_anchors(p) == {"ok": True, "epochs": 1}


def test_wasm_gap_matches_python():
    from killfeed import wasm_gates
    prefix = {"dram-1987": "dram"}["dram-1987"]
    w = V.load_world("dram-1987")
    for snap in w["timeline"]:
        dl, dh, sl, sh = _agg(w, snap, prefix)
        got = wasm_gates.gap_wasm(dl, dh, sl, sh, 1.0)
        want = [r for r in engine.evaluate_world(w)
                if r["as_of"] == snap["date"]][0]["claim_states"]["GAP"]
        assert got == want, snap["date"]
    nan = float("nan")
    assert wasm_gates.gap_wasm(nan, nan, nan, nan) == "UNKNOWN"
    assert wasm_gates.gap_wasm(130, 140, 90, 100) == "TRUE"
