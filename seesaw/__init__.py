"""Seesaw formal layer (seesaw.md): shadow-price tracking for constraint
migration. Complements killfeed (which asks whether a KNOWN trade is
alive) by asking WHERE the binding constraint is and where it moves
when AI capability shifts.

v0 scope, deliberately narrow:
- dependency chains as data (output → inputs, recursively);
- S_i scoring per the thesis formula (illustrative magnitudes);
- AI exposure per node (demand effect minus destruction effect);
- before/after event comparison showing migration (the test that matters).

Killfeed answers "is constraint X still binding". Seesaw answers
"constraint X just relaxed — which constraint binds next".
"""
from .graph import (  # noqa: F401
    ai_exposure, binding_constraint, evaluate_event_claims, score_node,
)
