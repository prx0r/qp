"""Second-wave tests: updaters, persistence, jumps, feeds, AlphaFold."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seesaw import beliefs, feeds, jumps, updaters  # noqa: E402
from seesaw.graph import binding_constraint  # noqa: E402

EV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "events", "alphafold.json")


def test_updater_registry_and_beam_math():
    assert updaters.apply("logodds", 0.5, {"lr": 3.0}) == pytest.approx(0.75)
    assert updaters.apply("beam", 0.2, {"delta": 0.5}) == pytest.approx(0.7)
    assert updaters.apply("beam", 0.9, {"delta": 0.5}) == 1.0  # clipped
    with pytest.raises(ValueError):
        updaters.apply("ii_mu", 0.5, {"lr": 2.0})  # not solved here


def test_update_records_carry_updater_version():
    g = beliefs.Graph()
    g.belief("h", 0.5)
    g.update("h", "e1", 2.0)
    rec = g.nodes["h"]["updates"][-1]
    assert rec["updater"].startswith("logodds:")
    assert rec["prior"] == 0.5 and "p" in rec
    g.update_beam("h", "e2", -0.1)
    assert g.nodes["h"]["updates"][-1]["updater"].startswith("beam:")


def test_graph_persistence_inherits_cells(tmp_path):
    g = beliefs.Graph()
    g.belief("h", 0.6, impact=0.8)
    g.belief("k", 0.4)
    g.support("E", "h", 2.0, 0.5)
    g.update("h", "e1", 2.0)
    p = str(tmp_path / "cell.json")
    g.save(p)
    g2 = beliefs.Graph.load(p)  # new session inherits, never restarts
    assert g2.nodes["h"]["p"] == pytest.approx(g.nodes["h"]["p"])
    assert g2.edges == g.edges
    wave = g2.propagate({"E": "TRUE"}, "e2")
    assert [w["id"] for w in wave] == ["h"]
    assert wave[0]["after"] > wave[0]["before"]


def test_jump_migrates_binding_and_alpha_window():
    fx = json.load(open(EV))
    assert binding_constraint(fx["nodes_before"])["binding"] == fx["expected_before"]
    rep = jumps.apply_jump(fx["nodes_before"],
                           {"structure_prediction": -7, "wetlab_validation": 5},
                           fx["date"])
    assert rep["before"] == fx["expected_before"]
    assert rep["after"] == fx["expected_after"]
    assert rep["migrated"] is True and rep["t_star"] is None
    closed = jumps.close_alpha_window(rep, "2021-12-01", "db uptake visible")
    assert closed["t_star"] == "2021-12-01"
    mp = jumps.exposure_map(fx["nodes_after"])
    assert mp["structure_prediction"]["direction"] == "RELAXES"
    assert mp["wetlab_validation"]["direction"] == "TIGHTENS"


def test_feeds_variables_exposure_hazard():
    f = feeds.Feeds()
    f.append("AI_AUTONOMY", "2026-01-01", 0.4, "anthropic-index")
    f.append("AI_AUTONOMY", "2026-06-01", 0.55, "anthropic-index")
    assert f.latest()["AI_AUTONOMY"]["value"] == 0.55
    with pytest.raises(ValueError):
        f.append("MADE_UP", "2026-01-01", 1.0, "x")
    mix = {"coding": (0.8, 0.9), "support": (0.6, 0.7), "writing": (0.1, 0.9)}
    assert f.automation_exposure(mix) == pytest.approx((0.72 + 0.42 + 0.09) / 3)
    assert f.hazard({"sw": 0.4, "bio": 0.1}) == pytest.approx(0.5)
