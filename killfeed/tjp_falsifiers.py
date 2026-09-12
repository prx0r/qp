"""TJP falsifier corpus → swarm FALSIFY seeds (postreview.md §4).

The thesis desk's 74 falsifier-bearing theses are pre-shaped attack
material: each names a claim plus what would kill it. This loader turns
them into A-COM FALSIFY tasks so the swarm works them instead of
admiring them. Source files live in vendor/tjp-agitheses (imported).
"""
import glob
import json
import os

from acom import objects

CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                      "vendor", "tjp-agitheses")


def load_corpus(path: str = "") -> list:
    """All {memo, thesis, falsifier, rating} rows with falsifiers."""
    rows = []
    for f in sorted(glob.glob(os.path.join(path or CORPUS, "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for t in d.get("theses", []) or []:
            if t.get("falsifier"):
                rows.append({"memo": d.get("subject", "?")[:60],
                             "thesis": t.get("title", "?"),
                             "falsifier": t.get("falsifier"),
                             "rating": t.get("rating")})
    seen, out = set(), []
    for r in rows:  # memos repeat; dedupe on thesis text
        if r["thesis"] not in seen:
            seen.add(r["thesis"])
            out.append(r)
    return out


def to_jobs(rows: list, target: str = "open") -> list:
    """Falsifier rows → FALSIFY tasks aimed at `target` (a claim id or
    'open' for the shared pool). Acceptance names the falsifier, so a
    worker knows exactly what would kill the thesis."""
    jobs = []
    for r in rows:
        jobs.append(objects.make_task(
            "FALSIFY", target,
            {"thesis": r["thesis"][:160],
             "falsifier": str(r["falsifier"])[:300],
             "rating": r["rating"],
             "need": "hard evidence for OR against the falsifier"}))
    return jobs
