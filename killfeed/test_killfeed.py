"""Killfeed acceptance, pytest edition. Full gate is verify_all;
this file runs the fast subset (determinism at 10 reruns) so the
default suite stays quick. Anything here failing means the harness,
not just a world, is broken.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from killfeed import validators as V  # noqa: E402


def test_worlds():
    r = V.v_all_worlds()
    assert r["ok"], r["detail"]


def test_precision():
    r = V.v_precision()
    assert r["ok"], r["detail"]


def test_determinism_smoke():
    r = V.v_determinism(10)
    assert r["ok"], r["detail"]


def test_no_future_leak():
    assert V.v_no_future_leak()["ok"]


def test_unknown_and_source_failure():
    assert V.v_unknown_semantics()["ok"]
    assert V.v_source_failure()["ok"]


def test_lineage_mutation_dependency():
    assert V.v_duplicates()["ok"]
    assert V.v_mutation()["ok"]
    assert V.v_dependency()["ok"]


def test_adversarial_and_schemas():
    assert V.v_adversarial()["ok"]
    assert V.v_schemas()["ok"]


def test_two_counterfactuals_per_world():
    import glob as _g
    import os as _o
    for wid in ["oil-1979", "dram-1987", "fiber-1996", "palladium-1998",
                "china-metals-2003", "uranium-2003", "rare-earths-2010",
                "lumber-2020", "containers-2020", "fertilizer-2021"]:
        n = len(_g.glob(f"killfeed/worlds/{wid}/counterfactuals/*.json"))
        assert n >= 2, wid
    assert True
