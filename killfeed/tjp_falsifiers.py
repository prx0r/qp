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
                             "rating": t.get("rating"),
                             "body": str(t.get("body", ""))})
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


def ratings_as_priors(rows: list) -> dict:
    """Desk ratings (explicit `8.9/10` markers in the thesis record) → EI
    impact priors in (0,1]. The /10 suffix is required: bare decimals
    appear in prose and would invent scores. Unrated theses sort last
    at 0.0 rather than inventing weight."""
    import json
    import re
    out = {}
    for r in rows:
        m = re.search(r"(\d\.\d)\s*/\s*10", json.dumps(r))
        out[r["thesis"]] = round(float(m.group(1)) / 10, 3) if m else 0.0
    return out
