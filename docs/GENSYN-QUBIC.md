# Gensyn + Qubic: what to implement, what to admire from afar

Cloned 2026-09-12 into `vendor/` (git-ignored, reference only):
`ree` (receipt-bearing reproducible inference), `axl` (P2P agent
network node), `rl-swarm` (RL training swarms), `qubic-core` (tick node).
No vendored code is copied into qp; everything below is clean-room.

## Implement (or already did)

1. **REE receipt envelope → DONE in `acom/runs.py`.** Their receipt binds
   model/prompt/output/repro-metadata; ours binds task/model/prompt-root/
   tools/inputs/outputs/cost/trace. Field names differ, shape rhymes.
   Action: add an `ree_compat` export mapping so our receipts read
   naturally to anyone coming from Gensyn. Small.
2. **Verde bisection → DONE in `killfeed/dispute.py`.** Minimal evidence
   subset preserving a verdict difference is our exact analogue of
   isolating the first differing operator. Convergent evolution noted.
3. **Ed25519 node identities (axl pattern).** Already our identity
   primitive (`acom/crypto.py`). Their nodes generate keys with openssl;
   ours with `keypair()` — same math, no dependency either way.
4. **Burn sinks attach at metered grants.** Every grant constraint with
   a price dimension is a future burn hook. No token work until live
   worlds settle; the hooks are already in the schema.

## Study, don't build (yet)

- **AXL userspace P2P** (Yggdrasil/gVisor, no TUN, no root, HTTP bridge,
  MCP/A2A inside): the right shape for replica transport when replicas
  stop living on one box. Today replicas are same-process; take the
  pattern, not the dependency.
- **Qubic ticks/quorum**: ticks confirm cursors-with-quorum is a sane
  shape, but 676 performance-selected computors is a different trust
  model from our permissionless replica agreement. Borrow the shape
  (epoch = cursor + roots), not the committee.
- **rl-swarm**: relevant only when procedures themselves get trained
  rather than selected. Parked until the gym has promotion demand.

## Hard boundaries (license + physics)

- REE's reproducible-execution binaries are PROPRIETARY (Binary License).
  The receipt FORMAT is portable; the bitwise reproducibility is not
  something we can vendor. Our honesty boundary stands: hash everything
  we control, attest cognition via adapters later, never claim GPU
  determinism we don't have.
- Nothing here runs on this box (no GPU, no Docker daemon needed):
  assessment is from code + docs, and any claim otherwise would be fake.
