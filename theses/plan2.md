# Plan 2 — crypto-protocol landscape + layered build (2026-09-12, verbatim thesis)

Yes — this is becoming crypto-protocol-shaped, but I would **not** start by building a custom blockchain.

The thing we have is more fundamental than “a chain”:

> **A-COM/Killfeed = a verifiable state-transition protocol for autonomous agents.**

A blockchain can later become one settlement/consensus layer beneath it. The protocol should remain independently replayable without one.

The closest existing primitives I found are surprisingly strong.

* **Gensyn REE** is probably the closest match to our execution-receipt idea. It packages model execution so the same model/input/config can be reproduced across supported hardware and emits a cryptographic receipt binding input to output. Their Verde work goes further: when two ML executions disagree, it isolates the first differing operator and only that operation needs recomputation. That is extremely close to our “agent can compute arbitrarily; dispute only the smallest hard transition” philosophy. ([Gensyn][1])
* **Olas / Autonolas** is probably closest to our agent-service layer. Their architecture explicitly runs complex agent services off-chain, replicas execute the same service, a consensus gadget agrees on state/actions, and important values are anchored to an L1/L2. They already model reusable components, agents and services rather than treating the LLM as the whole system. ([Olas][2])
* **Bittensor** is the best reference for incentivizing open-ended workers. Miners produce a commodity; validators score them; Yuma uses stake-weighted consensus and clips unsupported minority scoring. Useful for evidence discovery and agent competition, but weaker than our deterministic gate when objective verification is possible. ([Bittensor][3])
* **Pearl Research** is relevant specifically for proving that AI work happened. Their PoUW makes matrix multiplication—the core compute in inference—the useful work being mined, with a lightweight verification construction rather than duplicating full inference. This is excellent as a future **cognition attestation** layer, but it does not prove the semantic conclusion is correct. ([Pearl Research Labs][4])
* **Qubic** is philosophically adjacent: useful PoW contributes to ANN training, while the top 676 Computors form the epoch validator set and 2/3+ quorum agrees on chain computation. It's interesting because it explicitly separates useful AI work used for ranking from normal transaction consensus. ([Qubic Docs][5])
* **Lagrange** is the proof-factory model: expensive work occurs outside consensus and a distributed prover network produces cheap-to-check ZK proofs. They report more than 14M proofs generated. ([Lagrange][6])
* **Celestia** solves evidence availability rather than truth: blob data stays retrievable and apps can prove availability/inclusion using namespaced Merkle trees and DAS. That becomes interesting once Killfeed needs public evidence bundles that challengers must be able to retrieve. ([Celestia Documentation][7])
* **EigenLayer AVSs** are relevant if we eventually want economically staked validators without bootstrapping our own security. Their own whitepaper is quite explicit about the dangers of buggy slashing logic, which is exactly why I would delay this part until our hard gates are mature. ([EigenCloud][8])

But the one I hadn't appreciated enough is **Gensyn**.

They've independently landed on almost our exact three-layer model:

> P2P communication
>
> * persistent on-chain identity
> * cryptographic verification of computation.

Their chain is now an **EVM-compatible OP Stack L2** for identity, payments, stake and reputation, while REE provides verifiable execution. ([Gensyn][9])

That is basically:

```text
A-COM                Gensyn

RUN                   REE run
RECEIPT               REE receipt
WORKER ID             CHAIN identity
PAYMENT               CHAIN settlement
DISPUTE               Verde
AGENT NETWORK         AXL
```

So I would absolutely study their implementation before inventing cryptographic execution infrastructure.

## But Killfeed has one thing they don't

They're mostly proving:

> **Did this computation execute as specified?**

We're trying to prove:

> **Given this canonical evidence and rule set, is this economic predicate currently TRUE or FALSE?**

Those are different.

Gensyn can potentially prove:

```text
model M
+
prompt P
+
config C
→
output O
```

Killfeed needs:

```text
evidence E
+
claim definition C
+
gate V
→
TRUE
```

And then:

```text
TRUE_t → FALSE_t+1
=
KILL EVENT
```

That second layer is ours.

---

# Should Killfeed be a blockchain?

### Eventually, maybe.

### Right now: definitely not.

A custom chain immediately forces us to solve:

* networking;
* consensus;
* validator selection;
* Sybil resistance;
* incentives;
* upgrades;
* wallets;
* state sync;
* slashing;
* economic security;
* chain explorers;
* token economics.

None of those prove the actual thing we care about:

> can we correctly detect the end of historical scarcity trades?

Our current acceptance test is much better:

```text
10 historical worlds
↓
frozen evidence
↓
5 predicates
↓
deterministic transition
↓
10/10 correct kill regimes
```

If that doesn't work, a blockchain merely decentralizes incorrect answers.

---

# What I'd actually build right now

I think there's an awesome **A-COM local protocol** that could be real in days rather than months.

## Layer 0 — A-COM Core

Rust if possible.

Tiny.

```text
canonical JSON
BLAKE3/SHA256
event log
state roots
TransitionReceipt
Gate ABI
Grant verification
dependency DAG
replay
```

No LLM dependencies.

