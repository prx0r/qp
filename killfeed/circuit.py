"""Executable boolean circuits over economic reality (circuitboard.md).

Claim graphs are data, not code: AND/OR/NOT/IF over comparisons over
metrics, with Kleene bool3 (TRUE/FALSE/UNKNOWN) throughout — UNKNOWN
propagates, never silently becomes FALSE. Every node returns
(value, margin): margin is the distance to flipping (weakest link
propagates through AND/OR, taken branch through IF), None where
distance is meaningless (dates, strings). Temporal ops read snapshot
history from the evaluation context. The top-level trade gate is itself
a circuit, so raw metrics → leaves → five → trade state is one graph.
"""

UNKNOWN = object()


def is_unknown(v):
    return v is UNKNOWN


def _b3(v):
    """Coerce Python values to bool3."""
    if v is UNKNOWN:
        return UNKNOWN
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, str) and v in ("TRUE", "FALSE", "UNKNOWN"):
        return UNKNOWN if v == "UNKNOWN" else v
    raise ValueError(f"not bool3-coercible: {v!r}")


def _num(v):
    if isinstance(v, bool) or v is UNKNOWN:
        raise ValueError("not numeric")
    return float(v)


class Ctx:
    """Evaluation context: fresh accepted evidence + snapshot date +
    history (prior {date, evidence, states} for temporal ops)."""

    def __init__(self, evidence, date, history=None):
        self.evidence = evidence
        self.date = date
        self.history = history or []

    def metric_vals(self, metric):
        """Sorted (low, high) range list for one metric."""
        out = []
        for e in self.evidence:
            if e.get("metric") != metric:
                continue
            v = e.get("value")
            try:
                if isinstance(v, dict):
                    out.append((float(v["low"]), float(v["high"])))
                elif isinstance(v, bool):
                    out.append((v, v))
                else:
                    out.append((float(v), float(v)))
            except (TypeError, ValueError):
                out.append((v, v))
        return sorted(out, key=repr)


def _numeric(vals):
    return [(a, b) for a, b in vals
            if isinstance(a, (int, float)) and not isinstance(a, bool)
            and isinstance(b, (int, float)) and not isinstance(b, bool)]


def _min_margin(margins):
    ms = [m for m in margins if m is not None]
    return min(ms) if ms else None


def ev(node, ctx):
    """Evaluate one circuit node → (value, margin). Malformed circuits
    raise ValueError (fail loud: a broken circuit must never score)."""
    if not isinstance(node, dict):
        raise ValueError(f"bad node: {node!r}")
    if "op" in node:
        fn = _OPS.get(node["op"])
        if fn is None:
            raise ValueError(f"unknown op: {node['op']}")
        return fn(node, ctx)
    if "const" in node:
        v = node["const"]
        return (UNKNOWN, None) if v == "UNKNOWN" else (v, None)
    if "metric" in node:
        vals = ctx.metric_vals(node["metric"])
        if not vals:
            return (UNKNOWN, None)
        nums = _numeric(vals)
        if nums:
            return ({"low": min(a for a, _ in nums),
                     "high": max(b for _, b in nums)}, None)
        return (vals[0][0], None)
    if "claim" in node:
        refs = getattr(ctx, "claims", {})
        if node["claim"] not in refs:
            raise ValueError(f"unresolved claim ref: {node['claim']}")
        return (refs[node["claim"]], None)
    if "param" in node:
        params = getattr(ctx, "params", {})
        if node["param"] not in params:
            raise ValueError(f"unresolved param: {node['param']}")
        return (params[node["param"]], None)
    raise ValueError(f"empty node: {node!r}")


def _args(node, ctx, n=None):
    a = [ev(c, ctx) for c in node.get("args", [])]
    if n is not None and len(a) != n:
        raise ValueError(f"{node.get('op')} needs {n} args")
    return a


def _range(v):
    if v is UNKNOWN:
        return None
    if isinstance(v, dict):
        return (v["low"], v["high"])
    if isinstance(v, bool):
        raise ValueError("bool where number expected")
    return (v, v)


def _and(node, ctx):
    pairs = [(_b3(v), m) for v, m in _args(node, ctx)]
    vals = [v for v, _ in pairs]
    if "FALSE" in vals:
        return ("FALSE", _min_margin(
            m for v, m in pairs if v == "FALSE"))
    if any(v is UNKNOWN for v in vals):
        return (UNKNOWN, None)
    return ("TRUE", _min_margin(m for _, m in pairs))


def _or(node, ctx):
    pairs = [(_b3(v), m) for v, m in _args(node, ctx)]
    vals = [v for v, _ in pairs]
    if "TRUE" in vals:
        return ("TRUE", _min_margin(
            m for v, m in pairs if v == "TRUE"))
    if any(v is UNKNOWN for v in vals):
        return (UNKNOWN, None)
    return ("FALSE", _min_margin(m for _, m in pairs))


