"""Demo 2: one ORDINARY atask through the SAME kernel and receipt type.

Task: back up a mailbox file before migration (kind BACKUP_VERIFY).
Evidence: source manifest hash + destination manifest hash, distinct
source classes (mailbox_manifest, backup_manifest).
Resolve TRUE at proof level V4 (local derived metric). If this and the
HBM demo both settle against the same TransitionReceipt, the kernel
abstraction is real (northstar §42).
Writes: runs/atask-demo/receipt.json + evidence.json. Returns receipt.
"""
import json
import os

from acom import objects, receipts, store

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "runs", "atask-demo")


def run(store_path: str = "") -> dict:
    claim = objects.make_claim(
        "Mailbox backup matches source manifest exactly.",
        "ops.backup", result="UNKNOWN")
    ev1 = objects.make_evidence("source_manifest", "sha256:111",
                                "hash", "2026-09-12",
                                {"class": "mailbox_manifest",
                                 "artifact_hash": "sha256:111"})
    ev2 = objects.make_evidence("dest_manifest", "sha256:111",
                                "hash", "2026-09-12",
                                {"class": "backup_manifest",
                                 "artifact_hash": "sha256:222"})
    evidence = [ev1, ev2]
    decided = dict(claim, result="TRUE")

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
    run = objects.make_run("task:demo-atask", "demo-worker", "demo",
                           inputs_root="demo")
    rec = receipts.transition(
        before, proposal, evidence,
        ["evidence-fresh-v1", "no-duplicate-v1", "two-sources-v1",
         "claim-resolved-v1"],
        run, proof_level=4, transition_type="RESOLVE", apply=apply)
    st.append("transition", {"receipt": rec["id"], "passed": rec["passed"],
                             "subject": rec["subject"]})
    os.makedirs(OUT, exist_ok=True)
    json.dump(rec, open(os.path.join(OUT, "receipt.json"), "w"),
              sort_keys=True, indent=2)
    json.dump(evidence, open(os.path.join(OUT, "evidence.json"), "w"),
              sort_keys=True, indent=2)
    print(json.dumps({"demo": "atask-backup", "receipt": rec["id"],
                      "passed": rec["passed"],
                      "settle": receipts.settle(rec, evidence)}))
    return rec


if __name__ == "__main__":
    run()
