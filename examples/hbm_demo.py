"""Demo 1 (northstar §42): one Killfeed HBM claim through the kernel.

Claim: memory.hbm.gap (qualified HBM demand exceeds effective supply).
Evidence: two items, distinct source classes (producer_guidance,
channel_checks) — satisfies two-sources-v1 honestly.
Resolve TRUE at proof level V7 (canonical economic claim).
Writes: runs/hbm-claim/receipt.json + evidence.json. Returns receipt.
"""
import json
import os

from acom import gates, objects, receipts, store

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "runs", "hbm-claim")


def run(store_path: str = "") -> dict:
    claim = objects.make_claim(
        "Qualified HBM demand exceeds effective qualified supply.",
        "semiconductors.memory", result="UNKNOWN")
    ev1 = objects.make_evidence("qualified_hbm_supply", 102,
                                "normalized_capacity", "2026-09-12",
                                {"class": "producer_guidance",
                                 "artifact_hash": "sha256:aaa"})
    ev2 = objects.make_evidence("qualified_hbm_demand", 131,
                                "normalized_capacity", "2026-09-12",
                                {"class": "channel_checks",
                                 "artifact_hash": "sha256:bbb"})
    evidence = [ev1, ev2]
    decided = dict(claim, result="TRUE")  # cognition proposes; gates dispose

    def apply(state_before, proposal, ev):
        nxt = dict(state_before)
        nxt["cursor"] = state_before["cursor"] + 1
        nxt["claims"] = {**state_before.get("claims", {}),
                         decided["id"]: decided["result"]}
        return nxt

    st = store.Store(store_path or os.path.join(OUT, "events.jsonl"))
    before = {"cursor": st.cursor, "rules_commit": "demo",
              "event_root": st.event_root, "state_root": st.event_root}
    proposal = {"id": claim["id"], "target": claim["id"], "claim": decided,
                "grant": None}
    run = objects.make_run("task:demo-hbm", "demo-worker", "demo",
                           inputs_root="demo")
    rec = receipts.transition(
        before, proposal, evidence,
        ["evidence-fresh-v1", "no-duplicate-v1", "two-sources-v1",
         "claim-resolved-v1"],
        run, proof_level=7, transition_type="RESOLVE", apply=apply)
    st.append("transition", {"receipt": rec["id"], "passed": rec["passed"],
                             "subject": rec["subject"]})
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(os.path.join(OUT, "receipt.json"), "w"),
              sort_keys=True, indent=2)
    json.dump(evidence, open(os.path.join(OUT, "evidence.json"), "w"),
              sort_keys=True, indent=2)
    print(json.dumps({"demo": "hbm-claim", "receipt": rec["id"],
                      "passed": rec["passed"],
                      "settle": receipts.settle(rec, evidence)}))
    return rec


if __name__ == "__main__":
    run()