---

# Layer 1 — WASM gates

Compile gate programs to WASM.

For Killfeed:

```text
need.wasm
gap.wasm
lag.wasm
wtp.wasm
nosub.wasm
```

Input:

```json
{
  "claim": "...",
  "evidence": [...]
}
```

Output:

```json
{
  "state": "TRUE",
  "margin": 0.17
}
```

Then anyone can rerun them.

This is the Telegraph-style part.

---

# Layer 2 — Gensyn-style receipts

Every agent run should produce:

```text
AComRunReceipt
```

binding:

```text
task
model
prompt/context root
tool calls
inputs
outputs
cost
event trace
```

We don't need full bitwise reproducible AI immediately.

Hash everything we control today.

Later add Gensyn REE/Pearl proof adapters for stronger cognition attestation.

---

# Layer 3 — OpenPāṭala/QDW state

Use the stuff we already built:

```text
append-only events
canonical replay
state digest
hard verification ladder
UNKNOWN != FALSE
evidence provenance
```

This is already more important than chain consensus.

---

# Layer 4 — Killfeed

Exactly five conditions per scarcity trade:

```text
NEED
GAP
LAG
WTP
NOSUB
```

All depend on canonical evidence.

Then:

```text
ACTIVE
WARNING
KILLED
UNKNOWN
```

And changes emit:

```text
KillEvent
```

---

# Layer 5 — agent swarm

Now point unlimited agents at it.

But give them only these jobs:

```text
FILL
REFRESH
CHALLENGE
FALSIFY
```

A tweet doesn't change truth.

It creates a task.

Example:

> “Samsung HBM expansion will end shortage.”

becomes:

```text
candidate target:
memory.hbm.LAG

effect:
TRUE → FALSE
```

Agents then search only hard data.

---

# Layer 6 — adversarial validators

Now we introduce crypto-ish structure.

Run five independent replicas:

```text
validator A
validator B
validator C
validator D
validator E
```

Same:

```text
state root
evidence root
gate hash
```

Require identical output.

This is already basically a permissionless validation protocol without having a chain.

If:

```text
A TRUE
B TRUE
C TRUE
D TRUE
E TRUE
```

easy.

If:

```text
A TRUE
B TRUE
C FALSE
```

don't majority vote immediately.

We want:

> **find exactly why deterministic execution diverged.**

Gensyn Verde is a particularly strong inspiration here. ([Gensyn][1])

---

# Layer 7 — settle only the root

Only after all of that works would I anchor:

```text
epoch
state_root
evidence_root
rules_commit
```

to an existing chain.

This costs almost nothing.

Base would be perfectly adequate.

Example:

```solidity
struct KillfeedEpoch {
    uint64 epoch;
    bytes32 stateRoot;
    bytes32 evidenceRoot;
    bytes32 rulesHash;
}
```

That's enough to timestamp and make historical rewrites obvious.

No custom blockchain.

---

# The first crypto-native version could be an AVS

If we want crypto-economic validators quickly:

**EigenLayer AVS** is arguably more sensible than making a chain.

Operators:

1. download evidence bundle;
2. reproduce Killfeed state;
3. sign root;
4. get rewarded;
5. provably incorrect attestations can eventually be penalized.

The key word is **eventually** because slashing must be extraordinarily conservative. EigenLayer themselves emphasize unintended-slashing risk and governance vetoes during early stages. ([EigenCloud][8])

For Killfeed, slash only objective faults:

```text
signed wrong WASM result
signed wrong evidence root
double-signed incompatible root
```

Never:

> “your economic prediction turned out wrong.”

---

# Or Bittensor could provide evidence discovery

This may actually be the best Bittensor integration.

Don't make miners decide truth.

Have miners compete to supply:

```text
freshest evidence
best source resolution
novel hard data
source lineage
missing metrics
```

Then validators run our deterministic Killfeed gates.

So:

```text
BITTENSOR
= incentive/discovery market

KILLFEED
= truth-transition layer
```

That separation is excellent.

Yuma is built for subjective utility consensus; we should use it where the commodity really is subjective, not where a deterministic gate exists. ([Bittensor][3])

---

# The niche intellectual protocols I think matter most

If you're looking for the “SafeTrade weird genius coin” category rather than established infra, I would study these technology families:

### Qubic

Why interesting:

> useful compute determines validator eligibility.

That is intellectually close to our assumption:

> unlimited computation should be doing useful work.

But Qubic's Quorum still validates ordinary state transitions after that. ([Qubic Docs][5])

### Pearl Research

Why interesting:

> computation itself can generate both useful inference and cryptographic/economic work.

Potential A-COM use:

```text
prove cognition occurred
```

not:

```text
prove cognition was correct.
```

([Pearl Research Labs][4])

### Gensyn

Probably **the most important one to us right now**.

They've developed:

```text
bitwise/reproducible ML operators
receipt-bearing inference
dispute localization
agent identities
AI settlement L2
```

This is very close to the A-COM substrate. ([Gensyn][1])

### Olas

Most mature example I've found of:

```text
autonomous agents
+
wallets
+
service composition
+
off-chain consensus
+
on-chain settlement
```

