#!/usr/bin/env python3
"""Deterministic fixture builder for the 10 historical worlds.

Compact specs expand to world.yaml + timeline/*.json + expected.json +
counterfactuals/*.json. Rerunning reproduces every byte, so fixture
determinism starts before the engine. Values are illustrative index
levels chosen to exercise the §9 gate boundaries, not measurements —
v0 validates the kernel, not the crawler.
"""
import json
import os

import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worlds")

UNITS = {"demand": "index", "supply": "index", "intensity": "ratio",
         "relevant": "bool", "close": "date", "horizon": "date",
         "price": "pct", "qty": "pct", "share": "ratio", "redesign": "bool"}


def ev(wid, date, metric, value, source_id, cls, seq):
    import hashlib
    key = next(k for k in UNITS if metric.endswith(k))
    art = hashlib.sha256(f"{source_id}|{metric}".encode()).hexdigest()[:6]
    return {
        "evidence_id": f"{wid}-{date[:4]}{date[5:7]}-{metric}-{seq}",
        "metric": metric, "value": value, "unit": UNITS[key],
        "as_of": date,
        "source": {"source_id": source_id, "class": cls,
                   "artifact_hash": f"sha256:{art}"},
        "extraction": {"extractor": "manual", "extractor_version": "1",
                       "reviewed": True},
    }


def A(p, src, demand, supply, close, horizon, price, qty, share,
      intensity, relevant=True, redesign=False, cls="industry_data"):
    """One full predicate slate. demand/supply are (low, high) tuples."""
    return [
        (f"{p}_demand", {"low": demand[0], "high": demand[1]},
         f"{src}-demand", cls),
        (f"{p}_supply", {"low": supply[0], "high": supply[1]},
         f"{src}-supply", cls),
        (f"{p}_intensity", intensity, f"{src}-gov", "government"),
        (f"{p}_relevant", relevant, f"{src}-gov", "government"),
        (f"{p}_close", close, f"{src}-outlook", "industry_data"),
        (f"{p}_horizon", horizon, f"{src}-outlook", "industry_data"),
        (f"{p}_price", price, f"{src}-press", "news"),
        (f"{p}_qty", qty, f"{src}-stats", "government"),
        (f"{p}_share", share, f"{src}-acad", "academic"),
        (f"{p}_redesign", redesign, f"{src}-acad", "academic"),
    ]


def _if(c, t, e):
    return {"op": "IF", "args": [c, t, e]}


def _const(v):
    return {"const": v}


def gap_circuit(p):
    d, s = f"{p}_demand", f"{p}_supply"
    return _if(
        {"op": "GTE", "args": [{"op": "COUNT", "metrics": [d, s]},
                               {"param": "min_sources"}]},
        _if({"op": "GT", "args": [
                {"op": "LOW", "metric": d},
                {"op": "MUL", "args": [{"op": "HIGH", "metric": s},
                                       {"param": "threshold"}]}]},
            _const("TRUE"),
            _if({"op": "LTE", "args": [{"op": "HIGH", "metric": d},
                                       {"op": "LOW", "metric": s}]},
                _const("FALSE"), _const("UNKNOWN"))),
        _const("UNKNOWN"))


def need_circuit(p):
    i, r = {"metric": f"{p}_intensity"}, {"metric": f"{p}_relevant"}
    return _if({"op": "AND", "args": [
                   {"op": "GTE", "args": [i, {"param": "min_intensity"}]}, r]},
               _const("TRUE"),
               _if({"op": "OR", "args": [
                       {"op": "LT", "args": [i, {"param": "kill"}]},
                       {"op": "NOT", "args": [r]}]},
                   _const("FALSE"), _const("UNKNOWN")))


def lag_circuit(p):
    c, h = {"metric": f"{p}_close"}, {"metric": f"{p}_horizon"}
    return _if({"op": "GT", "args": [c, h]}, _const("TRUE"),
               _if({"op": "LTE", "args": [c, h]},
                   _const("FALSE"), _const("UNKNOWN")))


