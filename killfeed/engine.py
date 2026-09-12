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
    """TRUE iff demand_low > supply_high x threshold; FALSE iff
    demand_high <= supply_low; else UNKNOWN. `invert` exists ONLY for
    mutation testing (proves the suite can catch flipped logic)."""
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
    """TRUE iff the gap closes after the horizon (shortage persists)."""
    if close is None or horizon is None:
        return ("UNKNOWN", None, "missing dates", [])
    if close > horizon:
        return ("TRUE", None, "gap closes after horizon", [])
    return ("FALSE", None, "gap closes inside horizon", [])


def gate_wtp(price, qty, x=15.0, y=10.0):
    """TRUE iff price rises >= x with quantity resilient (>-y); FALSE iff
    price rises while demand collapses past elasticity; else UNKNOWN."""
    if price is None or qty is None:
        return ("UNKNOWN", None, "insufficient comparable periods", [])
    if price >= x and qty > -y:
        return ("TRUE", price, "price up, quantity resilient", [])
    if price >= x and qty <= -y:
        return ("FALSE", qty, "price up, demand collapsed", [])
    return ("UNKNOWN", None, "no material price rise", [])


def gate_nosub(share, threshold=0.25, redesign=False, share_known=True):
    """TRUE iff substitutes are marginal and no redesign removes the
    bottleneck; FALSE on viable substitution."""
    if not share_known:
        return ("UNKNOWN", None, "insufficient adoption evidence", [])
    if share >= threshold or redesign:
        return ("FALSE", share, "substitute viable", [])
    return ("TRUE", threshold - share, "no viable substitute", [])


def gate_need(intensity, min_intensity=0.5, relevant=True,
              relevant_known=True, kill_threshold=None):
    """TRUE iff downstream needs the input at intensity; FALSE iff the
    input is abandoned or immaterial (Fukushima-class demand shocks)."""
    if intensity is None or not relevant_known:
        return ("UNKNOWN", None, "insufficient evidence", [])
    kill = min_intensity if kill_threshold is None else kill_threshold
    if intensity < kill or not relevant:
        return ("FALSE", intensity, "input abandoned or immaterial", [])
    if intensity >= min_intensity and relevant:
        return ("TRUE", intensity, "downstream requires input", [])
    return ("UNKNOWN", None, "between kill and minimum", [])


# --- predicate evaluation ------------------------------------------------

def predicate_params(pcfg: dict) -> dict:
    """Tunable gate constants, single definition (CLI reuses this)."""
    return {"threshold": pcfg.get("threshold", 1.0),
            "share_threshold": pcfg.get("share_threshold",
                                        pcfg.get("threshold", 0.25)),
            "x": pcfg.get("x", 15.0), "y": pcfg.get("y", 10.0),
            "min_intensity": pcfg.get("min_intensity", 0.5),
            "kill": pcfg.get("kill_threshold",
                             pcfg.get("min_intensity", 0.5)),
            "min_sources": pcfg.get("min_sources", 1)}


def eval_predicate(name: str, cfg: dict, usable: list, date: str = "",
                   history=None, claims=None, use_circuit: bool = True):
    """Evaluate one predicate. Circuits (data) preferred; legacy templates
    kept as cross-check until equivalence is proven — then deleted."""
    if use_circuit and "circuit" in cfg:
        from . import circuit as _circuit
        params = predicate_params(cfg)
        try:
            state, margin = _circuit.evaluate_margin(
                cfg["circuit"], usable, date, history, claims or {}, params)
        except ValueError:
            state, margin = "UNKNOWN", None
        if state not in ("TRUE", "FALSE", "UNKNOWN"):
            state, margin = "UNKNOWN", None
        if state == "UNKNOWN":
            margin = None  # unknown has no measurable distance to flipping
        if cfg.get("invert") and state in ("TRUE", "FALSE"):
            state = "FALSE" if state == "TRUE" else "TRUE"
        used = [e for e in usable]
        return {"predicate": name, "state": state, "margin": margin,
                "reason": "circuit", "sources": independent_sources(used),
                "source_failure": False}
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


