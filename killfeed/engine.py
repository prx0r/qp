"""Killfeed engine: five predicates, deterministic gates, trade states.

Implements qpvalidate.md §1–§4, §8–§10. Pure functions only: no network,
no clock, no randomness. Same inputs → byte-identical outputs (tested at
100 reruns per world). An LLM may never override `evaluate_trade`.
"""

from acom.canonical import canonical, merkle_root, sha256_hex

PREDICATES = ("NEED", "GAP", "LAG", "WTP", "NOSUB")
TRADE_STATES = ("ACTIVE", "WARNING", "KILLED", "UNKNOWN")
ENGINE_VERSION = "killfeed-engine/0.1"

ALLOWED_SOURCE_CLASSES = ("government", "filing", "company_guidance",
                           "industry_data", "academic", "news", "other")


# --- evidence plumbing -------------------------------------------------

def provenance_ok(ev: dict) -> bool:
    """Provenance contract: accepted class + real artifact hash.
    Anything else is REJECTED (never scored, never zero)."""
    src = ev.get("source", {}) if isinstance(ev, dict) else {}
    if not isinstance(src, dict):
        return False
    art = src.get("artifact_hash", "")
    return (src.get("class") in ALLOWED_SOURCE_CLASSES
            and isinstance(art, str) and art.startswith("sha256:")
            and len(art) > 7)


def admissible(evidence: list, as_of: str, max_age_days: int):
    """Split evidence into (usable, rejected, stale) for snapshot date."""
    from datetime import date as _date
    usable, rejected, stale = [], [], []
    t = _date.fromisoformat(as_of)
    for e in evidence:
        if not provenance_ok(e):
            rejected.append(e.get("evidence_id", "?"))
            continue
        try:
            age = (t - _date.fromisoformat(e["as_of"])).days
        except Exception:
            rejected.append(e.get("evidence_id", "?"))
            continue
        if age < 0 or age > max_age_days:
            stale.append(e.get("evidence_id", "?"))
            continue
        usable.append(e)
    return usable, rejected, stale


def _vals(usable: list, metric: str):
    """All (low, high, source_id) for a metric. Scalars become points.
    Non-numeric values (dates, bools) pass through raw."""
    out = []
    for e in usable:
        if e.get("metric") != metric:
            continue
        v = e.get("value")
        sid = e["source"]["source_id"]
        if isinstance(v, dict):
            out.append((_num(v["low"]), _num(v["high"]), sid))
        else:
            out.append((_num(v), _num(v), sid))
    return out


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def independent_sources(usable: list) -> int:
    """Distinct source_ids. Five copies of one report count as ONE."""
    return len({e["source"]["source_id"] for e in usable
                if isinstance(e.get("source"), dict)})


# --- gate templates (§9). Each returns (state, margin, reason, used) ---

def gate_gap(vals_d, vals_s, threshold=1.0, invert=False):
    if not vals_d or not vals_s:
        return ("UNKNOWN", None, "missing demand or supply", [])
    dl = min(v[0] for v in vals_d)
    dh = max(v[1] for v in vals_d)
    sl = min(v[0] for v in vals_s)
    sh = max(v[1] for v in vals_s)
    if dl > sh * threshold:
        r = ("TRUE", dl - sh * threshold, "demand_low > supply_high")
    elif dh <= sl:
        r = ("FALSE", sl - dh, "demand_high <= supply_low")
    else:
        return ("UNKNOWN", None, "ranges overlap", [])
    if invert:
        r = ("FALSE" if r[0] == "TRUE" else "TRUE", r[1], r[2] + " [inverted]")
    return r[0], r[1], r[2], []


def gate_lag(close, horizon):
    if close is None or horizon is None:
        return ("UNKNOWN", None, "missing dates", [])
    if close > horizon:
        return ("TRUE", None, "gap closes after horizon", [])
    return ("FALSE", None, "gap closes inside horizon", [])


def gate_wtp(price, qty, x=15.0, y=10.0):
    if price is None or qty is None:
        return ("UNKNOWN", None, "insufficient comparable periods", [])
    if price >= x and qty > -y:
        return ("TRUE", price, "price up, quantity resilient", [])
    if price >= x and qty <= -y:
        return ("FALSE", qty, "price up, demand collapsed", [])
    return ("UNKNOWN", None, "no material price rise", [])


def gate_nosub(share, threshold=0.25, redesign=False, share_known=True):
    if not share_known:
        return ("UNKNOWN", None, "insufficient adoption evidence", [])
    if share >= threshold or redesign:
        return ("FALSE", share, "substitute viable", [])
    return ("TRUE", threshold - share, "no viable substitute", [])


def gate_need(intensity, min_intensity=0.5, relevant=True,
              relevant_known=True, kill_threshold=None):
    if intensity is None or not relevant_known:
        return ("UNKNOWN", None, "insufficient evidence", [])
    kill = min_intensity if kill_threshold is None else kill_threshold
    if intensity < kill or not relevant:
        return ("FALSE", intensity, "input abandoned or immaterial", [])
    if intensity >= min_intensity and relevant:
        return ("TRUE", intensity, "downstream requires input", [])
    return ("UNKNOWN", None, "between kill and minimum", [])


# --- predicate evaluation ------------------------------------------------

