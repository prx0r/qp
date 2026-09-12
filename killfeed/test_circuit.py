"""Circuit tests: the gate layer is data now, so test the data path.

- §3 truth table over the TRADE_CIRCUIT (every row of the spec).
- Legacy templates == circuits on all 10 worlds (migration proof).
- Kleene laws: UNKNOWN poisons AND/OR correctly, IS_UNKNOWN tests it.
- Temporal ops against synthetic history.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from killfeed import circuit, engine, validators as V  # noqa: E402
from killfeed.engine import TRADE_CIRCUIT  # noqa: E402


def _trade(states):
    return circuit.evaluate(TRADE_CIRCUIT, [], "2020-01-01", claims=states)


def test_section3_truth_table():
    assert _trade({"NEED": "FALSE", "GAP": "TRUE", "LAG": "TRUE",
                   "WTP": "TRUE", "NOSUB": "TRUE"}) == "KILLED"
    assert _trade({"NEED": "TRUE", "GAP": "FALSE", "LAG": "TRUE",
                   "WTP": "TRUE", "NOSUB": "TRUE"}) == "KILLED"
    assert _trade({"NEED": "UNKNOWN", "GAP": "TRUE", "LAG": "TRUE",
                   "WTP": "TRUE", "NOSUB": "TRUE"}) == "UNKNOWN"
    assert _trade({"NEED": "TRUE", "GAP": "TRUE", "LAG": "FALSE",
                   "WTP": "TRUE", "NOSUB": "TRUE"}) == "WARNING"
    assert _trade({"NEED": "TRUE", "GAP": "TRUE", "LAG": "TRUE",
                   "WTP": "TRUE", "NOSUB": "UNKNOWN"}) == "UNKNOWN"
    assert _trade({p: "TRUE" for p in
                   ("NEED", "GAP", "LAG", "WTP", "NOSUB")}) == "ACTIVE"
    # kill priority over unknowns elsewhere
    assert _trade({"NEED": "FALSE", "GAP": "UNKNOWN", "LAG": "UNKNOWN",
                   "WTP": "UNKNOWN", "NOSUB": "UNKNOWN"}) == "KILLED"


def test_legacy_circuits_equivalent():
    for wid in V.WORLDS:
        w = V.load_world(wid)
        a = [(r["as_of"], r["state_after"], r["claim_states"])
             for r in engine.evaluate_world(w, use_circuit=False)]
        b = [(r["as_of"], r["state_after"], r["claim_states"])
             for r in engine.evaluate_world(w, use_circuit=True)]
        assert a == b, wid


def test_kleene_laws():
    E = circuit.evaluate
    assert E({"op": "AND", "args": [{"const": "TRUE"},
                                    {"const": "UNKNOWN"}]},
             [], "2020-01-01") == "UNKNOWN"
    assert E({"op": "AND", "args": [{"const": "FALSE"},
                                    {"const": "UNKNOWN"}]},
             [], "2020-01-01") == "FALSE"
    assert E({"op": "OR", "args": [{"const": "TRUE"},
                                   {"const": "UNKNOWN"}]},
             [], "2020-01-01") == "TRUE"
    assert E({"op": "IS_UNKNOWN", "args": [{"const": "UNKNOWN"}]},
             [], "2020-01-01") == "TRUE"
    assert E({"op": "IS_UNKNOWN", "args": [{"const": "TRUE"}]},
             [], "2020-01-01") == "FALSE"


def _hist_ev(metric, values, date="2020-01-01"):
    return [{"evidence_id": f"e{i}", "metric": metric, "value": v,
             "unit": "x", "as_of": date,
             "source": {"source_id": "s", "class": "news",
                        "artifact_hash": "sha256:0"},
             "extraction": {}} for i, v in enumerate(values)]


def test_temporal_ops():
    hist = [{"date": "2019-01-01",
             "evidence": _hist_ev("m", [100], "2019-01-01"),
             "states": {"GAP": "TRUE"}},
            {"date": "2019-06-01",
             "evidence": _hist_ev("m", [120], "2019-06-01"),
             "states": {"GAP": "TRUE"}}]
    E = circuit.evaluate
    now = _hist_ev("m", [140], "2020-01-01")
    assert E({"op": "TREND_UP", "args": [], "metric": "m", "periods": 2},
             now, "2020-01-01", hist) == "TRUE"
    assert E({"op": "TREND_DOWN", "args": [], "metric": "m", "periods": 2},
             now, "2020-01-01", hist) == "FALSE"
    assert E({"op": "CHANGED_BY", "metric": "m",
              "direction": "GT", "delta": 10},
             now, "2020-01-01", hist) == "TRUE"
    assert E({"op": "CHANGED_WITHIN", "args": [], "predicate": "GAP",
              "days": 400}, now, "2020-01-01", hist) == "FALSE"


def test_malformed_circuits_fail_loud():
    E = circuit.evaluate
    for bad in ({"op": "NOPE", "args": []},
                {"claim": "MISSING"},
                {"param": "nope"},
                "not-a-dict"):
        try:
            E(bad, [], "2020-01-01")
        except (ValueError, AttributeError):
            continue
        raise SystemExit(f"malformed circuit scored: {bad!r}")