# --- trade state (§3, circuitboard: the top-level gate is universal) -----

def _EQC(claim, const):
    return {"op": "EQ", "args": [{"claim": claim}, {"const": const}]}


def _ISU(claim):
    return {"op": "IS_UNKNOWN", "args": [{"claim": claim}]}


def _OR(*names, const):
    return {"op": "OR",
            "args": [_EQC(n, const) for n in names]}


def _ORU(*names):
    return {"op": "OR", "args": [_ISU(n) for n in names]}


def _IFC(cond, then, otherwise):
    return {"op": "IF", "args": [cond, {"const": then}, otherwise]}


TRADE_CIRCUIT = _IFC(
    _OR("NEED", "GAP", const="FALSE"), "KILLED",
    _IFC(_ORU("NEED", "GAP"), "UNKNOWN",
         _IFC(_OR("LAG", "WTP", "NOSUB", const="FALSE"), "WARNING",
              _IFC(_ORU("LAG", "WTP", "NOSUB"), "UNKNOWN",
                   {"const": "ACTIVE"}))))

def evaluate_trade(preds: dict) -> str:
    """§3 state machine. NEED/GAP FALSE kill; NEED/GAP UNKNOWN unknowns;
    any FALSE among LAG/WTP/NOSUB warns. No LLM may override this."""
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

def evaluate_snapshot(world: dict, snapshot: dict, mutations: dict = None,
                      history=None, use_circuit: bool = True):
    """One frozen date → claim states + trade state + §10 receipt.
    history = prior [{date, evidence, states}] for temporal ops and the
    live recompute path (new evidence → leaves → propagate → kill)."""
    cfg = world["config"]
    usable, rejected, stale = admissible(
        snapshot["evidence"], snapshot["date"], cfg.get("max_age_days", 400))
    states, details, claims = {}, {}, {}
    for name in PREDICATES:
        pcfg = dict(cfg["predicates"][name])
        if mutations and name in mutations:
            pcfg.update(mutations[name])
        r = eval_predicate(name, pcfg, usable, snapshot["date"],
                           history, claims, use_circuit)
        states[name] = r["state"]
        claims[name] = r["state"]
        details[name] = r
    if use_circuit:
        from . import circuit as _circuit
        try:
            trade = _circuit.evaluate(TRADE_CIRCUIT, usable,
                                      snapshot["date"], history, claims)
        except ValueError:
            trade = "UNKNOWN"
        if trade not in ("ACTIVE", "WARNING", "KILLED", "UNKNOWN"):
            trade = "UNKNOWN"
    else:
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


def evaluate_world(world: dict, mutations: dict = None,
                   use_circuit: bool = True):
    """Whole timeline in date order, chaining prev states. Each snapshot
    sees prior snapshots as history (temporal ops, live recompute)."""
    receipts = []
    prev = "GENESIS"
    history = []
    for snap in sorted(world["timeline"], key=lambda s: s["date"]):
        snap = dict(snap, prev_state=prev)
        r = evaluate_snapshot(world, snap, mutations, history, use_circuit)
        receipts.append(r)
        history.append({"date": snap["date"],
                        "evidence": snap["evidence"],
                        "states": r["claim_states"]})
        prev = r["state_after"]
    return receipts


def world_state_root(receipts: list) -> str:
    """One root per world evaluation: replayable, comparable across
    replicas. Three nodes agree iff these match on every world."""
    from acom.canonical import merkle_root
    return merkle_root([r["output_hash"] for r in receipts])


def kill_events(world: dict):
    """TRUE→FALSE predicate flips across the timeline (circuitboard:
    flips are the events; trade KILL is their consequence)."""
    evs = []
    receipts = evaluate_world(world)
    prior = {}
    for r in receipts:
        for name in PREDICATES:
            if prior.get(name) == "TRUE" and r["claim_states"][name] == "FALSE":
                evs.append({"world": world["world_id"], "predicate": name,
                            "from": "TRUE", "to": "FALSE",
                            "date": r["as_of"],
                            "trade": r["state_after"]})
        prior = r["claim_states"]
    return evs