They report over **20.5M total agent transactions** and over **14.6M agent-to-agent transactions** as of September 10, 2026, so this isn't just architecture diagrams anymore. ([Olas][10])

### Lagrange

Strong reference for:

```text
distributed proving as a service
```

which becomes relevant once A-COM has huge volumes of proofs. ([Lagrange][6])

### Celestia

Potential evidence availability layer.

Not truth.

Not compute.

Just:

> prove the bytes required to challenge state remain available.

([Celestia Documentation][7])

---

# The really insane version

I think the ultimate architecture looks like:

```text
                       WORLD
                         │
                         ▼
              HIGH-SIGNAL FEEDS
                         │
                         ▼
                  IDEA SEEDS
                         │
                         ▼
              UNLIMITED AGENTS
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        search         simulate       attack
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                     PROPOSALS
                         │
                         ▼
              CANONICAL EVIDENCE
                         │
                         ▼
                A-COM HARD GATES
                   WASM / proofs
                         │
                         ▼
                 VERIFIED STATE
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          KILLFEED       MW        ATASK
             │           │           │
             └───────────┼───────────┘
                         ▼
                     ACTIONS
                         │
                         ▼
                  REAL OUTCOMES
                         │
                         ▼
                      CG/MWGYM
                         │
              replay 1,000 variants
                         │
                         ▼
                 BETTER PROCEDURES
                         │
                         └────→ back into A-COM
```

And then crypto gradually hardens every boundary:

```text
Gensyn / Pearl
→ computation receipts

Celestia
→ evidence availability

RISC Zero / Lagrange
→ succinct execution proof

EigenLayer
→ economic security

Base/Ethereum
→ canonical root settlement
```

No single project has to own all of it.

---

# The possible end-state custom chain

Only once Killfeed/A-COM actually has meaningful traffic would I consider a chain.

And if we ever do one, I would **not** make a normal smart-contract blockchain.

I'd make something much narrower.

Blocks contain primarily:

```text
EvidenceCommitment
ClaimTransition
RunReceipt
Grant
Challenge
Resolution
```

Consensus is not:

> execute arbitrary Solidity.

It's:

> agree on valid A-COM state transitions.

Almost like a **proof ledger for autonomous cognition**.

A block could literally be:

```text
epoch 84920

+ evidence: micron-10q
+ evidence: trendforce-memory
+ claim HBM.LAG TRUE→FALSE
+ task 18ac resolved
+ run 00fe accepted
+ procedure v18 promoted
+ grant 4aa2 revoked

state_root: ...
```

That would be genuinely interesting.

But it should be the **last** thing we build, not the first.

## The thing I'd build tomorrow

I would build an `acom-node` executable:

```bash
acom init
acom evidence add ...
acom claim evaluate memory.hbm.gap
acom world replay dram-1988
acom verify receipt.json
acom state root
acom killfeed
```

Then:

```text
Node A
Node B
Node C
```

run independently against the same historical fixture.

Acceptance condition:

```text
state_root_A
==
state_root_B
==
state_root_C
```

for **all 10 historical worlds**.

Once that works, we have something much more interesting than a whitepaper:

> **a deterministic multi-node economic truth state machine whose output can already be cryptographically committed, independently replayed, challenged, and eventually economically secured.**

At that point, whether the settlement backend is Base, EigenLayer, Gensyn, Bittensor, Qubic, Pearl or our own eventual chain becomes an adapter choice rather than the architecture itself.

[1]: https://www.gensyn.ai/research/verde-a-verification-system-for-machine-learning-over-untrusted-nodes?utm_source=chatgpt.com "Gensyn | Verde: a verification system for machine learning over untrusted nodes"
[2]: https://olas.network/documents/whitepaper/Whitepaper%20Summary%20v1.0.pdf?utm_source=chatgpt.com "AUTONOLAS WHITEPAPER SUMMARY — TECHNICAL ARCHITECTURE"
[3]: https://www.bittensor.com/docs/internals/consensus?utm_source=chatgpt.com "Yuma Consensus — Bittensor Docs"
[4]: https://pearlresearch.ai/research/blog/proof-of-useful-work?utm_source=chatgpt.com "Proof of Useful Work"
[5]: https://docs.qubic.org/overview/consensus/?utm_source=chatgpt.com "Qubic Consensus aka Quorum | Qubic Docs"
[6]: https://lagrange.dev/zk-prover-network?utm_source=chatgpt.com "Lagrange | ZK Prover Network — Decentralized Proving"
[7]: https://docs.celestia.org/learn/celestia-101/data-availability/?utm_source=chatgpt.com "Celestia Documentation"
[8]: https://docs.eigenlayer.xyz/assets/files/EigenLayer_WhitePaper-88c47923ca0319870c611decd6e562ad.pdf?utm_source=chatgpt.com "EigenLayer: The Restaking Collective"
[9]: https://www.gensyn.ai/infrastructure?utm_source=chatgpt.com "Gensyn | Infrastructure"
[10]: https://olas.network/?locale=en&utm_source=chatgpt.com "Olas | Co-own AI"