def _not(node, ctx):
    (v, m) = _args(node, ctx, 1)[0]
    v = _b3(v)
    if v is UNKNOWN:
        return (UNKNOWN, None)
    return ("FALSE" if v == "TRUE" else "TRUE", m)


def _if(node, ctx):
    (c, cm), (t, tm), (e, em) = _args(node, ctx, 3)
    c = _b3(c)
    if c is UNKNOWN:
        return (UNKNOWN, None)
    if c == "TRUE":
        return (t, _min_margin([cm, tm]))
    return (e, _min_margin([cm, em]))


def _cmp(name, fn):
    def go(node, ctx):
        (a, _), (b, _) = _args(node, ctx, 2)
        ra, rb = _range(a), _range(b)
        if ra is None or rb is None:
            return (UNKNOWN, None)
        try:
            return fn(ra, rb)
        except TypeError:
            return (UNKNOWN, None)
    go.__name__ = name
    return go


def _num_pair(ra, rb):
    try:
        return (float(ra[0]), float(ra[1]), float(rb[0]), float(rb[1]))
    except (TypeError, ValueError):
        return None


def _gt(ra, rb):
    q = _num_pair(ra, rb)
    if q is None:
        if ra[0] > rb[1]:
            return ("TRUE", None)
        if ra[1] <= rb[0]:
            return ("FALSE", None)
        return (UNKNOWN, None)
    (al, ah, bl, bh) = q
    if al > bh:
        return ("TRUE", round(al - bh, 4))
    if ah <= bl:
        return ("FALSE", round(bl - ah, 4))
    return (UNKNOWN, None)


def _gte(ra, rb):
    q = _num_pair(ra, rb)
    if q is None:
        if ra[0] >= rb[1]:
            return ("TRUE", None)
        if ra[1] < rb[0]:
            return ("FALSE", None)
        return (UNKNOWN, None)
    (al, ah, bl, bh) = q
    if al >= bh:
        return ("TRUE", round(al - bh, 4))
    if ah < bl:
        return ("FALSE", round(bl - ah, 4))
    return (UNKNOWN, None)


def _lt(ra, rb):
    q = _num_pair(ra, rb)
    if q is None:
        if ra[1] < rb[0]:
            return ("TRUE", None)
        if ra[0] >= rb[1]:
            return ("FALSE", None)
        return (UNKNOWN, None)
    (al, ah, bl, bh) = q
    if ah < bl:
        return ("TRUE", round(bl - ah, 4))
    if al >= bh:
        return ("FALSE", round(al - bh, 4))
    return (UNKNOWN, None)


def _lte(ra, rb):
    q = _num_pair(ra, rb)
    if q is None:
        if ra[1] <= rb[0]:
            return ("TRUE", None)
        if ra[0] > rb[1]:
            return ("FALSE", None)
        return (UNKNOWN, None)
    (al, ah, bl, bh) = q
    if ah <= bl:
        return ("TRUE", round(bl - ah, 4))
    if al > bh:
        return ("FALSE", round(al - bh, 4))
    return (UNKNOWN, None)


def _eq(ra, rb):
    if ra is None or rb is None:
        return (UNKNOWN, None)
    if "UNKNOWN" in (ra[0], ra[1], rb[0], rb[1]):
        return (UNKNOWN, None)
    if isinstance(ra[0], str) or isinstance(rb[0], str):
        same = ra[0] == rb[0] and ra[1] == rb[1]
        return ("TRUE" if same else "FALSE", None)
    if ra[0] == ra[1] == rb[0] == rb[1]:
        return ("TRUE", 0.0)
    if ra[1] < rb[0] or rb[1] < ra[0]:
        return ("FALSE", None)
    return (UNKNOWN, None)


def _arith(name, fn):
    def go(node, ctx):
        (a, _), (b, _) = _args(node, ctx, 2)
        try:
            return (fn(_num(a), _num(b)), None)
        except ValueError:
            return (UNKNOWN, None)
    go.__name__ = name
    return go


def _low(node, ctx):
    m = node.get("metric")
    nums = _numeric(ctx.metric_vals(m)) if isinstance(m, str) else []
    return (min(a for a, _ in nums), None) if nums else (UNKNOWN, None)


def _high(node, ctx):
    m = node.get("metric")
    nums = _numeric(ctx.metric_vals(m)) if isinstance(m, str) else []
    return (max(b for _, b in nums), None) if nums else (UNKNOWN, None)


def _count(node, ctx):
    ms = node.get("metrics", [])
    ids = {e["source"]["source_id"] for e in ctx.evidence
           if e.get("metric") in ms and isinstance(e.get("source"), dict)}
    # Gate, not distance: source-count margins would mix units with the
    # economic distances they guard, so this is always margin-free.
    return (len(ids), None)


