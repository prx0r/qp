"""Breakthrough battery: the shared migration pattern, three events.

Every breakthrough must show the same shape: binding migrates, the
relaxed node carries negative AI exposure, the tightened node positive
exposure. NS and AlphaFold load fixtures; Extropic encodes the thesis
weights trajectory (illustrative magnitudes, asserted directions).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seesaw import graph, jumps  # noqa: E402

EV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "events")


def _case(name):
    fx = json.load(open(os.path.join(EV, name)))
    before = graph.binding_constraint(fx["nodes_before"])["binding"]
    after = graph.binding_constraint(fx["nodes_after"])["binding"]
    mp = jumps.exposure_map(fx["nodes_after"])
    return before, after, mp


def test_ns_migration_pattern():
    before, after, mp = _case("ns_202609.json")
    assert before == "math_search" and after == "verification"
    assert mp["math_search"]["direction"] == "RELAXES"
    assert mp["verification"]["direction"] == "TIGHTENS"


def test_alphafold_migration_pattern():
    before, after, mp = _case("alphafold.json")
    assert before == "structure_prediction"
    assert after == "wetlab_validation"
    assert mp["structure_prediction"]["direction"] == "RELAXES"
    assert mp["wetlab_validation"]["direction"] == "TIGHTENS"


def test_extropic_migration_pattern():
    nodes_before = [
        {"id": "hbm_compute", "marginal_value": 9, "demand": 9,
         "response_time": 6, "capacity": 3, "alternatives": 0.9,
         "demand_effect": 8, "destruction_effect": 1},
        {"id": "thermo_fab", "marginal_value": 5, "demand": 2,
         "response_time": 8, "capacity": 2, "alternatives": 0.5,
         "demand_effect": 2, "destruction_effect": 1},
        {"id": "power", "marginal_value": 7, "demand": 6,
         "response_time": 4, "capacity": 5, "alternatives": 0.8,
         "demand_effect": 7, "destruction_effect": 0},
    ]
    nodes_after = [
        {"id": "hbm_compute", "marginal_value": 9, "demand": 4,
         "response_time": 6, "capacity": 3, "alternatives": 0.9,
         "demand_effect": 3, "destruction_effect": 8},
        {"id": "thermo_fab", "marginal_value": 7, "demand": 7,
         "response_time": 8, "capacity": 2, "alternatives": 0.5,
         "demand_effect": 7, "destruction_effect": 1},
        {"id": "power", "marginal_value": 8, "demand": 8,
         "response_time": 4, "capacity": 5, "alternatives": 0.8,
         "demand_effect": 8, "destruction_effect": 0},
    ]
    assert graph.binding_constraint(nodes_before)["binding"] == "hbm_compute"
    rep = jumps.apply_jump(nodes_before, {"hbm_compute": -5, "thermo_fab": 5,
                                          "power": 2}, "2026-09-01")
    assert rep["before"] == "hbm_compute"
    after = graph.binding_constraint(nodes_after)["binding"]
    assert after == "thermo_fab"
    mp = jumps.exposure_map(nodes_after)
    assert mp["hbm_compute"]["direction"] == "RELAXES"
    assert mp["thermo_fab"]["direction"] == "TIGHTENS"
    assert rep["migrated"] is True


def test_truth_infra_family_moves_together():
    import json
    from seesaw import graph, jumps
    fx = json.load(open("seesaw/events/truth_infra.json"))
    mp = jumps.exposure_map(fx["members"])
    assert all(v["direction"] == "TIGHTENS" for v in mp.values())
    before = graph.binding_constraint(fx["members"])["binding"]
    rep = jumps.apply_jump(
        fx["members"], {m["id"]: 2 for m in fx["members"]}, fx["date"])
    assert rep["after"] == before  # family moves together, no internal flip
    s0 = {r["id"]: r["S"] for r in graph.binding_constraint(
        fx["members"])["ranking"]}
    assert all(v > 0 for v in s0.values())
