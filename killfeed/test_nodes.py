"""Replica, run-receipt, swarm, settle, and WASM tests."""
import os
import sys

import pytest

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


def test_tjp_falsifier_corpus_loads_and_seeds():
    from killfeed import tjp_falsifiers as T
    rows = T.load_corpus()
    assert len(rows) >= 30, f"corpus shrank: {len(rows)}"
    assert all(r["falsifier"] and r["thesis"] for r in rows)
    jobs = T.to_jobs(rows)
    assert len(jobs) == len(rows)
    assert {j["task_kind"] for j in jobs} == {"FALSIFY"}
    assert all("falsifier" in j["acceptance"] for j in jobs)


def test_lag_candidates_become_swarm_jobs():
    from killfeed import swarm
    from seesaw import waiting
    store = []
    waiting.log_breakthrough(store, "ns-2026", "2026-09-08",
                             {"COGNITION": -2, "VERIFICATION": 2})
    jobs = swarm.jobs_from_lags(store, "ns-2026")
    assert len(jobs) == 2
    assert {j["task_kind"] for j in jobs} == {"FALSIFY"}
    waiting.record_response(store, "ns-2026", "VERIFICATION", "2026-09-20",
                            True)
    jobs2 = swarm.jobs_from_lags(store, "ns-2026")
    assert len(jobs2) == 1 and jobs2[0]["acceptance"]["constraint"] == "COGNITION"


def test_oring_ranks_weakest_cheapest_link_first():
    from killfeed import gym
    rows = gym.oring_leverage([
        {"id": "design", "p_success": 0.99, "fix_cost": 10.0},
        {"id": "qualify", "p_success": 0.60, "fix_cost": 1.0},
        {"id": "ship", "p_success": 0.95, "fix_cost": 2.0},
    ])
    assert [r["id"] for r in rows] == ["qualify", "ship", "design"]
    assert rows[0]["system_p_if_fixed"] == pytest.approx(0.99 * 0.95)


def test_dag_compiles_to_executable_circuits():
    from killfeed import dag_compile
    dag = {"nodes": [{"id": "gap", "op": "AND"}, {"id": "demand"},
                     {"id": "supply"}, {"id": "relief", "op": "OR"},
                     {"id": "sub"}, {"id": "ramp"}],
           "edges": [{"src": "demand", "dst": "gap", "delay_years": 0},
                     {"src": "supply", "dst": "gap", "delay_years": 0},
                     {"src": "sub", "dst": "relief", "delay_years": 0},
                     {"src": "ramp", "dst": "relief", "delay_years": 9},
                     {"src": "gap", "dst": "trade", "delay_years": 0},
                     {"src": "relief", "dst": "trade", "delay_years": 0}]}
    try:
        dag_compile.compile(dag)
        assert False, "edge to unknown node must raise"
    except ValueError:
        pass
    dag["nodes"].append({"id": "trade", "op": "AND"})
    comp = dag_compile.compile(dag, horizon_years=5.0)
    assert comp["dropped"] == [{"edge": ["ramp", "relief"],
                                "reason": "delay exceeds horizon"}]
    out = dag_compile.evaluate(comp, {"demand": "TRUE", "supply": "TRUE",
                                      "sub": "FALSE", "ramp": "TRUE"})
    assert out == {"demand": "TRUE", "supply": "TRUE", "gap": "TRUE",
                   "sub": "FALSE", "ramp": "TRUE", "relief": "FALSE",
                   "trade": "FALSE"}


def test_obsolescence_gate_pure_python():
    from killfeed import obsolescence as O
    assert O.obsolescence(100, 10) > O.obsolescence(100, 90) > 0
    cites = [{"citing_firm": "us", "citing_year": 2018, "cited_patent": "p1", "cited_owner": "them"},
             {"citing_firm": "us", "citing_year": 2019, "cited_patent": "p2", "cited_owner": "them"},
             {"citing_firm": "other", "citing_year": 2021, "cited_patent": "p1", "cited_owner": "them"},
             {"citing_firm": "other2", "citing_year": 2021, "cited_patent": "p2", "cited_owner": "them"},
             {"citing_firm": "other", "citing_year": 2024, "cited_patent": "p2", "cited_owner": "them"}]
    assert O.construct_base(cites, "us", 2020) == {"p1", "p2"}
    assert O.construct_base(cites, "nobody", 2020) is None
    assert O.external_cites(cites, {"p1", "p2"}, 2024) == 1
    v = O.firm_obsolescence(cites, "us", 2021, 2024, window=2)
    assert v is not None and v > 0  # 2 outside cites decayed to 1
    assert O.firm_obsolescence(cites, "nobody", 2021, 2024) is None