def _fresh(node, ctx):
    from datetime import date as _date
    ms = node.get("metrics", [node.get("metric")] if "metric" in node else [])
    max_age = node.get("max_age_days", 400)
    try:
        t = _date.fromisoformat(ctx.date)
    except ValueError:
        return (UNKNOWN, None)
    for e in ctx.evidence:
        if e.get("metric") not in ms:
            continue
        try:
            if 0 <= (t - _date.fromisoformat(e["as_of"])).days <= max_age:
                return ("TRUE", None)
        except ValueError:
            continue
    return (UNKNOWN, None)


def _hist_vals(ctx, metric, n):
    seq = []
    for snap in [{"evidence": ctx.evidence}] + list(
            reversed(ctx.history))[:n]:
        highs = []
        for e in snap["evidence"]:
            if e.get("metric") != metric:
                continue
            v = e.get("value")
            try:
                highs.append(float(v["high"] if isinstance(v, dict) else v))
            except (TypeError, ValueError, KeyError):
                continue
        if not highs:
            return None
        seq.append(max(highs))
    return seq if len(seq) == n + 1 else None


def _trend(node, ctx, rising):
    seq = _hist_vals(ctx, node["metric"], node.get("periods", 2))
    if seq is None:
        return (UNKNOWN, None)
    ok = all((b > a if rising else b < a) for a, b in zip(seq[1:], seq))
    return (("TRUE", min(abs(b - a) for a, b in zip(seq[1:], seq)))
            if ok else ("FALSE", None))


def _changed_by(node, ctx):
    seq = _hist_vals(ctx, node["metric"], 1)
    if seq is None:
        return (UNKNOWN, None)
    delta = seq[0] - seq[1]
    direction = node.get("direction", "GT")
    amt = float(node.get("delta", 0))
    if direction == "GT":
        return ("TRUE" if delta > amt else "FALSE", round(abs(delta), 4))
    if direction == "LT":
        return ("TRUE" if delta < -amt else "FALSE", round(abs(delta), 4))
    raise ValueError(f"bad CHANGED_BY direction: {direction}")


def _window_states(ctx, predicate, days):
    from datetime import date as _date, timedelta as _td
    try:
        t = _date.fromisoformat(ctx.date)
    except ValueError:
        return None
    out = []
    for h in ctx.history:
        try:
            if t - _date.fromisoformat(h["date"]) <= _td(days=days):
                out.append(h["states"][predicate])
        except (KeyError, ValueError):
            continue
    return out if out else None


def _changed_within(node, ctx):
    states = _window_states(ctx, node["predicate"], node.get("days", 365))
    if states is None:
        return (UNKNOWN, None)
    return ("TRUE" if len(set(states)) > 1 else "FALSE", None)


def _true_for(node, ctx):
    states = _window_states(ctx, node["predicate"], node.get("days", 365))
    if states is None:
        return (UNKNOWN, None)
    return ("TRUE" if all(s == "TRUE" for s in states) else "FALSE", None)


def _is_unknown(node, ctx):
    (v, _) = _args(node, ctx, 1)[0]
    return ("TRUE" if v is UNKNOWN or v == "UNKNOWN" else "FALSE", None)


_OPS = {
    "AND": _and,
    "OR": _or,
    "NOT": _not,
    "IF": _if,
    "EQ": _cmp("EQ", _eq),
    "GT": _cmp("GT", _gt),
    "GTE": _cmp("GTE", _gte),
    "LT": _cmp("LT", _lt),
    "LTE": _cmp("LTE", _lte),
    "MUL": _arith("MUL", lambda a, b: a * b),
    "ADD": _arith("ADD", lambda a, b: a + b),
    "SUB": _arith("SUB", lambda a, b: a - b),
    "DIV": _arith("DIV", lambda a, b: a / b if b else (_ for _ in ()).throw(
        ValueError("div0"))),
    "LOW": _low,
    "HIGH": _high,
    "COUNT": _count,
    "FRESH": _fresh,
    "TREND_UP": lambda n, c: _trend(n, c, True),
    "TREND_DOWN": lambda n, c: _trend(n, c, False),
    "CHANGED_BY": _changed_by,
    "CHANGED_WITHIN": _changed_within,
    "TRUE_FOR": _true_for,
    "IS_UNKNOWN": _is_unknown,
}


def evaluate(node, evidence, date, history=None, claims=None, params=None):
    """Top entry: node + usable evidence + date + optional history,
    claims (claim refs) and params (tunable gate constants).
    Always returns a plain value; unknown arrives as "UNKNOWN"."""
    ctx = Ctx(evidence, date, history)
    ctx.claims = claims or {}
    ctx.params = params or {}
    v, _ = ev(node, ctx)
    return "UNKNOWN" if v is UNKNOWN else v


def evaluate_margin(node, evidence, date, history=None, claims=None,
                    params=None):
    """Same, but keeps the margin (distance to flipping)."""
    ctx = Ctx(evidence, date, history)
    ctx.claims = claims or {}
    ctx.params = params or {}
    v, m = ev(node, ctx)
    return ("UNKNOWN" if v is UNKNOWN else v, m)