def _neg(param):
    return {"op": "SUB", "args": [{"const": 0}, {"param": param}]}


def wtp_circuit(p):
    pr, q = {"metric": f"{p}_price"}, {"metric": f"{p}_qty"}
    up = {"op": "GTE", "args": [pr, {"param": "x"}]}
    hi = {"op": "AND", "args": [up, {"op": "GT", "args": [q, _neg("y")]}]}
    lo = {"op": "AND", "args": [up, {"op": "LTE", "args": [q, _neg("y")]}]}
    return _if(hi, _const("TRUE"), _if(lo, _const("FALSE"), _const("UNKNOWN")))


def nosub_circuit(p):
    s, r = {"metric": f"{p}_share"}, {"metric": f"{p}_redesign"}
    return _if({"op": "OR", "args": [
                   {"op": "GTE", "args": [s, {"param": "share_threshold"}]}, r]},
               _const("FALSE"),
               _if({"op": "AND", "args": [
                       {"op": "LT", "args": [s, {"param": "share_threshold"}]},
                       {"op": "NOT", "args": [r]}]},
                   _const("TRUE"), _const("UNKNOWN")))


def build(wid, trade, thesis, interval, max_age, prefix, snaps, expected,
          counterfactuals):
    d = os.path.join(ROOT, wid)
    os.makedirs(os.path.join(d, "timeline"), exist_ok=True)
    os.makedirs(os.path.join(d, "counterfactuals"), exist_ok=True)
    doc = {
        "world_id": wid, "trade": trade, "thesis": thesis,
        "interval_days": interval, "max_age_days": max_age,
        "predicates": {
            "NEED": {"intensity_metric": f"{prefix}_intensity",
                     "relevance_metric": f"{prefix}_relevant",
                     "min_intensity": 0.5,
                     "circuit": need_circuit(prefix)},
            "GAP": {"demand": [f"{prefix}_demand"],
                    "supply": [f"{prefix}_supply"],
                    "threshold": 1.0, "min_sources": 1,
                    "circuit": gap_circuit(prefix)},
            "LAG": {"close_metric": f"{prefix}_close",
                    "horizon_metric": f"{prefix}_horizon",
                    "circuit": lag_circuit(prefix)},
            "WTP": {"price_metric": f"{prefix}_price",
                    "qty_metric": f"{prefix}_qty",
                    "x": 15, "y": 10,
                    "circuit": wtp_circuit(prefix)},
            "NOSUB": {"share_metric": f"{prefix}_share",
                      "threshold": 0.25,
                      "redesign_metric": f"{prefix}_redesign",
                      "circuit": nosub_circuit(prefix)},
        },
    }
    open(os.path.join(d, "world.yaml"), "w").write(yaml.safe_dump(
        doc, sort_keys=False))
    for date, items in snaps:
        json.dump(
            {"date": date, "evidence": [
                ev(wid, date, m, v, s, c, i)
                for i, (m, v, s, c) in enumerate(items)]},
            open(os.path.join(d, "timeline", f"{date}.json"), "w"),
            sort_keys=True, indent=1)
    json.dump(expected, open(os.path.join(d, "expected.json"), "w"),
              sort_keys=True, indent=2)
    for name, date, items, exp_trade, exp_preds in counterfactuals:
        json.dump(
            {"date": date, "expected_trade": exp_trade,
             "expected_predicates": exp_preds, "evidence": [
                 ev(wid, date, m, v, s, c, i)
                 for i, (m, v, s, c) in enumerate(items)]},
            open(os.path.join(d, "counterfactuals", f"{name}.json"), "w"),
            sort_keys=True, indent=1)
    print("wrote", wid)


