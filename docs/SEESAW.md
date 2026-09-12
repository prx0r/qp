# SEESAW — formal layer (seesaw.md thesis, v0)

Killfeed asks whether a KNOWN trade is alive. Seesaw asks WHERE the
binding constraint is and where it moves when AI capability shifts.
Both share circuits, canonical bytes, and receipts.

## Belief vs fact (`seesaw/beliefs.py`)

- BELIEF: log-odds state, updated per evidence LR. Reopenable forever.
- FACT: epoch-finalized verdict, immutable. New epochs append; finalized
  FACTs raise on update. History is never rewritten.
- Waves: claim states flow along support edges in topological order;
  every moved belief reported with before/after. UNKNOWN skips.
- EI = P(E) x impact ranks what to research (feeds VOI routing).

## Module (`seesaw/`)

- `graph.score_node`: S_i = M·D·T / (C·A) plus constraint pressure D/C.
- `graph.ai_exposure`: demand_effect − destruction_effect → TIGHTENS /
  RELAXES / NEUTRAL (the central equation).
- `graph.binding_constraint`: argmax S over nodes — the current trade.
- `graph.evaluate_event_claims`: boolean circuits over event evidence.

## First live test (`seesaw/events/ns_202609.json`)

Navier–Stokes Sep 2026: claims A–E evaluate TRUE/FALSE/FALSE/TRUE/TRUE,
the dumb short-CFD trade evaluates FALSE, binding migrates
math_search → verification, CFD software doesn't move. Four tests pin it.

## Relation to killfeed

A migration event SHOULD produce killfeed work: when exposure flips
negative on a node, emit CHALLENGE jobs against that node's predicates;
when a new node takes the argmax, open a candidate trade dossier. That
wiring is next, not yet built.
