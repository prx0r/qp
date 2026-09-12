# Crypto-protocol landscape + layered build plan (2026-09-12)

Source thesis filed verbatim in essence; key decisions preserved.

## Position

A-COM/Killfeed is a verifiable state-transition protocol for autonomous
agents, more fundamental than "a chain". A blockchain may later sit
beneath as settlement; the protocol replays without one. Do NOT start
with a custom blockchain.

## Closest existing primitives

- **Gensyn REE/Verde**: execution receipts binding input to output;
  Verde isolates the first differing operator so only it is recomputed.
  Closest to "dispute only the smallest hard transition". Study before
  inventing execution crypto. Three-layer model (P2P comms, on-chain
  identity, verification) mirrors RUN/RECEIPT/WORKER-ID/PAYMENT/DISPUTE.
- **Olas**: agent services off-chain + consensus gadget + L1/L2 anchors;
  20.5M agent transactions. Closest agent-service layer.
- **Bittensor**: incentive/discovery market (Yuma stake-weighted); use
  for evidence discovery competition, NEVER for truth (deterministic
  gates decide where verification is objective).
- **Pearl**: cognition attestation (PoUW from MatMul), not correctness.
- **Qubic**: useful work for ranking + quorum consensus; outsourced
  computations ≈ compute router; see `qubic-thesis.md`.
- **Lagrange**: proving as a service for later proof volume.
- **Celestia**: evidence availability (bytes retrievable), not truth.
- **EigenLayer AVS**: staked validators later; slash ONLY objective
  faults (wrong WASM result, wrong root, double-sign), never predictions.

## Killfeed's edge over all of them

They prove "did this computation execute as specified". We prove
"given canonical evidence E, rule set C, gate V, is predicate P
TRUE/FALSE" — and then TRUE→FALSE transitions as KILL EVENTs.

## Build layers (in order)

0. A-COM Core (tiny; canonical JSON, hashing, receipts, gates, grants).
1. WASM gates (need/gap/lag/wtp/nosub; rerunnable by anyone).
2. Gensyn-style run receipts (hash all controlled inputs today).
3. Existing state assets (append-only events, replay, UNKNOWN semantics).
4. Killfeed five predicates → ACTIVE/WARNING/KILLED/UNKNOWN + KillEvent.
5. Agent swarm restricted to FILL/REFRESH/CHALLENGE/FALSIFY jobs.
6. Five-replica adversarial validators; diverge → localize (Verde-style),
   never bare majority vote.
7. Anchor roots only (epoch/state/evidence/rules) to an existing chain.

## Possible end-state chain (LAST, maybe never)

Not a smart-contract chain: a proof ledger for autonomous cognition
(EvidenceCommitment, ClaimTransition, RunReceipt, Grant, Challenge,
Resolution). Consensus = agree on valid A-COM transitions.

## First executable: acom-node + replica agreement

```bash
acom init
acom evidence add ...
acom claim evaluate memory.hbm.gap
acom world replay dram-1988
acom verify receipt.json
acom state root
acom killfeed
```

Nodes A/B/C run the same fixtures; acceptance is identical state_roots
across all 10 worlds. Settlement backend (Base, EigenLayer, Gensyn,
Bittensor, Qubic, Pearl, own chain) stays an adapter choice.

## References

[1] Gensyn Verde — verification for ML over untrusted nodes
[2] Autonolas whitepaper summary — agent services + consensus gadget
[3] Bittensor Yuma consensus docs
[4] Pearl Research — proof of useful work
[5] Qubic docs — consensus/quorum
[6] Lagrange ZK prover network
[7] Celestia docs — data availability
[8] EigenLayer whitepaper (slashing dangers)
[9] Gensyn infrastructure (OP Stack L2 + REE)
[10] Olas — agent transaction counts, Sep 2026