def exp(wid, states, signal, invariant, earliest, max_delay):
    return {"world_id": wid,
            "expected_states": [{"as_of": d, "trade": t} for d, t in states],
            "expected_first_kill_signal": signal,
            "required_invariant": invariant,
            "earliest_kill_date": earliest, "max_delay_days": max_delay}


WORLDS = [
 ("oil-1979", "oil", "supply disruption + inelastic demand", 365, 500, "oil",
  [("1979-06-01", A("oil", "iea79", (125, 135), (95, 105), "1983-01-01", "1980-06-01", 60, -2, 0.05, 0.9)),
   ("1980-06-01", A("oil", "iea80", (120, 130), (95, 105), "1982-06-01", "1981-01-01", 80, -18, 0.08, 0.85)),
   ("1981-06-01", A("oil", "iea81", (95, 100), (105, 115), "1981-09-01", "1982-01-01", 10, -5, 0.10, 0.7))],
  exp("oil-1979", [("1979-06-01", "ACTIVE"), ("1980-06-01", "WARNING"), ("1981-06-01", "KILLED")],
      "GAP", {"NEED_at_kill": "TRUE"}, "1981-06-01", 365),
  [("early-peace", "1980-06-01",
    A("oil", "cf1", (95, 100), (110, 120), "1980-09-01", "1981-06-01", 5, -2, 0.06, 0.85),
    "KILLED", {"NEED": "TRUE", "GAP": "FALSE"})]),

 ("dram-1987", "dram", "PC demand outruns DRAM supply", 365, 500, "dram",
  [("1987-06-01", A("dram", "dt87", (130, 140), (90, 100), "1989-06-01", "1988-01-01", 45, -3, 0.03, 0.85)),
   ("1988-06-01", A("dram", "dt88", (125, 135), (100, 108), "1988-12-01", "1989-06-01", 30, -4, 0.04, 0.85)),
   ("1989-06-01", A("dram", "dt89", (100, 105), (120, 130), "1989-09-01", "1990-01-01", 5, -8, 0.06, 0.8))],
  exp("dram-1987", [("1987-06-01", "ACTIVE"), ("1988-06-01", "WARNING"), ("1989-06-01", "KILLED")],
      "GAP", {"NEED_at_kill": "TRUE"}, "1989-06-01", 365),
  [("abundant-supply", "1988-06-01",
    A("dram", "cf1", (125, 135), (160, 180), "1988-09-01", "1989-06-01", 5, -1, 0.04, 0.85),
    "KILLED", {"GAP": "FALSE"})]),

 ("fiber-1996", "bandwidth", "traffic growth outruns capacity", 365, 600, "fiber",
  [("1998-01-01", A("fiber", "itu98", (140, 150), (90, 100), "2001-01-01", "1999-06-01", 50, -2, 0.02, 0.9)),
   ("2000-01-01", A("fiber", "itu00", (150, 160), (120, 130), "2000-06-01", "2001-01-01", 35, -3, 0.05, 0.9)),
   ("2001-09-01", A("fiber", "itu01", (160, 170), (200, 220), "2001-06-01", "2002-01-01", 5, -12, 0.30, 0.85))],
  exp("fiber-1996", [("1998-01-01", "ACTIVE"), ("2000-01-01", "WARNING"), ("2001-09-01", "KILLED")],
      "GAP", {"NEED_at_kill": "TRUE"}, "2001-09-01", 620),
  [("capacity-huger", "2000-01-01",
    A("fiber", "cf1", (300, 320), (500, 550), "2000-03-01", "2001-01-01", 5, -2, 0.05, 0.95),
    "KILLED", {"NEED": "TRUE", "GAP": "FALSE"})]),

 ("palladium-1998", "palladium", "catalyst demand + Russian constraint", 365, 500, "pal",
  [("1999-01-01", A("pal", "jmi99", (135, 145), (90, 100), "2001-06-01", "2000-01-01", 70, -2, 0.05, 0.9)),
   ("2000-06-01", A("pal", "jmi00", (140, 150), (105, 115), "2001-12-01", "2001-01-01", 60, -4, 0.35, 0.9)),
   ("2001-06-01", A("pal", "jmi01", (110, 115), (125, 135), "2001-09-01", "2002-01-01", 10, -9, 0.40, 0.85))],
  exp("palladium-1998", [("1999-01-01", "ACTIVE"), ("2000-06-01", "WARNING"), ("2001-06-01", "KILLED")],
      "GAP", {"NEED_at_kill": "TRUE"}, "2001-06-01", 365),
  [("substitution-60", "2000-06-01",
    A("pal", "cf1", (140, 150), (100, 110), "2001-12-01", "2001-01-01", 60, -4, 0.60, 0.9),
    "WARNING", {"NOSUB": "FALSE", "GAP": "TRUE"})]),

 ("china-metals-2003", "iron-ore", "China infrastructure demand", 365, 500, "ore",
  [("2005-01-01", A("ore", "bhp05", (140, 150), (95, 105), "2008-01-01", "2006-06-01", 40, -3, 0.04, 0.9)),
   ("2008-01-01", A("ore", "bhp08a", (145, 155), (110, 120), "2009-01-01", "2008-06-01", 60, -15, 0.05, 0.85)),
   ("2008-12-01", A("ore", "bhp08b", (100, 105), (115, 125), "2009-03-01", "2009-12-01", 5, -20, 0.06, 0.6))],
  exp("china-metals-2003", [("2005-01-01", "ACTIVE"), ("2008-01-01", "WARNING"), ("2008-12-01", "KILLED")],
      "GAP", {"NEED_at_kill": "TRUE"}, "2008-12-01", 335),
  [("demand-collapse", "2008-01-01",
    A("ore", "cf1", (95, 100), (110, 120), "2008-06-01", "2009-01-01", 5, -22, 0.05, 0.55),
    "KILLED", {"GAP": "FALSE"})]),

 ("uranium-2003", "uranium", "renaissance expectations + slow mines", 365, 600, "ura",
  [("2005-01-01", A("ura", "uxc05", (135, 145), (90, 100), "2009-01-01", "2006-06-01", 55, -2, 0.03, 0.85)),
   ("2007-06-01", A("ura", "uxc07", (140, 150), (105, 115), "2008-01-01", "2009-01-01", 50, -3, 0.04, 0.85)),
   ("2011-06-01", A("ura", "uxc11", (80, 85), (110, 120), "2011-09-01", "2012-01-01", -10, -25, 0.05, 0.3, relevant=False))],
  exp("uranium-2003", [("2005-01-01", "ACTIVE"), ("2007-06-01", "WARNING"), ("2011-06-01", "KILLED")],
      "NEED", {"NEED_at_kill": "FALSE"}, "2011-06-01", 1460),
  [("no-fukushima", "2011-06-01",
    A("ura", "cf1", (120, 125), (130, 140), "2011-09-01", "2012-01-01", 20, -3, 0.05, 0.8),
    "KILLED", {"NEED": "TRUE", "GAP": "FALSE"})]),

 ("rare-earths-2010", "rare-earths", "export restrictions", 180, 400, "ree",
  [("2010-06-01", A("ree", "arg10", (140, 150), (85, 95), "2012-01-01", "2011-01-01", 90, -1, 0.02, 0.9)),
   ("2011-01-01", A("ree", "arg11a", (145, 155), (100, 110), "2012-06-01", "2011-06-01", 120, -25, 0.10, 0.9)),
   ("2011-12-01", A("ree", "arg11b", (90, 95), (105, 115), "2012-03-01", "2012-06-01", 10, -15, 0.30, 0.85))],
  exp("rare-earths-2010", [("2010-06-01", "ACTIVE"), ("2011-01-01", "WARNING"), ("2011-12-01", "KILLED")],
      "GAP", {"NEED_at_kill": "TRUE"}, "2011-12-01", 335),
  [("thrifting-only", "2011-01-01",
    A("ree", "cf1", (145, 155), (100, 110), "2012-06-01", "2011-06-01", 120, -25, 0.30, 0.9),
    "WARNING", {"NOSUB": "FALSE", "GAP": "TRUE"})]),

 ("lumber-2020", "lumber", "housing demand vs idled mills", 120, 300, "lum",
  [("2020-08-01", A("lum", "risi20", (150, 160), (95, 105), "2021-06-01", "2021-01-01", 100, -2, 0.05, 0.85)),
   ("2021-03-01", A("lum", "risi21a", (145, 155), (115, 125), "2021-05-01", "2021-12-01", 80, -6, 0.06, 0.85)),
   ("2021-09-01", A("lum", "risi21b", (110, 115), (140, 150), "2021-10-01", "2022-01-01", 10, -12, 0.07, 0.8))],
  exp("lumber-2020", [("2020-08-01", "ACTIVE"), ("2021-03-01", "WARNING"), ("2021-09-01", "KILLED")],
      "GAP", {"NEED_at_kill": "TRUE"}, "2021-09-01", 184),
  [("no-restarts", "2021-03-01",
    A("lum", "cf1", (145, 155), (115, 125), "2023-01-01", "2021-12-01", 80, -6, 0.06, 0.85),
    "ACTIVE", {})]),

 ("containers-2020", "shipping", "congestion cuts effective capacity", 180, 400, "box",
  [("2021-01-01", A("box", "drew21", (150, 160), (100, 110), "2022-06-01", "2021-12-01", 120, -1, 0.05, 0.9)),
   ("2022-03-01", A("box", "drew22a", (140, 150), (115, 125), "2022-12-01", "2022-06-01", 40, -14, 0.06, 0.85)),
   ("2022-09-01", A("box", "drew22b", (110, 115), (135, 145), "2022-10-01", "2023-01-01", 5, -10, 0.07, 0.8))],
  exp("containers-2020", [("2021-01-01", "ACTIVE"), ("2022-03-01", "WARNING"), ("2022-09-01", "KILLED")],
      "GAP", {"NEED_at_kill": "TRUE"}, "2022-09-01", 184),
  [("congestion-persists", "2022-03-01",
    A("box", "cf1", (140, 150), (100, 110), "2023-01-01", "2022-06-01", 40, -14, 0.06, 0.85),
    "WARNING", {"GAP": "TRUE"})]),

 ("fertilizer-2021", "nitrogen", "gas/ammonia constraints", 180, 400, "fert",
  [("2021-09-01", A("fert", "crU21", (140, 150), (95, 105), "2023-01-01", "2022-06-01", 110, -3, 0.06, 0.85)),
   ("2022-06-01", A("fert", "crU22a", (145, 155), (120, 130), "2022-12-01", "2023-06-01", 90, -8, 0.07, 0.85)),
   ("2023-03-01", A("fert", "crU22b", (105, 110), (130, 140), "2023-04-01", "2023-09-01", 10, -11, 0.08, 0.8))],
  exp("fertilizer-2021", [("2021-09-01", "ACTIVE"), ("2022-06-01", "WARNING"), ("2023-03-01", "KILLED")],
      "GAP", {"NEED_at_kill": "TRUE"}, "2023-03-01", 273),
  [("gas-stays-high", "2022-06-01",
    A("fert", "cf1", (145, 155), (120, 130), "2024-01-01", "2023-06-01", 90, -8, 0.07, 0.85),
    "ACTIVE", {})]),
]


def _check_wtp(price, qty):
    if price >= 15 and qty > -10:
        return "TRUE"
    if price >= 15 and qty <= -10:
        return "FALSE"
    return "UNKNOWN"


if __name__ == "__main__":
    for wid, trade, thesis, interval, max_age, prefix, snaps, expected, cfs in WORLDS:
        build(wid, trade, thesis, interval, max_age, prefix, snaps,
              expected, cfs)
