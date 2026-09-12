"""Validators: every class from qpvalidate.md §14–§18.

Each returns {"name":..., "ok": bool, "detail": ...}. No network, no
clock, no randomness except seeded shuffles. Deterministic verdicts.
"""
import copy
import glob
import json
import os
import random

import yaml

from . import engine
from .engine import (PREDICATES, evaluate_snapshot, evaluate_trade,
                     evaluate_world, independent_sources)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worlds")
WORLDS = sorted(d for d in os.listdir(ROOT)
                if os.path.isdir(os.path.join(ROOT, d)))


def load_world(wid):
    d = os.path.join(ROOT, wid)
    cfg = yaml.safe_load(open(os.path.join(d, "world.yaml")))
    tl = [json.load(open(f)) for f in sorted(glob.glob(
        os.path.join(d, "timeline", "*.json")))]
    exp = json.load(open(os.path.join(d, "expected.json")))
    cfs = [json.load(open(f)) for f in sorted(glob.glob(
        os.path.join(d, "counterfactuals", "*.json")))]
    return {"world_id": cfg["world_id"], "config": cfg,
            "timeline": tl, "expected": exp, "counterfactuals": cfs}


def _kill_signal(receipt):
    cs = receipt["claim_states"]
    return "NEED" if cs["NEED"] == "FALSE" else "GAP"


def check_world(wid):
    """Timeline vs frozen expected states + signal + invariant + timing."""
    w = load_world(wid)
    receipts = evaluate_world(w)
    by_date = {r["as_of"]: r for r in receipts}
    exp = w["expected"]
    for s in exp["expected_states"]:
        r = by_date.get(s["as_of"])
        if r is None or r["state_after"] != s["trade"]:
            return {"ok": False, "world": wid,
                    "detail": f"{s['as_of']}: expected {s['trade']}, "
                              f"got {r['state_after'] if r else 'missing'}"}
    kills = [r for r in receipts if r["state_after"] == "KILLED"]
    first_kill = kills[0] if kills else None
    if first_kill and _kill_signal(first_kill) != exp["expected_first_kill_signal"]:
        return {"ok": False, "world": wid, "detail": "wrong kill signal"}
    for k, v in exp.get("required_invariant", {}).items():
        pred = k[:-len("_at_kill")] if k.endswith("_at_kill") else k
        if first_kill and first_kill["claim_states"].get(pred) != v:
            return {"ok": False, "world": wid,
                    "detail": f"invariant {k} violated"}
    if kills:
        from datetime import date as _date
        delay = (_date.fromisoformat(kills[0]["as_of"])
                 - _date.fromisoformat(exp["earliest_kill_date"])).days
        if delay < 0 or delay > exp.get("max_delay_days", 31):
            return {"ok": False, "world": wid,
                    "detail": f"detection delay {delay}d out of bounds"}
    for cf in w["counterfactuals"]:
        r = evaluate_snapshot(
            w, {"date": cf["date"], "evidence": cf["evidence"]})
        if r["state_after"] != cf["expected_trade"]:
            return {"ok": False, "world": wid,
                    "detail": f"counterfactual {cf['date']}: "
                              f"expected {cf['expected_trade']}, "
                              f"got {r['state_after']}"}
        for p, v in cf.get("expected_predicates", {}).items():
            if r["claim_states"].get(p) != v:
                return {"ok": False, "world": wid,
                        "detail": f"counterfactual predicate {p}"}
    return {"ok": True, "world": wid,
            "detail": f"{len(receipts)} snapshots, kill "
                      f"{first_kill['as_of'] if first_kill else 'none'}"}


def v_all_worlds():
    bad = []
    for wid in WORLDS:
        r = check_world(wid)
        if not r["ok"]:
            bad.append(f"{wid}: {r['detail']}")
    return {"name": "worlds", "ok": not bad,
            "detail": f"{len(WORLDS) - len(bad)}/{len(WORLDS)}" +
                      ("" if not bad else f" FAIL {bad}")}


def v_precision():
    """0 false hard kills, 0 missed hard kills across all worlds."""
    false_kills = missed_kills = 0
    for wid in WORLDS:
        w = load_world(wid)
        receipts = {r["as_of"]: r for r in evaluate_world(w)}
        for s in w["expected"]["expected_states"]:
            got = receipts[s["as_of"]]["state_after"]
            if got == "KILLED" and s["trade"] != "KILLED":
                false_kills += 1
            if s["trade"] == "KILLED" and got != "KILLED":
                missed_kills += 1
    return {"name": "precision", "ok": not (false_kills or missed_kills),
            "detail": f"false={false_kills} missed={missed_kills}"}


def _receipt_hash(r):
    from acom.canonical import canonical, sha256_hex
    return sha256_hex(canonical({k: v for k, v in r.items()
                                 if k != "_meta"}))


def v_determinism(n=100):
    mism = 0
    for wid in WORLDS:
        w = load_world(wid)
        base = [_receipt_hash(r) for r in evaluate_world(w)]
        for _ in range(n):
            if [_receipt_hash(r) for r in evaluate_world(w)] != base:
                mism += 1
                break
    return {"name": "determinism", "ok": mism == 0,
            "detail": f"{n} reruns/world, mismatches={mism}"}


