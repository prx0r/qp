"""Waiting room (atunomousgoal §18): breakthrough feed with lag detection.

Log the shock, emit the impact map immediately, then compare each
predicted move against market response evidence as it arrives. A
predicted consequence with no market response after its window is a
lag candidate — the only thing agents investigate. Small, append-only,
deterministic.
"""
from . import classes


def log_breakthrough(store: list, bid: str, date: str, moves: dict) -> dict:
    """Append a breakthrough event. Returns the logged record."""
    vec = classes.encode(moves)
    rec = {"id": bid, "t0": date, "vector": vec,
           "signs": classes.sign(vec),
           "long_leg": classes.amplified(vec),
           "short_leg": classes.destroyed(vec),
           "responses": {}, "t_star": None}
    store.append(rec)
    return rec


def record_response(store: list, bid: str, constraint: str, date: str,
                    moved: bool):
    """Market evidence: did the predicted constraint respond?"""
    rec = next(r for r in store if r["id"] == bid)
    rec["responses"][constraint] = {"date": date, "moved": moved}


def lag_candidates(store: list, bid: str, window_days: int = 90) -> list:
    """Predicted moves with no confirming market response inside the
    window (or an explicit non-move): investigate these, nothing else."""
    from datetime import date as _date
    rec = next(r for r in store if r["id"] == bid)
    t0 = _date.fromisoformat(rec["t0"])
    out = []
    for c in rec["long_leg"] + rec["short_leg"]:
        r = rec["responses"].get(c)
        if r is None:
            out.append({"constraint": c, "status": "UNOBSERVED"})
        elif not r["moved"] and (_date.fromisoformat(r["date"]) - t0).days <= window_days:
            out.append({"constraint": c, "status": "LAGGED",
                        "as_of": r["date"]})
    return out


def close_window(store: list, bid: str, t_star: str):
    rec = next(r for r in store if r["id"] == bid)
    rec["t_star"] = t_star
    return rec
