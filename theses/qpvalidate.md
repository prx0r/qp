# A-COM / Killfeed — Historical Validation Specification

## Goal

Validate that the A-COM / Killfeed kernel actually works.

Do not validate that:

* the code compiles;
* schemas exist;
* an agent can write a report;
* a dashboard renders;
* a model can explain a historical trade.

Validate the central claim:

> **Given evidence available at historical time T, can the system deterministically determine whether a scarcity trade is ACTIVE, WARNING, KILLED, or UNKNOWN from five binary economic predicates, and can it detect the transition that ended the trade?**

The system is only considered useful if it works on historical examples where we already know what happened.

---

# 1. The canonical five predicates

Every scarcity trade MUST reduce to exactly these five top-level predicates:

```text
NEED
GAP
LAG
WTP
NOSUB
```

Definitions:

## NEED

Question:

> Does the valuable downstream activity still materially require this input?

Boolean:

```text
TRUE / FALSE / UNKNOWN
```

Example:

```text
Do frontier AI systems still require increasing high-bandwidth memory?
```

## GAP

Question:

> Does effective demand for the input exceed effective immediately usable supply?

Not installed capacity.

Not theoretical capacity.

Effective supply.

## LAG

Question:

> Is supply unable to close the demand gap quickly enough to eliminate the current scarcity regime?

This is forward-looking.

A shortage can exist today while `LAG = FALSE` if sufficient capacity is imminently arriving.

## WTP

Question:

> Are marginal buyers still accepting materially higher input prices without proportionally reducing quantity demanded?

This detects whether scarcity rents remain economically sustainable.

## NOSUB

Question:

> Is there no economically viable substitute, redesign, efficiency improvement, recycling path, or architecture change capable of materially removing the bottleneck?

---

# 2. Required internal states

Protocol state MUST NOT be binary-only internally.

Every predicate must return:

```text
TRUE
FALSE
UNKNOWN
```

Optional metadata:

```text
DISPUTED
STALE
SOURCE_FAILURE
```

But `SOURCE_FAILURE` must NEVER silently become `FALSE`.

Invariant:

```text
NO DATA != FALSE
BROKEN SOURCE != ZERO
UNKNOWN != FALSE
```

---

# 3. Trade state

Implement one deterministic function:

```python
evaluate_trade(predicates) -> TradeState
```

Required states:

```text
ACTIVE
WARNING
KILLED
UNKNOWN
```

Rules:

```text
if NEED == FALSE:
    KILLED

elif GAP == FALSE:
    KILLED

elif NEED == UNKNOWN or GAP == UNKNOWN:
    UNKNOWN

elif LAG == FALSE or WTP == FALSE or NOSUB == FALSE:
    WARNING

elif any of LAG/WTP/NOSUB == UNKNOWN:
    UNKNOWN

else:
    ACTIVE
```

Do not allow an LLM to override this.

---

# 4. Hard-kill priority

Rank predicates:

```text
1. NEED   weight 35
2. GAP    weight 25
3. LAG    weight 20
4. WTP    weight 12
5. NOSUB  weight 8
```

But weights are explanatory only.

`NEED = FALSE` or `GAP = FALSE` is an immediate kill regardless of weighted score.

---

# 5. Core object model

Implement these minimal objects:

```text
Evidence
Claim
Gate
ClaimEvaluation
TradeDefinition
TradeEvaluation
TransitionReceipt
HistoricalWorld
```

---

# 6. Evidence schema

```json
{
  "evidence_id": "sha256:...",
  "metric": "string",
  "value": 123.4,
  "unit": "string",

  "as_of": "YYYY-MM-DD",
  "valid_from": "YYYY-MM-DD",
  "valid_until": "YYYY-MM-DD|null",

  "source": {
    "source_id": "string",
    "class": "government|filing|company_guidance|industry_data|academic|news|other",
    "artifact_hash": "sha256:..."
  },

  "extraction": {
    "extractor": "manual|deterministic|llm",
    "extractor_version": "string",
    "reviewed": true
  }
}
```

Historical fixtures may use manually curated evidence.

The purpose of v0 is validating the kernel, not building the crawler.

---

# 7. Claim schema