def v_no_future_leak():
    for wid in WORLDS:
        w = load_world(wid)
        for snap in w["timeline"] + [
                {"date": c["date"], "evidence": c["evidence"]}
                for c in w["counterfactuals"]]:
            for e in snap["evidence"]:
                if e["as_of"] > snap["date"]:
                    return {"name": "no_future_leak", "ok": False,
                            "detail": f"{wid}: {e['evidence_id']}"}
    return {"name": "no_future_leak", "ok": True, "detail": "clean"}


def v_unknown_semantics():
    """Delete required evidence → UNKNOWN, never FALSE/KILLED."""
    w = load_world("dram-1987")
    snap = copy.deepcopy(w["timeline"][0])
    snap["evidence"] = [e for e in snap["evidence"]
                        if not e["metric"].endswith(
                            ("_demand", "_supply"))]
    r = evaluate_snapshot(w, snap)
    ok = r["state_after"] == "UNKNOWN" and r["claim_states"]["GAP"] == "UNKNOWN"
    return {"name": "unknown_semantics", "ok": ok,
            "detail": f"got {r['state_after']}/{r['claim_states']['GAP']}"}


def v_source_failure():
    """Corrupt provenance → excluded → UNKNOWN, never zero/FALSE."""
    w = load_world("dram-1987")
    snap = copy.deepcopy(w["timeline"][0])
    for e in snap["evidence"]:
        if e["metric"].endswith(("_demand", "_supply")):
            e["source"] = {"source_id": e["source"]["source_id"],
                           "class": "industry_data"}  # artifact dropped
    r = evaluate_snapshot(w, snap)
    ok = (r["state_after"] == "UNKNOWN"
          and len(r["_meta"]["rejected"]) >= 2)
    return {"name": "source_failure", "ok": ok,
            "detail": f"got {r['state_after']}, "
                      f"rejected={len(r['_meta']['rejected'])}"}


def v_duplicates():
    """Five copies of one source count as ONE independent source."""
    w = load_world("dram-1987")
    base = [e for e in w["timeline"][0]["evidence"]
            if e["metric"].endswith(("_demand", "_supply"))][:1]
    copies = []
    for i in range(5):
        c = copy.deepcopy(base[0])
        c["evidence_id"] = f"dup-{i}"
        copies.append(c)
    n = independent_sources(copies)
    if n != 1:
        return {"name": "duplicates", "ok": False, "detail": f"count={n}"}
    snap = {"date": "1987-06-01", "evidence": copies}
    cfg = copy.deepcopy(w["config"])
    cfg["predicates"]["GAP"]["min_sources"] = 2
    w2 = dict(w, config=cfg)
    r = evaluate_snapshot(w2, snap)
    ok = r["claim_states"]["GAP"] == "UNKNOWN"
    return {"name": "duplicates", "ok": ok,
            "detail": f"independent={n}, gap={r['claim_states']['GAP']}"}


def v_mutation():
    """Inverted GAP logic MUST break the suite (else coverage is fake)."""
    bad_worlds = 0
    for wid in WORLDS:
        w = load_world(wid)
        receipts = {r["as_of"]: r for r in
                    evaluate_world(w, mutations={"GAP": {"invert": True}})}
        for s in w["expected"]["expected_states"]:
            if receipts[s["as_of"]]["state_after"] != s["trade"]:
                bad_worlds += 1
                break
    if bad_worlds == 0:
        return {"name": "mutation", "ok": False,
                "detail": "inverted gates still green — fake harness"}
    w = load_world("dram-1987")
    receipts = {r["as_of"]: r for r in
                evaluate_world(w, mutations={"GAP": {"threshold": 1000.0}})}
    absurd_breaks = any(
        receipts[s["as_of"]]["state_after"] != s["trade"]
        for s in w["expected"]["expected_states"])
    ok = absurd_breaks
    return {"name": "mutation", "ok": ok,
            "detail": f"invert breaks {bad_worlds} worlds, "
                      f"absurd-threshold breaks dram={absurd_breaks}"}


def v_order_independence():
    for wid in WORLDS:
        w = load_world(wid)
        base = [_receipt_hash(r) for r in evaluate_world(w)]
        for seed in range(5):
            w2 = copy.deepcopy(w)
            rng = random.Random(seed)
            for s in w2["timeline"]:
                rng.shuffle(s["evidence"])
            if [_receipt_hash(r) for r in evaluate_world(w2)] != base:
                return {"name": "order", "ok": False,
                        "detail": f"{wid} seed {seed}"}
    return {"name": "order", "ok": True, "detail": "5 shuffles/world stable"}


