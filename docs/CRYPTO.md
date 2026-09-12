# CRYPTO — qp as an autonomous-agent crypto primitive

qp is a crypto primitive in the precise sense: every consequential
artifact is public-key verifiable by anyone, with no server, no chain,
and no token. Cryptography here is integrity + capability, nothing else.

## Identities

- Ed25519, vendored pure-Python (`acom/ed25519.py`), zero dependencies.
- Correctness is cross-proven against the `cryptography` package in
  `tests/test_crypto.py` (sign→verify in both directions), not trusted.
- Identity = pubkey hex. Address = sha256(pubkey)[:16] for display.
- Private keys live in the vault or caller memory. NEVER in the tree,
  NEVER in chat, NEVER in any artifact. The kernel has no key storage
  and no key generation ceremony beyond `crypto.keypair()`.

## What verifies what

| Artifact | Signed over | Verified by | Failure means |
|---|---|---|---|
| TransitionReceipt | receipt id | `verify_receipt` | content forged or signer lying |
| Grant (pubkey subject) | canonical grant body | `verify_grant` | forged capability — denied |
| Grant (named subject) | — (presence only) | `verify_grant` | unsigned — denied (fail closed) |

Rules: the kernel never signs (`sign_receipt` is authority tooling);
`signer` rides outside the hashed body (id commits to content,
signature commits signer to id); unknown grant constraint keys are
rejected, not ignored.

## Explicitly NOT built

No chain, no consensus, no staking/slashing, no token, no anchoring
service. If two agents hold the same bytes they reach the same verdict
— that property is the whole primitive. Anchoring (publishing Merkle
roots somewhere public) can be added without changing a single gate.
