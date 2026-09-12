# Post-review — post-AGI theses vs qp (2026-09-12)

## Sources (all imported)

- `vendor/tjp-agitheses/` — 32 post-AGI memos (5 research, 23 alpha
  hunts, 3 kernel builds), 247 theses, 115 unique, 74 carrying explicit
  falsifiers. Cloned from `~/tjp` (thesis desk). THIS is the post-AGI
  corpus: physical-world bottlenecks, not model chat.
- `vendor/postagi-kernel/` — bneck2 obsolescence kernel (reviewed below).
- BEAR trading engine — NIL/XMR/ZEC footprint (addendum at end).

## What the memos actually say

One thesis repeated in a dozen forms: AI collapses design/discovery
stages while physical validation, qualification, and truth-tracking
can't keep up — so rents migrate to the slowest physical gate.
Recurring primitives: calibration debt, qualification debt, truth
infrastructure as an asset class, certification bandwidth, inspection-
memory scarcity, experimental entropy inflation, rare-failure telemetry
as a negative-data asset class, fab activation latency, O-ring gating
(multiplicative quality constraints), capacity displacement, embedded-
utility toll roads, dopant/interface-chemistry layers.

## Mapping vs qp work (hits, not vibes)

1. **Truth infrastructure / certification bandwidth / inspection-memory
   = our verification layer.** The memos independently price exactly
   what Seesaw claim E says rises (formal/proof/qualification
   infrastructure). Outside confirmation of the NS-worked direction.
2. **Experimental entropy inflation = the NS thesis verbatim.**
   "AI increases the variety of physical experiments" → validation
   becomes the binding constraint. Our candidate-generation↑↑ vs
   physical-validation story, found independently in the wild.
3. **O-ring gating = our AND circuits.** Multiplicative
   quality/completion constraints where one failing stage kills the
   chain are bottleneck AND-chains. Their screen ("find workflows with
   multiplicative constraints, estimate which stages AI collapses,
   reprice the untouched stage") is a prose version of binding-argmax
   migration. Formalize it as a gym task next.
4. **74 falsifiers = FALSIFY seeds.** Wired: `killfeed/tjp_falsifiers.py`
   loads the deduped corpus (37 unique) into A-COM FALSIFY tasks whose
   acceptance names the falsifier. Tested.
5. **Ratings (8.1–9.5) = prior weights.** Usable directly as EI impact
   priors when these theses enter the belief graph.
6. **Qualification debt / LAG-flip-first** (mills restart, standards
   lag) matches our LAG-before-GAP kill ordering across lumber, DRAM,
   fiber worlds. The worlds already encode what the memos narrate.

## Previously reviewed (kept)

- postagi_kernel: typed causal DAG + Song Ma obsolescence + reverse
  ridge inference worth taking (DAG→circuit compiler, divergence
  score, pure-python gate, quarantined adapter, harness shape).
  Rejected: magic weights, synthetic Sharpe, heavy deps, mutable store.
- BEAR: thin NIL/XMR/ZEC footprint; XMR/ZEC relative thesis stays the
  second live world candidate; pressure/funding feeds map to evidence
  metrics without new code.

## Build order additions

1. DONE: falsifier corpus → FALSIFY seeds (`tjp_falsifiers`, tested).
2. NEXT: O-ring screen as gym task (multiplicative-constraint worlds).
3. NEXT: truth-infrastructure node family in seesaw (calibration /
   certification / inspection nodes with shared dynamics).
4. LATER: ratings as EI priors once belief theses import.