def v_dependency():
    """Child flip recomputes parent automatically (stateless engine)."""
    all_true = {p: "TRUE" for p in PREDICATES}
    if evaluate_trade(all_true) != "ACTIVE":
        return {"name": "dependency", "ok": False, "detail": "baseline"}
    flipped = dict(all_true, NOSUB="FALSE")
    if evaluate_trade(flipped) != "WARNING":
        return {"name": "dependency", "ok": False, "detail": "no recompute"}
    w = load_world("dram-1987")
    snap = copy.deepcopy(w["timeline"][1])
    snap["evidence"] = (
        [e for e in snap["evidence"] if e["metric"] != "dram_close"] + [{
            "evidence_id": "dep-probe", "metric": "dram_close",
            "value": "1995-01-01", "unit": "date", "as_of": "1988-06-01",
            "source": {"source_id": "probe", "class": "industry_data",
                       "artifact_hash": "sha256:999"},
            "extraction": {"extractor": "manual", "extractor_version": "1",
                           "reviewed": True}}])
    r = evaluate_snapshot(w, snap)
    ok = r["state_after"] == "ACTIVE" and r["claim_states"]["LAG"] == "TRUE"
    return {"name": "dependency", "ok": ok,
            "detail": f"lag-flip recomputes to {r['state_after']}"}


def v_adversarial():
    """Narrative / conflicting / stale / fake-authority attacks."""
    w = load_world("dram-1987")
    cfg = w["config"]
    mk = lambda items, date="1988-06-01": {"date": date, "evidence": items}
    base = {e["metric"]: e for e in w["timeline"][0]["evidence"]}

    r = evaluate_snapshot(w, mk([]))
    if r["state_after"] != "UNKNOWN":
        return {"name": "adversarial", "ok": False, "detail": "narrative moved state"}

    overlap = [dict(base["dram_demand"], value={"low": 100, "high": 120}),
               dict(base["dram_supply"], value={"low": 110, "high": 130})]
    r = evaluate_snapshot(w, mk(overlap))
    if r["claim_states"]["GAP"] != "UNKNOWN":
        return {"name": "adversarial", "ok": False, "detail": "conflict forced verdict"}

    old = dict(base["dram_demand"], as_of="1980-01-01")
    old2 = dict(base["dram_supply"], as_of="1980-01-01")
    cfg2 = copy.deepcopy(cfg)
    cfg2["max_age_days"] = 30
    w2 = dict(w, config=cfg2)
    r = evaluate_snapshot(w2, mk([old, old2]))
    if not (r["state_after"] == "UNKNOWN" and r["_meta"]["stale"]):
        return {"name": "adversarial", "ok": False, "detail": "stale accepted"}

    fake = dict(base["dram_demand"],
                source={"source_id": "x", "class": "government"})
    r = evaluate_snapshot(w, mk([fake, base["dram_supply"]]))
    if not (r["claim_states"]["GAP"] == "UNKNOWN"
            and r["_meta"]["rejected"]):
        return {"name": "adversarial", "ok": False, "detail": "fake authority scored"}
    return {"name": "adversarial", "ok": True, "detail": "4/4 attacks absorbed"}


def v_schemas():
    req_ev = ("evidence_id", "metric", "value", "unit", "as_of", "source",
              "extraction")
    req_src = ("source_id", "class", "artifact_hash")
    for wid in WORLDS:
        w = load_world(wid)
        for key in ("world_id", "trade", "interval_days", "max_age_days",
                    "thesis", "predicates"):
            if key not in w["config"]:
                return {"name": "schemas", "ok": False,
                        "detail": f"{wid} world.yaml missing {key}"}
        for snap in w["timeline"]:
            for e in snap["evidence"]:
                if any(k not in e for k in req_ev):
                    return {"name": "schemas", "ok": False,
                            "detail": f"{wid} evidence keys"}
                if any(k not in e["source"] for k in req_src):
                    return {"name": "schemas", "ok": False,
                            "detail": f"{wid} source keys"}
                if e["source"]["class"] not in engine.ALLOWED_SOURCE_CLASSES:
                    return {"name": "schemas", "ok": False,
                            "detail": f"{wid} bad class"}
        for k in ("world_id", "expected_states", "expected_first_kill_signal",
                  "required_invariant", "earliest_kill_date", "max_delay_days"):
            if k not in w["expected"]:
                return {"name": "schemas", "ok": False,
                        "detail": f"{wid} expected.json missing {k}"}
    return {"name": "schemas", "ok": True, "detail": "fixtures shaped"}


def v_replay():
    """Every evaluation receipt lands in the acom store; chain verifies;
    replayed count matches."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    ".."))
    from acom import store as store_mod
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "runs", "killfeed", "events.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    st = store_mod.Store(path)
    n = 0
    for wid in WORLDS:
        for r in evaluate_world(load_world(wid)):
            st.append("evaluation", {"receipt": _receipt_hash(r),
                                     "world": wid,
                                     "state": r["state_after"]})
            n += 1
    ok_chain = st.verify_chain()
    counted = st.replay(lambda acc, t, p: acc + 1
                        if t == "evaluation" else acc, 0)
    ok = ok_chain and counted == n
    return {"name": "replay", "ok": ok,
            "detail": f"{counted}/{n} replayed, chain={ok_chain}"}
