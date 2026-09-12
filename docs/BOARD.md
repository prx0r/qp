# BOARD — the full circuit board, one map (circuitboard2.md executable)

Computation flows left to right; money and risk flow with it; receipts
flow back up as learning. Every box below names its module.

```text
breakthrough
  │  seesaw/waiting.py (log, impact map, lag detection, t_star)
  ▼
evidence reads (budgeted)
  │  killfeed/gym.py (strategies, oring_leverage)
  ▼
canonical evidence ──► acom/store.py (append-only log)
  │
  ├─► killfeed/circuit.py ──► NEED/GAP/LAG/WTP/NOSUB ──► trade state
  │        ▲                         │ (margins = distance to flip)
  │        │                    ┌────┴─────┐
  │   dag_compile.py      kill_events   swarm jobs
  │   (DAG→circuits)      (TRUE→FALSE)  (FILL/REFRESH/CHALLENGE/FALSIFY)
  │                                           ▲
  │                      tjp_falsifiers.py ───┘ (37-cell attack corpus)
  ▼
belief/graph update ──► seesaw/beliefs.py (log-odds/beams, FACT clamps)
  │  seesaw/jumps.py (impact vectors, alpha windows)
  │  seesaw/monitor.py (flips → challenges, argmax → dossiers)
  │  seesaw/feeds.py (A_t vector) + series.py (H1–H3 adjudication)
  ▼
divergence ──► seesaw/graph.divergence() ──► backtest → positions
  │  killfeed/backtest.py (walk-forward, turnover costs)
  ▼
grants + budgets ──► acom/grants.py, scheduler.py (tokens/s/$/risk)
  ▼
anchors ──► killfeed/settle.py (local epoch log; chain later)
```

Learning loops (receipts upward):
- `acom/versions.py` — run history per component version; `compare()`
  gates promotion on measured deltas, never vibes.
- `acom/synthesize.py` — VOI-gated circuit choice under budget/proof.
- `acom/scheduler.py` — four-budget fit (p95 by default).
- `killfeed/dispute.py` + `replicas.py` — localize, never vote.
- `killfeed/reverse.py` — market-implied probs or honest refusal.
- `killfeed/obsolescence.py` — dying-base detector (short leg).
- `acom/runs.py` — run receipts + REE-shaped export.
- `killfeed/wasm_gates.py` — reference ABI proofs (gap/need/lag/wtp/nosub).

Theses: theses/ (northstar, qpvalidate, circuitboard×2, plan2, seesaw,
beautyy, atunomousgoal, bayesian, qubic/crypto, ecosystem, postreview).
Vendor reference (ignored): qubic-core, ree/axl/rl-swarm/repops-demo,
CommonGround/Chronicle, II-Commons-Skills, genii, postagi + tjp memos.
