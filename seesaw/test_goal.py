"""Autonomous-goal tests: vectors, waiting room, reflexivity, H1–H5."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seesaw import classes, hypotheses, reflex, waiting  # noqa: E402
from killfeed import validators as V  # noqa: E402


def test_vectors_encode_thesis_examples():
    ns = classes.VECTORS["navier-stokes-2026"]
    assert classes.sign(ns)["COGNITION"] == -1
    assert classes.sign(ns)["VERIFICATION"] == 1
    assert "COGNITION" in classes.destroyed(ns)
    assert "VERIFICATION" in classes.amplified(ns)
    with pytest.raises(ValueError):
        classes.encode({"NOPE": 1})
    with pytest.raises(ValueError):
        classes.encode({"MEMORY": 5})


def test_waiting_room_lag_detection():
    store = []
    waiting.log_breakthrough(store, "ns-2026", "2026-09-08",
                             {"COGNITION": -2, "VERIFICATION": 2})
    assert waiting.lag_candidates(store, "ns-2026") != []
    waiting.record_response(store, "ns-2026", "VERIFICATION", "2026-09-20",
                            True)
    waiting.record_response(store, "ns-2026", "COGNITION", "2026-09-20",
                            False)
    lags = waiting.lag_candidates(store, "ns-2026")
    assert [l["constraint"] for l in lags] == ["COGNITION"]
    assert lags[0]["status"] == "LAGGED"
    waiting.close_window(store, "ns-2026", "2026-10-01")
    assert store[0]["t_star"] == "2026-10-01"


def test_reflexivity_relaxes_discovered_scarcity():
    nodes = [{"id": "mem", "marginal_value": 9, "demand": 9,
              "response_time": 5, "capacity": 2, "alternatives": 0.9}]
    trace = reflex.simulate(nodes, 6)
    first = trace[0]["top_S"]
    assert trace[-1]["top_S"] < first  # proceeds destroy the rent
    assert all(t["binding"] == "mem" for t in trace)


def test_h4_h5_hold_on_all_worlds():
    for wid in V.WORLDS:
        w = V.load_world(wid)
        h4 = hypotheses.h4_staged_discovery(w)
        assert h4["ok"], (wid, h4)
        h5 = hypotheses.h5_graph_beats_naive(w)
        assert h5["ok"], (wid, h5)


def test_h1_h3_shapes_specified():
    assert hypotheses.h1_frequency_shape(
        [("a", 1), ("b", 2), ("c", 3)])["ok"] is True
    assert hypotheses.h1_frequency_shape([("a", 3)])["ok"] is False
    assert hypotheses.h2_complexity_shape(
        [{"a": 1}, {"a": 1, "b": -1}])["ok"] is True
    assert hypotheses.h3_forecast_error_shape([0.2, 0.5])["ok"] is True


def test_series_store_adjudicates_h123():
    from seesaw import series as _series
    s = _series.Series()
    assert s.adjudicate()["H1"]["ok"] is False  # empty: honest, not green
    s.record_jump_period("2024", 2)
    s.record_jump_period("2025", 3)
    s.record_jump_period("2026", 5)
    s.record_vector({"a": 1})
    s.record_vector({"a": 1, "b": -1})
    s.record_error(0.2)
    s.record_error(0.4)
    out = s.adjudicate()
    assert out["H1"]["ok"] is True
    assert out["H2"]["ok"] is True
    assert out["H3"]["ok"] is True


def test_lead_times_separate_restart_from_fab():
    from seesaw import reflex as _reflex
    base = {"marginal_value": 9, "demand": 9, "response_time": 5,
            "capacity": 2, "alternatives": 0.9}
    fast = _reflex.simulate([dict(base, id="mill", lead_periods=0)], 4)
    slow = _reflex.simulate([dict(base, id="fab", lead_periods=4)], 4)
    assert fast[-1]["top_S"] < slow[-1]["top_S"]  # fab relief arrives late
    assert slow[1]["top_S"] == slow[0]["top_S"]  # nothing materializes yet


def test_divergence_direction_and_zero():
    from seesaw import graph as _g
    d = _g.divergence(0.8, 0.4, 1.5, 2.0, 0.9)
    assert d["direction"] == "LONG_SCARCITY" and d["divergence"] > 0
    assert _g.divergence(0.4, 0.4, 1.0, 1.0, 0.5)["direction"] == "FLAT"
    assert _g.divergence(0.2, 0.7, 1.0, 1.0, 1.0)["direction"] == "SHORT_SCARCITY"


def test_monitor_flips_challenges_dossier():
    from seesaw import monitor as _m
    before = [{"id": "math_search", "marginal_value": 10, "demand": 9, "response_time": 10, "capacity": 2, "alternatives": 0.9, "demand_effect": 8, "destruction_effect": 1},
              {"id": "verification", "marginal_value": 6, "demand": 5, "response_time": 2, "capacity": 6, "alternatives": 0.7, "demand_effect": 1, "destruction_effect": 1}]
    after = [{"id": "math_search", "marginal_value": 10, "demand": 2, "response_time": 10, "capacity": 8, "alternatives": 0.9, "demand_effect": 1, "destruction_effect": 9},
             {"id": "verification", "marginal_value": 8, "demand": 9, "response_time": 2, "capacity": 6, "alternatives": 0.7, "demand_effect": 7, "destruction_effect": 1}]
    out = _m.watch(before, after, "2026-09-12")
    assert {f["node"] for f in out["flips"]} == {"math_search", "verification"}
    assert len(out["challenges"]) == 2
    assert out["dossier"]["before"] == "math_search" and out["dossier"]["after"] == "verification"


def test_hbm_shadow_frozen_binding():
    import json
    from seesaw.graph import binding_constraint
    fx = json.load(open("seesaw/events/hbm_shadow.json"))
    assert binding_constraint(fx["nodes"])["binding"] == "hbm"


def test_alpha_window_measures_assimilation_lag():
    from seesaw import waiting as _w
    store = []
    _w.log_breakthrough(store, "q", "2026-09-01", {"MEMORY": 2})
    _w.record_response(store, "q", "MEMORY", "2026-09-11", True)
    _w.close_window(store, "q", "2026-09-11")
    from datetime import date
    delta = (date.fromisoformat(store[0]["t_star"]) - date.fromisoformat(store[0]["t0"])).days
    assert delta == 10  # t_star - t0 is the standing objective to minimize