```json
{
  "claim_id": "memory.hbm.gap.v1",

  "predicate_type": "GAP",

  "statement": "Qualified HBM demand exceeds effective qualified HBM supply.",

  "dependencies": [
    "metric.hbm.demand",
    "metric.hbm.effective_supply"
  ],

  "gate_id": "gate.gap.v1",

  "hard_kill": true
}
```

---

# 8. Gate interface

All gates MUST use the same deterministic interface.

Conceptually:

```python
evaluate(inputs, parameters) -> {
    "state": "TRUE|FALSE|UNKNOWN",
    "margin": float | null,
    "reason_code": str,
    "inputs_used": [...],
    "missing_inputs": [...]
}
```

Eventually compile to WASM.

For v0, Python reference implementation is allowed ONLY if:

* no network calls;
* no clock calls;
* deterministic input;
* deterministic output;
* canonical JSON serialization;
* same fixture produces byte-identical result.

Build a WASM implementation for at least one gate to prove the ABI.

---

# 9. Generic gate templates

Do not build ten custom historical-trade engines.

Build reusable gates.

## GAP gate

```text
TRUE:
    demand_low > supply_high * threshold

FALSE:
    demand_high <= supply_low

UNKNOWN:
    otherwise
```

## LAG gate

Inputs:

```text
expected_gap_close_date
scarcity_horizon_end
```

Rule:

```text
TRUE:
    gap_close_date > scarcity_horizon_end

FALSE:
    gap_close_date <= scarcity_horizon_end

UNKNOWN:
    missing dates / ranges overlap
```

## WTP gate

Example rule:

```text
TRUE:
    price_change >= +X
    AND quantity_change > -Y

FALSE:
    price rises materially
    AND quantity demanded falls beyond elasticity threshold

UNKNOWN:
    insufficient comparable periods
```

## NOSUB gate

Use explicit measurable proxy:

```text
TRUE:
    substitute_share < threshold
    AND announced substitution capacity insufficient

FALSE:
    substitute_share >= threshold
    OR redesign removes material bottleneck

UNKNOWN:
    insufficient adoption evidence
```

## NEED gate

Must be domain-configurable.

Typical rule:

```text
TRUE:
    required_units_per_output >= minimum_intensity
    AND downstream output remains relevant

FALSE:
    input intensity falls below kill threshold
    OR downstream activity abandons the input

UNKNOWN:
    insufficient evidence
```

---

# 10. TransitionReceipt

Every evaluation produces:

```json
{
  "protocol": "acom/0.1",

  "subject": "trade:dram-1988",

  "state_before": "ACTIVE",
  "state_after": "WARNING",

  "as_of": "1989-06-01",

  "claim_states": {
    "NEED": "TRUE",
    "GAP": "TRUE",
    "LAG": "FALSE",
    "WTP": "TRUE",
    "NOSUB": "TRUE"
  },

  "evidence_root": "sha256:...",
  "rules_hash": "sha256:...",
  "output_hash": "sha256:..."
}
```

Canonical serialization required.

---

# 11. HistoricalWorld

Each historical trade must exist as a replayable world.

Structure:

```text
worlds/
    dram-1987-1989/
        world.yaml
        timeline/
            1987-01-01.json
            1987-07-01.json
            ...
        expected.json

    fiber-1996-2001/
    palladium-1998-2001/
    ...
```

Each timeline snapshot contains only information considered available by that date.

Do not leak future information into previous snapshots.

This is critical.

---

# 12. The ten required historical worlds

Implement all ten.

## WORLD 1 — Oil 1979–1981

Scarcity thesis:

```text
oil supply disruption + inelastic industrial demand
```

Expected active conditions:

```text
NEED   TRUE
GAP    TRUE
LAG    TRUE
WTP    TRUE
NOSUB  TRUE initially
```

Primary kill sequence:

```text
Demand destruction / conservation
+
non-OPEC supply growth
+
inventory normalization
```

Most important kill predicate:

```text
GAP → FALSE
```

Potential preceding warning:

```text
WTP → FALSE
```

Expected system behavior:

```text
ACTIVE
→ WARNING
→ KILLED
```

---

## WORLD 2 — DRAM 1987–1989

Scarcity thesis:

```text
PC demand requires DRAM faster than manufacturers can supply it
```

Active:

```text
NEED TRUE
GAP TRUE
LAG TRUE
WTP TRUE
NOSUB TRUE
```

