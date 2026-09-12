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
