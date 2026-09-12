"""Song Ma obsolescence gate, pure python (postreview build #3).

Technological obsolescence(c0, c1) = ln(c0/c1): citations to a firm's
fixed technology base at the start vs the end of the window. A dying
base (few outsiders still building on it) scores high — the short/risk
leg complement to NOSUB, which measures substitution threat from the
other side. No dependencies; citation records are plain dicts.
"""
import math


def obsolescence(c0: float, c1: float) -> float:
    """Log decay of external citations to a fixed base. Positive =
    abandonment; negative = revival (also signal, keep the sign).
    eps guards the empty end, never the interpretation."""
    return math.log((c0 + 1e-9) / (c1 + 1e-9))


def construct_base(cites: list, firm: str, cutoff: int, min_base: int = 1):
    """Technology base: patents owned by OTHERS that `firm` cited at or
    before cutoff. cite = {citing_firm, citing_year, cited_patent,
    cited_owner}. Returns None when the base is too small to trust."""
    base = {c["cited_patent"] for c in cites
            if c["citing_firm"] == firm and c["citing_year"] <= cutoff
            and c["cited_owner"] != firm}
    return base if len(base) >= min_base else None


def external_cites(cites: list, base: set, year: int) -> int:
    """Outside citations to the base in one year (outsiders only)."""
    return sum(1 for c in cites
               if c["citing_year"] == year and c["cited_patent"] in base
               and c["citing_firm"] != c.get("cited_owner", ""))


def firm_obsolescence(cites: list, firm: str, start: int, end: int,
                      window: int = 5, min_base: int = 1):
    """Full gate: base fixed `window` years before start, compare outside
    citations at start vs end. Returns None when unmeasurable (never zero:
    absence of data is UNKNOWN, not health)."""
    base = construct_base(cites, firm, start - window, min_base)
    if base is None:
        return None
    return obsolescence(external_cites(cites, base, start),
                        external_cites(cites, base, end))
