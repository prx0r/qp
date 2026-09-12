# Killfeed historical validation — how it works

Spec: `qpvalidate.md` (§1–§24). Run: `python -m killfeed.verify_all`.

## Engine (`killfeed/engine.py`)

Pure functions, no network/clock/randomness. Evidence → five predicate
gates (§9 templates, parameterized per world) → `evaluate_trade` (§3,
un-overridable) → §10 receipt with `evidence_root`, `rules_hash`,
`output_hash` (canonical JSON via `acom`).

Admissibility per snapshot: `as_of <= T`, age within `max_age_days`,
provenance contract (accepted class + `sha256:` artifact) else REJECTED.
Independent sources = distinct `source_id`s; verdicts below
`min_sources` collapse to UNKNOWN. Missing data is always UNKNOWN,
never FALSE (invariant 6); broken provenance is exclusion, never zero.

## Worlds (`killfeed/worlds/`)

Ten frozen worlds, each `world.yaml` (gate params) + `timeline/*.json`
(evidence only available at that date) + `expected.json` (frozen
acceptance) + `counterfactuals/*.json` (rule-not-memory proofs).
Fixtures built deterministically by `killfeed/build_worlds.py`;
values are illustrative levels exercising gate boundaries.

## Validators (`killfeed/validators.py`)

Worlds, precision (0 false / 0 missed hard kills), determinism (100
reruns, byte-identical hashes), no-future-leak, unknown semantics,
source failure, lineage collapse, gate mutation (inverted GAP must
break the suite or coverage is fake), seeded order shuffles,
dependency recompute, four adversarial attacks, schemas, acom-store
replay. Certificate → `runs/killfeed/certificate.json`.

## Deliberate deviations from the spec text

- §20 certificate: single `implementation_commit` (the spec prints the
  key twice, which is not valid JSON).
- Mutation is parameterized (`invert`, absurd threshold), not source
  editing — same falsification power, repeatable.
- `SOURCE_FAILURE` surfaces as UNKNOWN trade + rejected list (allowed
  by §2), not a fourth trade state.