def test_reverse_inference_identifiable_and_refusal():
    from killfeed import reverse as R
    ok = R.infer_market_probabilities([[1.0, 0.2], [0.3, 1.0], [0.5, 0.5]], [0.6, 0.7, 0.5])
    assert ok["ok"] and all(0.0 <= p <= 1.0 for p in ok["probs"])
    short = R.infer_market_probabilities([[1.0, 0.0]], [0.5])
    assert short["ok"] is False
    collinear = R.infer_market_probabilities([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]], [0.5, 0.5, 0.5], ridge=0.0)
    assert collinear["ok"] is False  # unregularized singularity refuses


def test_backtest_walk_forward_honest():
    from killfeed import backtest as B
    panel = [{"date": f"2020-0{m}-01", "ticker": t, "score": s, "fwd_ret": r}
             for m, sc in [(1, [3, 1, -1, -3]), (2, [2, 0, 0, -2])]
             for t, s, r in zip(["a", "b", "c", "d"], sc, [0.1, 0.02, -0.02, -0.1])]
    out = B.walk_forward(panel, cost_bps=10.0, quantile=0.25)
    assert len(out["nets"]) == 2
    assert out["nets"][0]["net"] > 0  # long winners, short losers
    assert set(out) >= {"ann", "vol", "sharpe", "maxdd"}


def test_wasm_all_gates_match_python():
    from killfeed import engine, wasm_gates
    nan = float("nan")
    assert wasm_gates.need_wasm(0.9, 0.5, 1, 0.5) == engine.gate_need(0.9, 0.5, True)[0] == "TRUE"
    assert wasm_gates.need_wasm(0.3, 0.5, 1, 0.5) == engine.gate_need(0.3, 0.5, True)[0] == "FALSE"
    assert wasm_gates.need_wasm(nan, 0.5, 1, 0.5) == "UNKNOWN"
    assert wasm_gates.lag_wasm(20250101, 20240101) == engine.gate_lag("2025-01-01", "2024-01-01")[0] == "TRUE"
    assert wasm_gates.lag_wasm(20230101, 20240101) == engine.gate_lag("2023-01-01", "2024-01-01")[0] == "FALSE"
    assert wasm_gates.wtp_wasm(60, -2) == engine.gate_wtp(60, -2)[0] == "TRUE"
    assert wasm_gates.wtp_wasm(60, -18) == engine.gate_wtp(60, -18)[0] == "FALSE"
    assert wasm_gates.wtp_wasm(5, -2) == engine.gate_wtp(5, -2)[0] == "UNKNOWN"
    assert wasm_gates.nosub_wasm(0.05) == engine.gate_nosub(0.05)[0] == "TRUE"
    assert wasm_gates.nosub_wasm(0.35) == engine.gate_nosub(0.35)[0] == "FALSE"
    assert wasm_gates.nosub_wasm(nan) == "UNKNOWN"


def test_ree_bridge_and_ratings_priors():
    from acom import runs
    from killfeed import tjp_falsifiers as T
    r = runs.build({"id": "task:t"}, "m", "p", [], [{"i": 1}], [{"o": 2}], 0.01, [])
    e = runs.export_ree(r)
    assert e["model"] == "m" and e["compat"] == "shape-only"
    assert runs.verify(r)["ok"]  # export never mutates
    rows = T.load_corpus()
    priors = T.ratings_as_priors(rows)
    assert len(priors) == len(rows)
    rated = {k: v for k, v in priors.items() if v > 0}
    assert rated, "no ratings parsed at all"
    assert all(0.0 < v <= 1.0 for v in rated.values())
