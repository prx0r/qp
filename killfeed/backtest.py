"""Walk-forward backtest for migration signals (postreview build #5).

Score-at-date → forward return, per-date rebalance, turnover × costs.
Same shape as BEAR and postagi harnesses (two independent instances of
one honest pattern): positions from scores, never from the future.
Panel rows: {date, ticker, score, fwd_ret}. Costs in bps per unit traded.
"""
def positions(scores: dict, quantile: float = 0.2, gross: float = 1.0):
    """Long top quantile, short bottom quantile, ±gross/2n each."""
    names = sorted(scores)
    n = max(1, int(len(names) * quantile))
    longs = sorted(names, key=lambda t: scores[t], reverse=True)[:n]
    shorts = sorted(names, key=lambda t: scores[t])[:n]
    pos = {t: 0.0 for t in names}
    for t in longs:
        pos[t] = gross / (2 * n)
    for t in shorts:
        pos[t] = -gross / (2 * n)
    return pos


def walk_forward(panel: list, cost_bps: float = 10.0, quantile: float = 0.2):
    """Per-date rebalance. Returns per-date nets + summary metrics."""
    by_date = {}
    for row in panel:
        by_date.setdefault(row["date"], []).append(row)
    prev, nets = {}, []
    for date in sorted(by_date):
        rows = by_date[date]
        pos = positions({r["ticker"]: r["score"] for r in rows}, quantile)
        rets = {r["ticker"]: r["fwd_ret"] for r in rows}
        gross = sum(pos[t] * rets.get(t, 0.0) for t in pos)
        turnover = sum(abs(pos[t] - prev.get(t, 0.0)) for t in pos)
        cost = turnover * cost_bps / 1e4
        nets.append({"date": date, "net": round(gross - cost, 6),
                     "turnover": round(turnover, 4)})
        prev = pos
    import math
    rs = [n["net"] for n in nets]
    if not rs:
        return {"nets": [], "ann": 0.0, "vol": 0.0, "sharpe": 0.0,
                "maxdd": 0.0}
    ann = (math.prod(1 + r for r in rs) ** (12 / len(rs)) - 1) if rs else 0.0
    mean = sum(rs) / len(rs)
    var = sum((r - mean) ** 2 for r in rs) / len(rs)
    vol = math.sqrt(var) * math.sqrt(12)
    peak = dd = 0.0
    eq = 1.0
    for r in rs:
        eq *= 1 + r
        peak = max(peak, eq)
        dd = max(dd, (peak - eq) / peak if peak else 0.0)
    return {"nets": nets, "ann": round(ann, 4), "vol": round(vol, 4),
            "sharpe": round(mean / math.sqrt(var) * math.sqrt(12), 4)
                      if var > 0 else 0.0,
            "maxdd": round(dd, 4)}