Primary kill:

```text
new DRAM capacity/yield + technology generation transition
```

Expected first warning:

```text
LAG → FALSE
```

Expected final kill:

```text
GAP → FALSE
```

This world is extremely important because it is the closest historical analogue to current HBM.

---

## WORLD 3 — Fiber / bandwidth 1996–2001

Scarcity thesis:

```text
internet traffic growth outruns telecommunications bandwidth capacity
```

Important feature:

```text
NEED stays TRUE even after trade dies.
```

Expected kill:

```text
GAP → FALSE
```

Because:

```text
capacity growth + DWDM efficiency > traffic growth
```

Expected:

```text
NEED TRUE
GAP FALSE
LAG FALSE
NOSUB FALSE
```

System MUST classify the trade as KILLED even though internet usage continues growing.

This is a mandatory anti-naive-growth test.

---

## WORLD 4 — Palladium 1998–2001

Scarcity thesis:

```text
automotive catalyst demand + Russian supply constraint
```

Primary kill:

```text
platinum substitution
+
thrifting
+
supply normalization
```

Expected earliest important flip:

```text
NOSUB → FALSE
```

Potential later:

```text
GAP → FALSE
```

System must detect substitution before relying only on falling spot price.

---

## WORLD 5 — China metals / iron ore 2003–2008

Scarcity thesis:

```text
Chinese infrastructure demand expands faster than mining/steel supply
```

Primary kill:

```text
global credit collapse + construction demand contraction
```

Expected:

```text
WTP / demand conditions deteriorate
GAP eventually → FALSE
```

The system must represent credit-dependent demand.

Do not encode "China needs infrastructure" as sufficient.

---

## WORLD 6 — Uranium 2003–2007/2011

Scarcity thesis:

```text
nuclear renaissance expectations + slow mine development + utility fuel need
```

Primary long-cycle warning:

```text
LAG → FALSE
```

as mine supply ramps.

Major exogenous kill:

```text
downstream nuclear demand shock
```

after Fukushima.

This should test:

```text
NEED can flip because downstream activity itself changes.
```

---

## WORLD 7 — Rare earths 2010–2011

Scarcity thesis:

```text
Chinese export restrictions constrain indispensable specialist materials
```

Critical kill evidence:

```text
buyers stop fully using available quotas
+
substitution/thrifting
+
alternative production
```

Expected warning:

```text
WTP → FALSE
```

and/or:

```text
NOSUB → FALSE
```

This is the canonical price-elasticity kill world.

---

## WORLD 8 — Lumber 2020–2021

Scarcity thesis:

```text
housing/remodeling demand exceeds reduced sawmill supply
```

Primary kill:

```text
idled supply restarts rapidly
```

Expected first flip:

```text
LAG → FALSE
```

Then:

```text
GAP → FALSE
```

This world should prove the system distinguishes:

```text
restart lead time
```

from:

```text
new capacity construction lead time
```

---

## WORLD 9 — Container shipping 2020–2022

Scarcity thesis:

```text
goods demand + port congestion reduce effective shipping capacity
```

Primary kill:

```text
congestion clears
+
goods demand normalizes
+
new ship capacity arrives
```

Expected key flip:

```text
GAP → FALSE
```

Important:

Installed fleet capacity may be unchanged.

The system MUST use:

```text
effective capacity
```

not total fleet tonnage.

---

## WORLD 10 — Nitrogen fertilizer 2021–2023

Scarcity thesis:

```text
high grain economics + gas/ammonia constraints create fertilizer shortage
```

Primary kill:

```text
natural gas prices fall
+
idled ammonia production restarts
+
trade flows normalize
+
farmer demand weakens
```

Expected first warning:

```text
LAG → FALSE
```

Potential:

```text
WTP → FALSE
```

Final:

```text
GAP → FALSE
```

The system must trace the upstream causal bottleneck:

```text
gas
→ ammonia
→ nitrogen fertilizer
→ crop economics
```

---

# 13. Expected-results file

Each world MUST contain manually frozen expected transitions.

Example:

