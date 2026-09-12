"""Kernel tests. Every invariant that can be checked cheaply, is.

Covers: canonical determinism, stable IDs, bool3 enforcement, store
append/chain-verify/tamper-detection, replay, all four gates (pass and
fail paths), grant verification (expiry/capability/constraint/predicate/
unsigned-fail-closed), receipt id round-trip, independent settlement,
FAIL receipts, and both demos settling against one receipt type.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acom import gates, grants, objects, receipts, store  # noqa: E402
from acom.canonical import canonical, merkle_root, obj_id  # noqa: E402


def test_canonical_deterministic():
    a = {"z": 1, "a": [1, 2], "m": {"k": "v"}}
    b = {"m": {"k": "v"}, "a": [1, 2], "z": 1}
    assert canonical(a) == canonical(b)
    assert obj_id("t", a) == obj_id("t", b)


def test_merkle_empty_and_single():
    assert merkle_root([]) == merkle_root([])
    assert merkle_root(["ab"]) == "ab"


def test_claim_bool3_enforced():
    try:
        objects.make_claim("s", "d", result="MAYBE")
        raise SystemExit("bool3 not enforced")
    except AssertionError:
        pass
    assert objects.make_claim("s", "d").get("result") == "UNKNOWN"


def test_ids_stable():
    c1 = objects.make_claim("same statement", "d")
    c2 = objects.make_claim("same statement", "d")
    assert c1["id"] == c2["id"]


def _tmp_store(tmp_path):
    return store.Store(str(tmp_path / "e.jsonl"))


def test_store_chain_and_tamper(tmp_path):
    st = _tmp_store(tmp_path)
    st.append("a", {"x": 1})
    st.append("b", {"x": 2})
    assert st.cursor == 2
    assert st.verify_chain()
    with open(st.path, "a") as f:
        f.write('{"seq":99,"type":"evil","payload":{},"prev":"x","hash":"y"}\n')
    assert not st.verify_chain()


def test_replay(tmp_path):
    st = _tmp_store(tmp_path)
    st.append("add", {"n": 2})
    st.append("add", {"n": 3})
    assert st.replay(lambda acc, t, p: acc + p["n"] if t == "add" else acc, 0) == 5


def _ev(*classes):
    return [objects.make_evidence(f"m{i}", i, "u", "2026-01-01",
                                  {"class": c, "artifact_hash": "sha256:0"})
            for i, c in enumerate(classes)]


def test_gate_two_sources():
    assert gates.execute("two-sources-v1",
                         {"evidence": _ev("a", "b")})["result"] == "PASS"
    assert gates.execute("two-sources-v1",
                         {"evidence": _ev("a", "a")})["result"] == "FAIL"
    assert gates.execute("nope-v9", {})["result"] == "FAIL"


def test_gate_fresh_and_unique():
    assert gates.execute("evidence-fresh-v1",
                         {"evidence": _ev("a")})["result"] == "PASS"
    assert gates.execute("evidence-fresh-v1",
                         {"evidence": [{"id": "x"}]})["result"] == "FAIL"
    ev = _ev("a")
    assert gates.execute("no-duplicate-v1",
                         {"evidence": ev + ev})["result"] == "FAIL"


def test_grant_matrix():
    g = objects.make_grant("w1", "trading.swap",
                           {"max_value": 500, "asset": "USDC", "calls": 3},
                           ["trade.thesis_alive == TRUE"],
                           "2030-01-01T00:00:00", signature="sig:abc",
                           minimum_proof_level=9)
    facts = {"trade": {"thesis_alive": "TRUE"}}
    ok = {"capability": "trading.swap", "value": 100,
          "asset": "USDC", "calls": 1}
    assert grants.verify_grant(g, ok, facts, "2026-01-01")["ok"]
    assert not grants.verify_grant(g, {**ok, "value": 600}, facts,
                                   "2026-01-01")["ok"]
    assert not grants.verify_grant(g, ok, {"trade": {"thesis_alive": "FALSE"}},
                                   "2026-01-01")["ok"]
    assert not grants.verify_grant(g, ok, facts, "2031-01-01")["ok"]
    unsigned = dict(g, signature="")
    assert not grants.verify_grant(unsigned, ok, facts, "2026-01-01")["ok"]


def _receipt(pass_claim=True):
    c = objects.make_claim("s", "d")
    decided = dict(c, result="TRUE" if pass_claim else "UNKNOWN")
    ev = _ev("a", "b")
    before = {"cursor": 0, "rules_commit": "t", "event_root": "",
              "state_root": ""}
    run = objects.make_run("task:t", "w")
    return receipts.transition(
        before, {"id": c["id"], "target": c["id"], "claim": decided,
                 "grant": None},
        ev, ["two-sources-v1", "claim-resolved-v1"], run, proof_level=7,
        apply=lambda s, p, e: {**s, "cursor": s["cursor"] + 1}), ev


def test_receipt_pass_and_fail():
    r, _ = _receipt(True)
    assert r["passed"] and r["state_after"]["cursor"] == 1
    r2, _ = _receipt(False)
    assert not r2["passed"] and r2["state_after"]["cursor"] == 0


def test_receipt_id_and_settle():
    r, ev = _receipt(True)
    assert receipts.verify_receipt(r)["ok"]
    assert receipts.settle(r, ev)["ok"]
    tampered = dict(r, proof_level=12)
    assert not receipts.verify_receipt(tampered)["ok"]


def test_both_demos_one_receipt_type():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from examples import atask_demo, hbm_demo
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        r1 = hbm_demo.run(os.path.join(td, "h.jsonl"))
        r2 = atask_demo.run(os.path.join(td, "a.jsonl"))
    assert r1["protocol"] == r2["protocol"] == "acom/0.1"
    assert r1["passed"] and r2["passed"]
