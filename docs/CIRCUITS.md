# Circuits — claim graphs are data (circuitboard.md, executable)

Evaluator: `killfeed/circuit.py`. Every node returns (value, margin);
UNKNOWN poisons AND/OR (Kleene), `IS_UNKNOWN` tests state identity
(comparing *against* UNKNOWN is UNKNOWN — that distinction cost a
debugging session; see git log). `IF` propagates the weaker margin of
condition and taken branch. Malformed circuits raise, never score.

Ops: AND OR NOT IF EQ GT GTE LT LTE MUL ADD SUB DIV LOW HIGH COUNT
FRESH TREND_UP TREND_DOWN CHANGED_BY CHANGED_WITHIN TRUE_FOR
IS_UNKNOWN, plus `metric` / `const` / `claim` / `param` leaves.
Comparisons understand ranges (`{low, high}`): TRUE only on clean
separation, FALSE only on clean containment, else UNKNOWN. Dates
compare lexicographically (ISO); margins on dates are None by design.

Worlds carry per-predicate `circuit:` blocks (emitted by
`build_worlds.py`); tunables arrive as `param` nodes resolved from the
predicate config, so mutations and threshold changes flow through.
The trade gate is one universal circuit (`engine.TRADE_CIRCUIT`).
Legacy templates remain as cross-checks (`use_circuit=False`);
`test_circuit.py` pins them identical on all worlds.

Temporal ops read snapshot history passed down by `evaluate_world`
(the live recompute path: new evidence → leaves → propagate → kill).
`engine.kill_events()` lists TRUE→FALSE flips with trade consequences.
