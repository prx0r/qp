# Circuitboard 2 — A-COM as circuit board (2026-09-12, verbatim thesis)

Exactly. That framing is cleaner than “agent framework.”

Think:

> **A-COM = circuit board**
>
> **agents/models/tools = components**
>
> **gates = logic**
>
> **receipts = electrical traces / instrumentation**
>
> **canonical state = register/memory**
>
> **CG, WorkerKit, Killfeed, Pearl, search, human oracle = pluggable chips**

Then every component has a typed contract:

```text
component: CG_EVAL
input: candidate_run + worldpack
output: verified_score + receipt
cost: ~$0.40
latency: ~20s
reliability: measured
proof_level: V7
side_effects: none
```

Another component:

```text
component: WEB_SEARCH
input: query
output: evidence_candidates
cost: $0.003
latency: 2s
reliability: empirical
proof_level: UNVERIFIED_EVIDENCE
```

Another:

```text
component: KILLFEED_GATE
input: canonical evidence bundle
output: TRUE | FALSE | UNKNOWN
cost: ~$0
latency: 5ms
deterministic: yes
```

Another:

```text
component: PAID_REPORT
input: report_id
output: new evidence
cost: $1
latency: 10s
expected_information_gain: HIGH
```

Now the autonomous problem becomes **circuit synthesis**.

Given:

```text
GOAL:
"Determine whether HBM scarcity trade is still alive"

BUDGET:
$1.00

TIME:
60 seconds

REQUIRED_CONFIDENCE:
V7
```

the system composes a circuit:

```text
live feeds
   │
   ├── filings fetch ─────────────┐
   ├── industry-data fetch ──────┤
   └── paid report? ─────────────┤
                                 ▼
                          evidence normalizer
                                 │
                                 ▼
                         five Killfeed gates
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
               NEED             GAP             LAG ...
                 └───────────────┼───────────────┘
                                 ▼
                           ACTIVE / KILL
```

But if the evidence is ambiguous:

```text
GAP = UNKNOWN
```

the board can route through a more expensive component:

```text
UNKNOWN
   ↓
VOI gate
   ↓
"is $0.40 CG / $1 report worth it?"
   ↓
YES
   ↓
expensive component
   ↓
recompute
```

That is very microprocessor-like.

## And every component has a measured transfer function

This becomes the fun part.

For `/cg`, don't merely store:

> costs $0.40 / 20 sec.

Store empirical properties:

```yaml
component: cg_eval_v4

cost:
  median: 0.40
  p95: 0.56

latency:
  median_ms: 20000
  p95_ms: 31000

success:
  probability: 0.94

information_gain:
  mean: 0.31

applicability:
  - strategy_evaluation
  - counterfactual_replay
  - promotion_test

requirements:
  - replayable_world
  - acceptance_gate
```

These values come from **receipts**, not guesses.

Then A-COM can learn:

> For this class of problem, adding CG after cheap search raises success probability from 71% → 96%, costs $0.40 and 20s.

Now routing is an optimization problem.

$$
\text{Choose circuit}
=
\arg\max_C
\frac{\text{Expected verified outcome value}(C)}
{\text{cost}(C),\text{latency}(C)}
$$

subject to:

$$
ProofLevel(C) \ge RequiredProof
$$

## This makes models themselves ordinary chips

GPT, DeepSeek, Qwen etc. aren't “the agent.”

They're components:

```text
LLM_DEEPSEEK
  cost: x
  latency: y
  pass_rate(task_class): z

LLM_GPT
  cost: larger
  pass_rate(task_class): higher

LLM_MIMO
  cost: tiny
  pass_rate(task_class): ...
```

BATS/WorkerKit can choose them exactly like a compiler chooses an implementation.

Same with humans:

```text
HUMAN_ORACLE
cost: $3
latency: 15m
accuracy: .99 on visual ambiguity
```

Same with Pearl:

```text
PEARL_INFERENCE
cost: ...
proof_of_compute: yes
```

Same with CG:

```text
CG
expensive
slow
highly discriminative
```

## Then `mwgym` really is a circuit-design gym

It can generate:

```text
problem
available components
component costs
hidden world truth
budget
deadline
```

and ask:

> **What circuit should you build?**

Candidate A:

```text
cheap LLM → search → answer
```

Candidate B:

```text
cheap LLM
→ search
→ structured evidence
→ deterministic gates
```

Candidate C:

```text
cheap LLM
→ search
→ paid data
→ 20 Monte Carlo agents
→ CG
→ gates
```

Run historical worlds.

Measure:

```text
accuracy
cost
latency
false-positive rate
proof level
```

Now A-COM can actually **evolve optimal circuits**.

## This also clarifies what an `a-com` should mean

Maybe an A-COM isn't one component.

It's a **composable autonomous-computation module**:

```yaml
acom:
  id: research.killfeed.hbm.v3

  inputs:
    - entity
    - timestamp

  outputs:
    - five_predicates
    - trade_state

  components:
    - feed_filter
    - evidence_resolver
    - paid_data_gate
    - claim_evaluator

  constraints:
    max_cost: 1.00
    max_latency: 60s

  acceptance:
    proof_level: V7
```

So one A-COM can itself contain other A-COMs.

Recursive circuit boards.

### Tiny primitive

```text
GT(a,b)
```

### Component

```text
KILLFEED_GAP()
```

### Higher-order component

```text
SCARCITY_TRADE()
```

### Full board

```text
AUTONOMOUS_TRADE_RESEARCHER()
```

All with the same interface philosophy.

## The “clock cycles” become money and time

Normal CPU:

```text
instruction count
cycles
memory
```

A-COM:

```text
tokens
seconds
dollars
external risk
```

So the scheduler optimizes along four budgets.

A component could advertise:

```text
CG:
  20 seconds
  $0.40
  1 external call
  no capital risk

UNISWAP_SWAP:
  2 seconds
  $0.02 gas
  $500 capital risk
```

That last dimension matters enormously.

A-COM should treat **risk budget** just like compute budget.

## And gates are literally transistors

This is where the analogy becomes surprisingly exact.

A transistor says:

> given input state, may current flow?

A-COM gate says:

> given evidence/state/grant, may this transition flow?

```text
proposal
   │
   ▼
[ GATE ]
   │
 PASS?
   │
   ▼
state transition
```

Millions of agent thoughts can hit the gate.

Only valid ones propagate.

That is basically what digital logic did for unreliable analog electronics:

> constrain a noisy substrate into hard compositional state transitions.

Here the noisy substrate is **LLM cognition**.

That's probably the deepest framing yet:

> **A-COM is digital logic for probabilistic autonomous cognition.**

And CG is like an expensive specialized coprocessor: slow compared with a simple gate, but worth invoking when the state transition is important enough.
