# ECOSYSTEM — what we have, and how it composes under A-COM

Review date 2026-09-12. Code surveyed same-day (survey reports on file
with the session, not committed). Read with `northstar.md` (thesis),
`qpvalidate.md` (acceptance), `docs/` (kernel contract).

## 1. What qp actually is now

`qp/acom` is the hard kernel (Phase A, proven: 12/12 unit, both demos
settle one receipt type). `qp/killfeed` is the first canonical
external-state engine AND the first procedure template: 10 frozen
worlds, 10/10 green, mutation-tested. qp is therefore two things
already: the microprocessor and its first program. Everything below
plugs into one of those two slots.

## 2. Sibling survey (ground truth, not brochure)

- **aloop** (`~/aloop`): mechanical autonomy loop over a pinned `atask`
  kernel submodule. `step()` with 9 outcomes, swappable policies,
  sweep/evolution worlds, MCP verbs, 37/37 loop tests green. This is
  northstar §7 almost verbatim — the loop with no intelligence in it.
- **atask**: no top-level dir; lives pinned inside aloop
  (`aloop/kernel/atask`, 68 tests). Goal/Task/Run/Evidence receipts,
  content-addressed. The predecessor kernel to align with, not fork.
- **aworker** (`~/aworker`): bounded-authority envelope — grants with
  parent-bound subdivision, quote→reserve→settle ledger, escalation
  claims vs block proofs. 22/22 green, honestly-logged holes (ledger
  blind to grants, float money). This is the economic governor (§20)
  and the authority layer (§28) wearing work clothes.
- **cg** (`~/cg`, cogymkernel): deterministic evolution lab — replayable
  worlds, content-addressed RunReceipts, quality gates with
  non-inferiority stats, proposer-blind secret sets, rebuild-gate CI,
  MCP + CLI. This is §18 (promotion lab) already built, including the
  `website/data/claims.json` static API habit we should copy.
- **mw** (`~/mw`, oracle): machine-work market map — 35-table store,
  27-route REST, SDK, MCP, live dashboard, real but uneven data. This is
  the SIGNAL LAYER (§24) and the gap-map feed (§21) in one:440
  opportunities is a ready-made gap list the moment claims attach.
- **acom-openai** (`~/acom-openai`): OpenAI Agents SDK as pure execution
  backend behind our semantics (worker specs, GrantGate, run records,
  voice slice), 29 offline tests green, live voice deliberately stubbed.
  This is the reference pattern for ALL cognition-plane adapters:
  SDK owns mechanism, kernel owns meaning.
- **freaktown/pogtown** (sibling project): the stage + game truth. A
  mafia room is a deterministic seeded world with perfect ground truth
  (roles, votes, winner) — see below.

## 3. Import map — primitives, microprocessors, routines

Think in three import shapes:

**As microprocessors (adopt the instruction set, keep the body):**
- aloop IS the §7 loop. Import: point its task source at A-COM TASKs
  and its step receipts at TransitionReceipts. One adapter, no rewrite.
- cg IS the §18 promotion lab. Import: register A-COM procedures as
  candidates; promotion = beating incumbents in frozen worlds.
- aworker IS the grant envelope. Import: kernel `verify_grant` becomes
  the leaf check inside worker subdivision; ledger entries become
  RUN cost facts.

**As primitives (steal the object, reimplement the shell):**
- atask's content-addressed Run/Evidence receipts → already mirrored
  in `acom/store.py`; converge the hash formats next (one canonical
  receipt across atask/aloop/qp kills three dialects).
- cg's `run_id = hash(worldpack+scenario+candidate+seed+events)` →
  adopt verbatim for killfeed world runs (currently sequential, weaker).
- mw's append-only `raw_obs→events→current-state` → the template for
  the live HBM signal layer when Phase D starts.
- acom-openai's GrantGate + worker_spec → the template for EVERY
  future model adapter (Qwen, hermes, mimo): mechanism outside,
  semantics inside.

**As routines (callable procedures above the kernel):**
- `REPLAY`, `AB_TEST`, `BACKTEST` → implement against cg worlds AND
  killfeed worlds with one runner (same receipt in, same verdict out).
- `EXPAND_INPUT_SPACE` / gap scheduler → mw opportunities ranked by
  the §21 priority formula, claimed atomically by workers.
- `PROMOTE` → cg campaign with proposer-blind secret sets; receipt or
  it didn't happen (invariant 10).
- Killer routine nobody planned: **mafia rooms as procedure worlds.**
  Seeded tables with perfect ground truth, built-in adversaries
  (liars), and a blind human baseline — the cheapest possible arena
  for benchmarking deception, detection, and memory procedures
  before spending a dollar on markets. Wire `mafia_sim` outputs as
  CG-style worldpacks; the hermes-vs-heuristic league is already
  generating training environments every run.

## 4. Recommended import order (cheapest first)

1. Receipt-format convergence (atask/aloop/qp): one hash, three dialects
   die. Days, no behavior change.
2. Mafia tables as first procedure worlds (reuses running sims).
3. aloop task-source adapter (A-COM TASKs flow through the proven loop).
4. aworker grant checks inside kernel grant verification path.
5. mw gap feed → TASK generation (Phase E seed).
6. cg campaigns for procedure promotion (Phase C/D payoff).

## 5. Is this becoming a crypto protocol?

Yes — as a primitive, not a chain. Direction set 2026-09-12: qp is an
autonomous-agent crypto primitive, meaning every consequential artifact
is public-key verifiable with no server. Signed TransitionReceipts,
capability grants with cryptographic subjects, vendored Ed25519, zero
crypto dependencies (`docs/CRYPTO.md`). Still deliberately absent: chain,
consensus, staking/slashing, token, anchoring service. Protocol here
means verifiable interfaces; a coin would add attack surface before the
primitive has users. Pogtown/mafia threads are out of scope for qp —
games were scaffolding for worlds, not the product.
