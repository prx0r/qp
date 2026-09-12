"""Reverse market inference, quarantined adapter (postreview build #4).

priced == X·p: infer market-implied probabilities from observed priced
impacts and exposures. Bounded ridge toward p0=0.5, pure python
(Gaussian elimination on the normal equations — small systems only;
this is an adapter, not the kernel). Refuses underdetermined systems
instead of hallucinating: unidentifiable stays UNKNOWN upstream.

No third-party imports. If numpy/scipy ever become kernel-allowed,
reimplement against them and keep this file as the cross-check.
"""


def _solve(aug, vec):
    """Gaussian elimination with partial pivoting. Raises on singularity
    (refusal propagates — never returns a fabricated inverse)."""
    n = len(vec)
    m = [row[:] + [vec[i]] for i, row in enumerate(aug)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular system: exposures collinear")
        m[col], m[piv] = m[piv], m[col]
        for r in range(n):
            if r != col and m[r][col] != 0:
                f = m[r][col] / m[col][col]
                for k in range(col, n + 1):
                    m[r][k] -= f * m[col][k]
    return [m[i][n] / m[i][i] for i in range(n)]


def infer_market_probabilities(X: list, y: list, ridge: float = 1e-3,
                               p0: float = 0.5) -> dict:
    """Bounded ridge: min ||Xp − y||² + ridge·||p − p0||², clipped [0,1].
    X rows = priced instruments, cols = scenarios. Returns probs +
    identifiability flag (False = refuse to use)."""
    n_rows, n_cols = len(y), len(X[0])
    if n_rows < n_cols:
        return {"ok": False, "reason": "underdetermined: fewer prices than scenarios"}
    aug = [[sum(X[r][i] * X[r][j] for r in range(n_rows))
            + (ridge if i == j else 0.0) for j in range(n_cols)]
           for i in range(n_cols)]
    rhs = [sum(X[r][i] * y[r] for r in range(n_rows)) + ridge * p0
           for i in range(n_cols)]
    try:
        raw = _solve(aug, rhs)
    except ValueError as e:
        return {"ok": False, "reason": str(e)}
    return {"ok": True,
            "probs": [min(1.0, max(0.0, v)) for v in raw]}