```json
{
  "world_id": "fiber-1996-2001",

  "expected_states": [
    {
      "as_of": "1998-01-01",
      "trade": "ACTIVE"
    },
    {
      "as_of": "2000-01-01",
      "trade": "WARNING"
    },
    {
      "as_of": "2001-09-01",
      "trade": "KILLED"
    }
  ],

  "expected_first_kill_signal": "GAP",

  "required_invariant": {
    "NEED_at_kill": "TRUE"
  }
}
```

These files are frozen acceptance specifications.

Changing them requires a separate logged spec-change event.

---

# 14. Required validation scripts

Implement these exact classes of scripts.

## `validate_world.py`

Usage:

```bash
python validate_world.py worlds/dram-1987-1989
```

Must exit:

```text
0 = all expected states reproduced
1 = mismatch
```

Output should be machine-readable JSON plus short console output.

---

## `validate_all_worlds.py`

```bash
python validate_all_worlds.py
```

Required output:

```text
10 / 10 worlds passed
```

Exit non-zero otherwise.

---

## `validate_determinism.py`

Run each world at least 100 times.

Require:

```text
identical verdicts
identical canonical JSON
identical evidence roots
identical receipt hashes
```

Any difference = FAIL.

---

## `validate_no_future_leak.py`

Verify that snapshot at time T references no evidence with:

```text
as_of > T
```

Any future evidence = FAIL.

---

## `validate_unknown_semantics.py`

Delete required evidence from fixtures.

Expected result:

```text
UNKNOWN
```

NOT FALSE.

---

## `validate_source_failure.py`

Simulate source artifact missing/corrupted.

Expected result:

```text
SOURCE_FAILURE or UNKNOWN
```

NOT zero.

NOT FALSE.

---

## `validate_gate_mutation.py`

Mutation test the gate implementation.

Examples:

Change:

```text
demand > supply
```

to:

```text
demand < supply
```

The historical suite MUST fail.

If mutated logic still passes all tests, test coverage is inadequate.

---

## `validate_order_independence.py`

Shuffle evidence object ordering.

Same semantic evidence must produce identical result/hash after canonicalization.

---

## `validate_duplicate_evidence.py`

Submit the same underlying source through two copied articles.

The source-lineage logic must not count them as two independent sources.

---

## `validate_claim_dependency.py`

Flip a child claim and ensure dependent trade state recomputes correctly.

Example:

```text
NOSUB TRUE → FALSE
```

must create:

```text
ACTIVE → WARNING
```

without manual intervention.

---

# 15. Killfeed timing test

The system must not merely get the final state correct.

Measure:

```text
detection_delay =
system_kill_date - manually_defined_earliest_supported_kill_date
```

For each historical world.

Initial acceptable target:

```text
<= one fixture interval
```

For example, if snapshots are monthly:

```text
<= 31 days
```

Later we can optimize.

---

# 16. Killfeed precision test

For each world, calculate:

```text
false_kill_count
missed_kill_count
warning_lead_time
```

Required v0:

```text
false hard kills: 0
missed hard kills: 0
```

Warnings may be imperfect initially.

Hard kills may not be.

---

# 17. Counterfactual sanity tests

Each world must include at least one counterfactual fixture.

Example DRAM:

```text
demand = historical demand
supply = hypothetical abundant supply
```

Expected:

```text
GAP FALSE
TRADE KILLED
```

Fiber:

```text
traffic demand huge
capacity even huger
```

Expected:

```text
NEED TRUE
GAP FALSE
KILLED
```

Palladium:

```text
supply constrained
but substitution adoption = 60%
```

Expected:

```text
NOSUB FALSE
WARNING
```

This proves the rules, not historical memorization.

---

# 18. Adversarial tests

Build explicit attacks.

## Narrative attack

Input:

```text
"This shortage is the biggest opportunity in history."
```

with no structured evidence.

Expected:

```text
no state change
```

## Conflicting evidence attack

Demand range overlaps supply range.

Expected:

```text
UNKNOWN
```

not arbitrary TRUE.

## Stale evidence attack

All evidence older than allowed freshness.

Expected:

```text
UNKNOWN / STALE
```

## Fake high-authority source attack

Source claims `government` class but provenance contract fails.

Expected:

```text
REJECT
```

## Duplicate-source attack

Five news stories all repeat one original report.

Expected independent source count:

```text
1
```

---

# 19. Acceptance criteria for the kernel

The system is NOT complete until all are true:

