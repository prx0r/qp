"""Versioned-component tests: chains, determinism, full run history."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acom import components, versions  # noqa: E402


@pytest.fixture(autouse=True)
def _clean():
    components.REGISTRY.clear()
    versions._VERSIONS.clear()
    yield
    components.REGISTRY.clear()
    versions._VERSIONS.clear()


def _mk(cid="c"):
    return components.register({"id": cid, "inputs": ["x"],
                                "outputs": ["y"]})


def _run(cid, tc="t", **kw):
    d = {"receipt_id": kw.get("rid", f"r-{cid}-{kw.get('n', 0)}"),
         "model": kw.get("model", "m1"), "latency_ms": kw.get("ms", 100),
         "cost": kw.get("cost", 0.5), "success": kw.get("ok", True),
         "outputs_root": kw.get("out", "o")}
    return versions.attach_run(cid, tc, d)


def test_version_chain_and_immutability():
    v1 = _mk("c")
    v2 = versions.revise("c", {"outputs": ["y", "z"]}, "add z")
    assert v2["version"] != v1["version"]
    assert v2["supersedes"] == v1["version"]
    assert versions.chain("c")[-1]["version"] == v2["version"]
    assert len(versions.chain("c")) == 2
    fresh = versions.chain("c")
    assert fresh[0]["version"] == v1["version"]  # old version untouched
    assert "z" not in fresh[0]["outputs"] and "z" in fresh[1]["outputs"]


def test_deterministic_execute_and_replay_refusal():
    _mk("det")
    out = versions.execute("det", "t", {"x": 1}, "m1",
                           lambda i: {"y": i["x"] + 1})
    assert out["outputs"] == {"y": 2}
    assert versions.totals("det", "t")["runs"] == 1
    _mk("flaky")
    import itertools
    state = itertools.count()
    with pytest.raises(ValueError):
        versions.execute("flaky", "t", {"x": 1}, "m1",
                         lambda i: {"y": next(state)})


def test_run_records_require_full_shape():
    _mk("c")
    with pytest.raises(ValueError):
        versions.attach_run("c", "t", {"model": "m"})
    _run("c")
    with pytest.raises(ValueError):
        _run("c")  # same receipt_id = replay, refused


def test_totals_derive_from_history():
    _mk("c")
    _run("c", model="m1", ms=100, cost=0.5, ok=True, n=1)
    _run("c", model="m2", ms=300, cost=1.5, ok=False, n=2)
    t = versions.totals("c", "t")
    assert (t["runs"], t["wins"]) == (2, 1)
    assert t["total_cost"] == pytest.approx(2.0)
    assert t["total_ms"] == 400
    assert t["models"] == {"m1": {"runs": 1, "wins": 1},
                           "m2": {"runs": 1, "wins": 0}}
    assert len(t["receipts"]) == 2


def test_promotion_compares_versions():
    _mk("c")
    _run("c", ok=True, n=1)
    _run("c", ok=False, n=2)
    versions.revise("c", {"outputs": ["y", "z"]}, "better?")
    _run("c", ok=True, n=3)
    _run("c", ok=True, n=4)
    chain = versions.chain("c")
    d = versions.compare(chain[0]["version"], chain[1]["version"], "t")
    assert d["ok"] and d["promote"] is True
    assert d["success_delta"] == pytest.approx(0.5)
    e = versions.compare(chain[0]["version"], chain[1]["version"], "nope")
    assert e["ok"] is False


def test_history_survives_save_load(tmp_path):
    _mk("c")
    _run("c", n=1)
    versions.revise("c", {"outputs": ["y", "z"]}, "better?")
    p = str(tmp_path / "reg.json")
    versions.save_all(p)
    components.REGISTRY.clear()
    versions.load_all(p)
    chain = versions.chain("c")
    assert len(chain) == 2  # archive survived the round trip
    assert versions.totals(chain[0]["version"], "t")["runs"] == 1
    assert versions.totals(chain[1]["version"], "t")["runs"] == 0
