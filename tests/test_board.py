"""Circuit-board tests: components, synthesis, modules, gym, budgets."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acom import components, grants, modules, objects, scheduler, synthesize  # noqa: E402
from killfeed import gym  # noqa: E402
from killfeed import validators as V  # noqa: E402


@pytest.fixture(autouse=True)
def _clean():
    components.REGISTRY.clear()
    synthesize.ensure_defaults()
    modules.seed_model_chips()
    yield
    components.REGISTRY.clear()


def test_registry_validates_and_versions():
    with pytest.raises(ValueError):
        components.register({"id": "x"})
    a = components.register({"id": "c", "inputs": ["q"], "outputs": ["a"]})
    b = dict(a)
    assert a["version"] == components.get("c")["version"]
    assert b["version"]


def test_stats_learned_from_receipts_not_guesses():
    for i, (c, ok) in enumerate([(0.1, True), (0.2, True), (0.3, False)]):
        components.record_run("web_search", "t", c, 1000 + i, ok, 0.1 * i)
    assert components.success_prob("web_search", "t") == pytest.approx(2 / 3)
    assert components.get("web_search")["cost"]["median"] == pytest.approx(0.2)


def test_voi_math():
    d = synthesize.voi_decide(0.35, 1000, 0.9, 3, 1.0)
    assert d["voi"] == pytest.approx(945.0) and d["acquire"] is True
    d2 = synthesize.voi_decide(0.01, 10, 0.5, 1, 100.0)
    assert d2["acquire"] is False


def test_synthesize_respects_budgets_and_proof():
    r = synthesize.synthesize("t", value=100.0, budget=0.05,
                              deadline_ms=60000, required_proof=4)
    assert r["best"] is not None
    assert r["best"]["cost"] <= 0.05 and r["best"]["proof"] >= 4
    r2 = synthesize.synthesize("t", value=100.0, budget=0.000001,
                               deadline_ms=60000, required_proof=12)
    assert r2["best"] is None  # free but under-proofed: say so, don't invent
    r3 = synthesize.synthesize("t", value=100.0, budget=100.0,
                               deadline_ms=60000, required_proof=12)
    assert r3["best"] is None  # no V12 chain exists


def test_module_check(tmp_path):
    p = str(tmp_path / "m.yaml")
    modules.example_module(p)
    m = modules.load(p)
    verdict = modules.check(m)
    assert verdict["ok"] is False  # example refs undefined components
    assert verdict["missing"]


def test_gym_deterministic_and_ranked():
    w = V.load_world("dram-1987")
    a = gym.compare(w, 0, 1.0)
    b = gym.compare(w, 0, 1.0)
    assert a == b
    assert a[0]["accuracy"] >= a[-1]["accuracy"]
    tight = gym.compare(w, 0, 0.03)
    assert tight[0]["spent"] <= 0.03 + 1e-9


def test_scheduler_four_budgets_and_risk_grant():
    f = scheduler.fits(
        ["web_search", "killfeed_gate"],
        {"tokens": 10**6, "seconds": 60, "dollars": 1.0, "risk": 0.0})
    assert f["fits"], f
    g = objects.make_grant("w", "swap", {"max_risk_usd": 500}, [], "2030-01-01",
                           signature="sig")
    ok = {"capability": "swap", "risk_usd": 100}
    assert grants.verify_grant(g, ok, {}, "2026-01-01")["ok"]
    assert not grants.verify_grant(
        g, {"capability": "swap", "risk_usd": 600}, {}, "2026-01-01")["ok"]