```text
[ ] 10 historical worlds implemented
[ ] 10/10 expected trade-state timelines reproduced
[ ] 0 false hard kills
[ ] 0 missed hard kills
[ ] deterministic receipt hashes across 100 reruns
[ ] no future leakage
[ ] missing evidence → UNKNOWN
[ ] broken source != zero/false
[ ] duplicate sources collapse correctly
[ ] gate mutation causes tests to fail
[ ] child claim changes automatically recompute parent trade
[ ] every output has evidence_root
[ ] every output has rules_hash
[ ] every transition has state_before/state_after
[ ] historical result can be independently replayed
```

---

# 20. Build certificate

At the end produce:

```json
{
  "system": "acom-killfeed",
  "version": "0.1",

  "implementation_commit": "...",

  "implementation_commit": "...",

  "worlds": {
    "total": 10,
    "passed": 10,
    "failed": 0
  },

  "determinism": {
    "reruns_per_world": 100,
    "hash_mismatches": 0
  },

  "kill_detection": {
    "false_hard_kills": 0,
    "missed_hard_kills": 0
  },

  "adversarial": {
    "future_leak": "PASS",
    "source_failure": "PASS",
    "unknown_semantics": "PASS",
    "duplicate_source": "PASS",
    "gate_mutation": "PASS"
  },

  "status": "PROVEN"
}
```

Anything else is:

```text
IMPLEMENTED_UNVERIFIED
```

not complete.

---

# 21. Do not build live ingestion yet

Historical validation first.

Do NOT spend time initially on:

```text
X firehose
Reuters ingestion
blockchain
validator tokenomics
pretty UI
trading execution
Celestia
Cartesi
Pearl integration
RISC Zero
Neo4j
LLM orchestration frameworks
```

First prove:

> **the five predicates can correctly identify and kill known historical scarcity regimes.**

If we cannot do that on history, real-time Killfeed is theatre.

---

# 22. After 10/10 historical validation

Only then build:

```text
LIVE WORLD 1:
HBM / memory
```

Same schema.

Same gates.

Same receipt.

Difference:

```text
historical fixture
→ live evidence adapters
```

Then live output becomes:

```text
HBM

NEED   YES
GAP    YES
LAG    YES
WTP    YES
NOSUB  YES

STATE: ACTIVE

evidence_root: ...
rules_hash: ...
as_of: ...
```

Every update must be independently replayable.

---

# 23. Second live world

After HBM:

```text
XMR / ZEC relative thesis
```

This will test whether the protocol generalizes beyond pure supply bottlenecks.

Do not change the kernel.

Create different claims/gates above the same transition protocol.

---

# 24. Final invariant

The coding agent must optimize for this test:

```text
Given only the admissible evidence available at historical time T,
does the deterministic graph produce the state that an informed
observer should have been able to justify at T?
```

Not:

```text
Can an LLM retrospectively tell a convincing story?
```

The entire purpose of the project is to make those two things different.

---

# Definition of Done

Run:

```bash
python -m killfeed.verify_all
```

Expected:

```text
CORE                PASS
SCHEMAS             PASS
DETERMINISM         PASS
REPLAY              PASS
NO_FUTURE_LEAK      PASS
UNKNOWN_SEMANTICS   PASS
SOURCE_FAILURE      PASS
SOURCE_LINEAGE      PASS
MUTATION            PASS
DEPENDENCY_RECOMPUTE PASS

HISTORICAL WORLDS:
oil-1979             PASS
dram-1987            PASS
fiber-1996           PASS
palladium-1998       PASS
china-metals-2003    PASS
uranium-2003         PASS
rare-earths-2010     PASS
lumber-2020          PASS
containers-2020      PASS
fertilizer-2021      PASS

WORLD PASS RATE      10/10
FALSE HARD KILLS     0
MISSED HARD KILLS    0
HASH MISMATCHES      0

STATUS: PROVEN
```

Until that exact class of output exists from machine-executed tests, consider the implementation **unverified**.

The especially important part is the **mutation test**. If I deliberately invert `demand > supply` or change `UNKNOWN` to `FALSE` and the suite still reports green, then the harness is fake. The historical worlds should function like cryptographic-style test vectors: implementations can change, but valid implementations must reproduce the same state transitions.
