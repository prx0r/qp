"""Seesaw formal tests: the Navier–Stokes event as machine verdicts.

Asserts the worked example from seesaw.md: claims A–E evaluate as
specified, the dumb thematic trade (short CFD) evaluates FALSE, and
the binding constraint migrates from discovery to verification while
CFD software doesn't move. If any of these fail, the lens is decoration.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seesaw import graph  # noqa: E402

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "events", "ns_202609.json")


def _load():
    return json.load(open(FIX))


def test_ns_claims_evaluate_as_specified():
    fx = _load()
    got = graph.evaluate_event_claims(fx["claims"], fx["evidence"],
                                      fx["date"])
    for cid, want in fx["expected"].items():
        assert got[cid] == want, f"{cid}: got {got[cid]}, want {want}"


def test_dumb_thematic_trade_rejected():
    fx = _load()
    got = graph.evaluate_event_claims(fx["claims"], fx["evidence"],
                                      fx["date"])
    assert got["NS_CFD_WORTHLESS"] == "FALSE"


def test_binding_constraint_migrates():
    fx = _load()
    before = graph.binding_constraint(fx["nodes_before"])
    after = graph.binding_constraint(fx["nodes_after"])
    assert before["binding"] == "math_search"
    assert after["binding"] == "verification"
    cfd = [r for r in after["ranking"] if r["id"] == "cfd_software"][0]
    cfd_before = [r for r in before["ranking"] if r["id"] == "cfd_software"][0]
    assert cfd["S"] == cfd_before["S"]  # CFD didn't move: the point


def test_ai_exposure_directions():
    fx = _load()
    after = {n["id"]: n for n in fx["nodes_after"]}
    assert graph.ai_exposure(after["math_search"])["direction"] == "RELAXES"
    assert graph.ai_exposure(after["verification"])["direction"] == "TIGHTENS"
