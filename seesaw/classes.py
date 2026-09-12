"""Ten scarcity classes + breakthrough impact vectors (atunomousgoal §10).

Coarse by design: every breakthrough maps to Δλ over ten classes on a
-2..+2 scale (↓↓/↓/0/↑/↑↑). Sign-only reasoning first (Seesaw v0 §16);
magnitudes order investigation, never decide truth.
"""
CLASSES = ("COGNITION", "COMPUTE", "MEMORY", "POWER", "FABRICATION",
           "MATERIALS", "DATA", "PHYSICAL_VALIDATION", "VERIFICATION",
           "AUTHORITY")


def encode(moves: dict) -> dict:
    """Validate a breakthrough impact vector. Unknown classes raise —
    a shock mapped to a nonexistent constraint is a modeling bug, and
    modeling bugs must fail here, not downstream."""
    for k, v in moves.items():
        if k not in CLASSES:
            raise ValueError(f"unknown scarcity class {k}")
        if v not in (-2, -1, 0, 1, 2):
            raise ValueError(f"move out of range: {k}={v}")
    return {c: moves.get(c, 0) for c in CLASSES}


def sign(vec: dict) -> dict:
    """sign(dS/dA) per class: +1 tighter, 0 none, -1 destroyed."""
    return {c: (1 if v > 0 else -1 if v < 0 else 0) for c, v in vec.items()}


def destroyed(vec: dict) -> list:
    """Constraints the breakthrough kills (the short/avoid leg)."""
    return sorted(c for c, v in vec.items() if v < 0)


def amplified(vec: dict) -> list:
    """Constraints the breakthrough tightens (the long leg)."""
    return sorted(c for c, v in vec.items() if v > 0)


VECTORS = {
    "navier-stokes-2026": {"COGNITION": -2, "COMPUTE": 1, "MEMORY": 1,
                           "PHYSICAL_VALIDATION": 1, "VERIFICATION": 2},
    "extropic-thermo": {"COMPUTE": -1, "MEMORY": -1, "POWER": -1,
                        "FABRICATION": 2, "MATERIALS": 1,
                        "PHYSICAL_VALIDATION": 1},
    "quantum-robust": {"COGNITION": 0, "COMPUTE": 1, "MATERIALS": 1,
                       "POWER": 1, "VERIFICATION": 2, "AUTHORITY": -2,
                       "FABRICATION": 2, "DATA": 1},
}
for _k, _v in VECTORS.items():
    VECTORS[_k] = encode(_v)