def eval_predicate(name: str, cfg: dict, usable: list):
    """Evaluate one predicate from usable evidence. Returns dict with
    state, margin, reason, sources, and SOURCE_FAILURE flag."""
    if name == "GAP":
        d = [x for m in cfg.get("demand", []) for x in _vals(usable, m)]
        s = [x for m in cfg.get("supply", []) for x in _vals(usable, m)]
        st, mg, rs, _ = gate_gap(d, s, cfg.get("threshold", 1.0),
                                 cfg.get("invert", False))
        used = d + s
    elif name == "LAG":
        c = _vals(usable, cfg["close_metric"]) if cfg.get("close_metric") else []
        h = _vals(usable, cfg["horizon_metric"]) if cfg.get("horizon_metric") else []
        if not c or not h:
            return _unknown(name, "missing dates")
        st, mg, rs, _ = gate_lag(c[0][0], h[0][0])
        used = c + h
    elif name == "WTP":
        p = _vals(usable, cfg["price_metric"]) if cfg.get("price_metric") else []
        q = _vals(usable, cfg["qty_metric"]) if cfg.get("qty_metric") else []
        if not p or not q:
            return _unknown(name, "insufficient comparable periods")
        st, mg, rs, _ = gate_wtp(p[0][0], q[0][0], cfg.get("x", 15.0),
                                 cfg.get("y", 10.0))
        used = p + q
    elif name == "NOSUB":
        sh = _vals(usable, cfg["share_metric"]) if cfg.get("share_metric") else []
        rd = _vals(usable, cfg["redesign_metric"]) if cfg.get("redesign_metric") else []
        if not sh:
            return _unknown(name, "insufficient adoption evidence")
        st, mg, rs, _ = gate_nosub(sh[0][0], cfg.get("threshold", 0.25),
                                   bool(rd and rd[0][0]), True)
        used = sh + rd
    elif name == "NEED":
        iv = _vals(usable, cfg["intensity_metric"]) if cfg.get("intensity_metric") else []
        rv = _vals(usable, cfg["relevance_metric"]) if cfg.get("relevance_metric") else []
        if not iv or not rv:
            return _unknown(name, "insufficient evidence")
        st, mg, rs, _ = gate_need(iv[0][0], cfg.get("min_intensity", 0.5),
                                  bool(rv[0][0]), True,
                                  cfg.get("kill_threshold"))
        used = iv + rv
    else:
        raise ValueError(f"unknown predicate {name}")
    if st != "UNKNOWN":
        need = cfg.get("min_sources", 1)
        have = len({x[2] for x in used})
        if have < need:
            return {"predicate": name, "state": "UNKNOWN", "margin": None,
                    "reason": f"only {have} independent sources, need {need}",
                    "sources": have, "source_failure": False}
    return {"predicate": name, "state": st, "margin": mg, "reason": rs,
            "sources": len({x[2] for x in used}), "source_failure": False}


def _unknown(name, reason):
    return {"predicate": name, "state": "UNKNOWN", "margin": None,
            "reason": reason, "sources": 0, "source_failure": False}


# --- trade state (§3). No LLM may override this. -------------------------

def evaluate_trade(preds: dict) -> str:
    p = preds
    if p["NEED"] == "FALSE":
        return "KILLED"
    if p["GAP"] == "FALSE":
        return "KILLED"
    if p["NEED"] == "UNKNOWN" or p["GAP"] == "UNKNOWN":
        return "UNKNOWN"
    if p["LAG"] == "FALSE" or p["WTP"] == "FALSE" or p["NOSUB"] == "FALSE":
        return "WARNING"
    if "UNKNOWN" in (p["LAG"], p["WTP"], p["NOSUB"]):
        return "UNKNOWN"
    return "ACTIVE"


# --- snapshot / world evaluation ------------------------------------------

def evaluate_snapshot(world: dict, snapshot: dict, mutations: dict = None):
    """One frozen date → claim states + trade state + §10 receipt."""
    cfg = world["config"]
    usable, rejected, stale = admissible(
        snapshot["evidence"], snapshot["date"], cfg.get("max_age_days", 400))
    states, details = {}, {}
    for name in PREDICATES:
        pcfg = dict(cfg["predicates"][name])
        if mutations and name in mutations:
            pcfg.update(mutations[name])
        r = eval_predicate(name, pcfg, usable)
        states[name] = r["state"]
        details[name] = r
    trade = evaluate_trade(states)
    ev_ids = sorted(e["evidence_id"] for e in usable)
    receipt = {
        "protocol": "acom/0.1",
        "subject": f"trade:{world['world_id']}",
        "state_before": snapshot.get("prev_state", "GENESIS"),
        "state_after": trade,
        "as_of": snapshot["date"],
        "claim_states": states,
        "evidence_root": "sha256:" + merkle_root(ev_ids),
        "rules_hash": "sha256:" + sha256_hex(
            canonical({"engine": ENGINE_VERSION, "config": cfg})),
        "output_hash": "",
    }
    receipt["output_hash"] = "sha256:" + sha256_hex(canonical(
        {"subject": receipt["subject"], "as_of": receipt["as_of"],
         "claim_states": states, "state": trade}))
    receipt["_meta"] = {"rejected": rejected, "stale": stale,
                        "details": details}
    return receipt


def evaluate_world(world: dict, mutations: dict = None):
    """Whole timeline in date order, chaining prev states."""
    receipts = []
    prev = "GENESIS"
    for snap in sorted(world["timeline"], key=lambda s: s["date"]):
        snap = dict(snap, prev_state=prev)
        r = evaluate_snapshot(world, snap, mutations)
        receipts.append(r)
        prev = r["state_after"]
    return receipts
