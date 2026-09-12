"""Belief-layer tests: Extropic wave, epoch finality, EI ranking.

The Z1T numbers pin the worked example from bayesian.md: one evidence
bundle moves A–E from the stated priors to the stated posteriors.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seesaw.beliefs import Graph  # noqa: E402

PRIORS = {"A": 0.95, "B": 0.91, "C": 0.88, "D": 0.84, "E": 0.30}
POST = {"A": 0.72, "B": 0.77, "C": 0.70, "D": 0.91, "E": 0.65}
LRS = {"A": 0.13534, "B": 0.33109, "C": 0.31818, "D": 1.9259, "E": 4.3333}


def _graph():
    g = Graph()
    for k, p in PRIORS.items():
        g.belief(k, p, impact={"A": 0.9, "B": 0.7, "C": 0.8, "D": 0.5,
                               "E": 0.65}[k])
    return g


def test_extropic_wave_reproduces_spec():
    g = _graph()
    for k, lr in LRS.items():
        g.update(k, "z1t-bundle", lr)
    for k, want in POST.items():
        assert g.nodes[k]["p"] == pytest.approx(want, abs=0.005), k


def test_finalize_freezes_epoch_never_reopens():
    g = _graph()
    f = g.finalize("A", 182, "TRUE", "ev:1", "gate:1", "proof:1")
    assert f["id"] == "A@epoch-182" and f["verdict"] == "TRUE"
    with pytest.raises(ValueError):
        g.update("A@epoch-182", "later-news", 2.0)
    f2 = g.finalize("A", 250, "FALSE", "ev:2", "gate:1")
    assert f2["id"] != f["id"]  # new epoch appends, history stands
    assert g.nodes["A"]["p"] == pytest.approx(0.95)  # belief untouched


def test_propagation_wave_order_and_deltas():
    g = Graph()
    g.belief("thermo", 0.5)
    g.belief("hbm_duration", 0.8)
    g.belief("trade_long", 0.7)
    g.support("Z1_EFFICIENT", "thermo", 3.0, 0.4)
    g.support("thermo_state", "hbm_duration", 0.5, 2.0)
    g.support("hbm_duration_state", "trade_long", 0.4, 2.5)
    wave = g.propagate({"Z1_EFFICIENT": "TRUE", "thermo_state": "TRUE",
                        "hbm_duration_state": "FALSE"}, "z1t-news")
    ids = [w["id"] for w in wave]
    assert ids == ["thermo", "hbm_duration", "trade_long"]
    assert wave[0]["after"] > wave[0]["before"]  # good news lifts thermo
    assert wave[1]["after"] < wave[1]["before"]  # thermo TRUE trims duration
    # duration-scare debunked (FALSE) lifts the long trade via lr 2.5
    assert wave[2]["after"] > wave[2]["before"]


def test_unknown_sources_skip_silently():
    g = Graph()
    g.belief("x", 0.6)
    g.support("Q", "x", 5.0, 0.2)
    assert g.propagate({"Q": "UNKNOWN"}, "e") == []


def test_ei_ranks_research():
    g = _graph()
    ranked = sorted(PRIORS, key=lambda k: g.expected_impact(k, 0.2),
                    reverse=True)
    assert ranked[0] == "A"  # 0.2 x 0.9 tops the list
