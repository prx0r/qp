"""verify_all: the Definition of Done, machine-executed.

Usage: python -m killfeed.verify_all [--quick]
--quick runs determinism at 5 reruns (for iteration); full runs demand 100.
Exit 0 with STATUS: PROVEN only if everything passes. Anything else is
IMPLEMENTED_UNVERIFIED. Writes runs/killfeed/certificate.json.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from killfeed import validators as V  # noqa: E402

SHORT = {"oil-1979": "oil-1979", "dram-1987": "dram-1987",
         "fiber-1996": "fiber-1996", "palladium-1998": "palladium-1998",
         "china-metals-2003": "china-metals-2003",
         "uranium-2003": "uranium-2003",
         "rare-earths-2010": "rare-earths-2010", "lumber-2020": "lumber-2020",
         "containers-2020": "containers-2020",
         "fertilizer-2021": "fertilizer-2021"}
W = 21


def main() -> int:
    """The Definition of Done, machine-executed. Exit 0 + PROVEN only if
    everything passes; anything else is IMPLEMENTED_UNVERIFIED."""
    quick = "--quick" in sys.argv
    rows = []
    core = [("SCHEMAS", V.v_schemas()),
            ("DETERMINISM", V.v_determinism(5 if quick else 100)),
            ("REPLAY", V.v_replay()),
            ("NO_FUTURE_LEAK", V.v_no_future_leak()),
            ("UNKNOWN_SEMANTICS", V.v_unknown_semantics()),
            ("SOURCE_FAILURE", V.v_source_failure()),
            ("SOURCE_LINEAGE", V.v_duplicates()),
            ("MUTATION", V.v_mutation()),
            ("DEPENDENCY_RECOMPUTE", V.v_dependency()),
            ("ADVERSARIAL", V.v_adversarial())]
    rows += [(n, r["ok"]) for n, r in core]
    worlds = V.v_all_worlds()
    wres = {}
    for wid in V.WORLDS:
        r = V.check_world(wid)
        wres[wid] = r["ok"]
    prec = V.v_precision()
    det = next(r for n, r in core if n == "DETERMINISM")

    print("CORE")
    for n, r in core:
        print(f"{n:<21}{'PASS' if r['ok'] else 'FAIL'}")
    print("\nHISTORICAL WORLDS:")
    for wid in V.WORLDS:
        print(f"{SHORT[wid]:<21}{'PASS' if wres[wid] else 'FAIL'}")
    print(f"\n{'WORLD PASS RATE':<21}{sum(wres.values())}/{len(wres)}")
    print(f"{'FALSE HARD KILLS':<21}{0 if prec['ok'] else '?'}")
    print(f"{'MISSED HARD KILLS':<21}{0 if prec['ok'] else '?'}")
    print(f"{'HASH MISMATCHES':<21}{0 if det['ok'] else '?'}")
    proven = (all(ok for _, ok in rows) and all(wres.values())
              and prec["ok"] and worlds_ok(worlds))
    print(f"\nSTATUS: {'PROVEN' if proven else 'IMPLEMENTED_UNVERIFIED'}")

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True,
            text=True, cwd=os.path.dirname(os.path.abspath(__file__))
            ).stdout.strip() or "uncommitted"
    except Exception:
        commit = "uncommitted"
    cert = {
        "system": "acom-killfeed", "version": "0.1",
        "implementation_commit": commit,
        "worlds": {"total": len(wres),
                   "passed": sum(wres.values()),
                   "failed": len(wres) - sum(wres.values())},
        "determinism": {"reruns_per_world": 5 if quick else 100,
                        "hash_mismatches": 0 if det["ok"] else -1},
        "kill_detection": {"false_hard_kills": 0 if prec["ok"] else -1,
                           "missed_hard_kills": 0 if prec["ok"] else -1},
        "adversarial": {"future_leak": "PASS" if _ok(rows, "NO_FUTURE_LEAK") else "FAIL",
                        "source_failure": "PASS" if _ok(rows, "SOURCE_FAILURE") else "FAIL",
                        "unknown_semantics": "PASS" if _ok(rows, "UNKNOWN_SEMANTICS") else "FAIL",
                        "duplicate_source": "PASS" if _ok(rows, "SOURCE_LINEAGE") else "FAIL",
                        "gate_mutation": "PASS" if _ok(rows, "MUTATION") else "FAIL"},
        "status": "PROVEN" if proven else "IMPLEMENTED_UNVERIFIED",
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "runs", "killfeed", "certificate.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(cert, open(out, "w"), sort_keys=True, indent=2)
    return 0 if proven else 1


def _ok(rows, name):
    return next(ok for n, ok in rows if n == name)


def worlds_ok(w):
    """Narrow helper so the PROVEN verdict reads as a sentence."""
    return w["ok"]


if __name__ == "__main__":
    raise SystemExit(main())
