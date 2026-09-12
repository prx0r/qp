"""A-COM CLI. Thin shell over the kernel; adds no semantics.

  python3 -m acom.cli init <dir>          fresh store + rules commit
  python3 -m acom.cli demo                HBM claim + generic task, end to end
  python3 -m acom.cli verify <receipt> <evidence>
                                          id check + full gate re-settlement
  python3 -m acom.cli chain <store>       hash-chain verification
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acom import store as store_mod  # noqa: E402
from acom.receipts import settle, verify_receipt  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(prog="acom")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("dir")
    sub.add_parser("demo")
    p = sub.add_parser("verify")
    p.add_argument("receipt"); p.add_argument("evidence")
    p = sub.add_parser("chain"); p.add_argument("store")
    a = ap.parse_args()

    if a.cmd == "init":
        os.makedirs(a.dir, exist_ok=True)
        open(os.path.join(a.dir, "events.jsonl"), "a").close()
        print(json.dumps({"ok": True, "store": a.dir + "/events.jsonl"}))
        return 0
    if a.cmd == "demo":
        from examples import hbm_demo, atask_demo
        r1 = hbm_demo.run()
        r2 = atask_demo.run()
        print(json.dumps({"ok": True,
                          "hbm": {"id": r1["id"], "passed": r1["passed"]},
                          "atask": {"id": r2["id"], "passed": r2["passed"]}}))
        return 0 if (r1["passed"] and r2["passed"]) else 1
    if a.cmd == "verify":
        rec = json.load(open(a.receipt))
        ev = json.load(open(a.evidence))
        print(json.dumps(settle(rec, ev)))
        return 0
    if a.cmd == "chain":
        print(json.dumps(
            {"ok": store_mod.Store(a.store).verify_chain()}))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
