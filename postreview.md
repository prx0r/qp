# Post-review — post-AGI kernel vs qp (2026-09-12)

## Where things were

No Nillion project exists on this box (the only hit is an incidental
string in vendored EDGAR data). The post-AGI theses live in
`bneck2/imported/postagi_kernel` — a 400KB research kernel, now imported
at `qp/vendor/postagi-kernel/` (reference only, git-ignored like the
other vendor clones). Its thesis: price divergence between our vs
market-implied probability of post-AGI world-states, times causal
cash-flow exposure. Alpha = `(our_p − market_p) × exposure × duration
× confidence` minus an obsolescence penalty.

## What's inside (honest)

Real machinery: typed causal DAG (`world→capability→cost→behavior→
demand→profit`) with elasticity/confidence/delay propagation; exact
Song Ma obsolescence formula from patent bases; reverse market-probability
inference via bounded ridge with a conditioning-number refusal gate;
log-odds Bayesian scenario updates; walk-forward long/short backtest
with turnover costs; SQLite evidence/snapshot store.

Admitted fixture, not alpha: demo Sharpe on synthetic planted data,
`our_p > market_p` hardcoded everywhere (structural long bias),
unjustified weights (0.55/0.20/0.15/0.10), damping constants, a decay
counter named after MIRAI, generic MLP named after Patentomics, and an
`INSERT OR REPLACE` evidence store that mutates receipts. Heavy deps
(networkx/scipy/sklearn/pandas) for work our stdlib kernel does smaller.

## Mined: what crosses over into qp

1. **Constraint-divergence score.** Their `divergence × exposure` is the
   tradable twin of our EI (`P × impact`). Import as: per (constraint ×
   scenario) divergence between our tightness verdict and the market's,
   ranked the same way. Fits `seesaw/` with no new objects.
2. **DAG paths compile to circuits.** Their typed edges
   (elasticity/confidence/delay) describe exactly the boolean circuits
   we hand-author in `killfeed/worlds/`. Import as: a compiler from
   DAG paths to circuit nodes (AND bottleneck chains, OR substitution
   branches, delay-gated activation). This kills hand-written worlds.
3. **Evidence receipts, fixed.** Their receipt shape matches ours except
   theirs mutates (`REPLACE`). Ours is already append-only — keep ours,
   note the bug so nobody reimports it.
4. **Reverse-inference gate.** Bounded ridge `priced == X·p` plus refuse-
   if-ill-conditioned is genuinely good and has no qp equivalent: infer
   market-implied constraint tightness from spreads, refuse when
   exposures are collinear. Needs scipy — quarantine as optional
   adapter, not kernel.
5. **Song Ma obsolescence as a NOSUB complement.** Exact, tiny, pure
   math: dying-technology-base detector for the short/risk leg, where
   our NOSUB measures substitution threat from the other side. Import
   as a gate template (no dependencies).
6. **Leakage-safe harness.** Score-at-date → forward return, per-date
   rebalance, turnover costs, as-of enforcement. Reuse verbatim shape
   for migration-signal backtests.

## Explicitly NOT importing

Hardcoded long bias, magic weights, synthetic Sharpe claims, heavy-dep
graph/ML stack, misnamed methods, mutable evidence store. Their
`docs/papers.md` honesty tiers (exact vs adapter vs extension) are
worth copying as a documentation convention.

## Recommended build order

1. DAG→circuit compiler (kills hand-authored worlds).
2. Divergence score in `seesaw/` (tradable EI twin).
3. Song Ma gate template (pure python, no deps).
4. Reverse-inference adapter (optional, scipy-quarantined).
5. Backtest harness reuse for migration signals.

## BEAR addendum — NIL / XMR / ZEC (2026-09-12)

The trades project is BEAR (`~/BEAR`, Hyperliquid perp engine, rel-value
+ funding/dispersion thesis). Its NIL/XMR/ZEC footprint is thin but real:
NIL lives in `data/dex_markets.json` (listing/market data), ZEC appears
twice in the 1,638-tweet CryptoBheem corpus, XMR carries one live pressure
reading (LONG-crowded 35). No dedicated trade ledger for the three —
mostly market data plus sparse social signal, plus BEAR's generic
pressure/backtest/mimic machinery around them.

Why this matters more than its size: these three are textbook Seesaw
assets. XMR/ZEC are privacy/authenticated-constraint exposure (qpvalidate
§23 already names XMR/ZEC relative thesis as the second live world after
HBM). NIL (blind computation) sits on the verification/computation
constraint the Seesaw stack itself needs. All three trade exactly the
migration Seesaw tracks: value moving toward constraints AI cannot relax
(privacy, authentication, verifiable private compute).

Concrete crossovers, cheapest first:

1. **XMR/ZEC relative thesis as live world #2.** BEAR already has the
   pressure scores, funding/basis inputs, and backtest panel shape;
   qp has the receipt/gate/clamp machinery. Feed BEAR pressure + funding
   as evidence metrics into a killfeed-style world with the same
   ACTIVE/WARNING/KILLED discipline — no new code on either side to start,
   just a world definition and an adapter.
2. **NIL as verification-constraint proxy.** Nillion's blind-compute
   thesis (private verifiable inference) is the market-priced version
   of our cognition-attestation layer. Track NIL pressure/funding as the
   market's vote on the verification scarcity our stack assumes.
3. **Mimic corpora as swarm FILL material.** 1,638-tweet expert corpora
   with timestamps are pre-shaped evidence bundles: expert claims with
   as-of dates, ready for provenance tagging into killfeed evidence
   once source lineage is attached.
4. **Backtest discipline reuse.** BEAR's walk-forward + turnover-cost
   harness is the honest template for scoring migration signals —
   same shape the postagi review recommended, now with a second
   independent instance confirming the pattern.
