# Circuitboard — logic gates over economic reality (2026-09-12, verbatim thesis)

Yes. That is the cleanest formulation.

We are basically building **logic gates over economic reality**.

The historical 10 are not examples anymore; they are **golden test vectors**. We work backwards from each successful/failed scarcity trade and ask:

> What minimal chain of boolean predicates would have correctly classified the regime *before* price collapsed?

Then we freeze those chains and test whether the same logic generalizes.

## The five terse statements become the top-level gate

For any scarcity trade:

1. **NEED** — does the valuable downstream thing still require X?
2. **GAP** — does demand for X exceed effective supply?
3. **LAG** — is supply too slow to close the gap?
4. **WTP** — are buyers still willing to pay up without materially cutting demand?
5. **NOSUB** — is there still no viable substitute/workaround?

Then:

$$
ACTIVE = NEED \land GAP \land LAG \land WTP \land NOSUB
$$

That is literally an AND gate.

A warning can be:

$$
WARNING = NEED \land GAP \land \neg(LAG \land WTP \land NOSUB)
$$

And a hard kill:

$$
KILLED = \neg NEED \lor \neg GAP
$$

So yes: logic gates.

## But each of those five is itself another logic circuit

Example: `GAP`.

```text
GAP
=
DEMAND_HIGH
AND
EFFECTIVE_SUPPLY_LOW
```

Then:

```text
DEMAND_HIGH
=
END_MARKET_VOLUME_UP
AND
INPUT_INTENSITY_NOT_FALLING
```

And:

```text
EFFECTIVE_SUPPLY_LOW
=
INSTALLED_CAPACITY_LOW
OR
UTILIZATION_HIGH
OR
CONGESTION_REMOVES_CAPACITY
OR
QUALIFICATION_LIMITS_USABLE_CAPACITY
```

Now you have a boolean DAG.

For memory:

```text
HBM_ACTIVE
│
├── NEED
│   ├── AI accelerator demand rising
│   └── memory bandwidth per accelerator not collapsing
│
├── GAP
│   ├── buyer demand > qualified supply
│   └── inventory buffer insufficient
│
├── LAG
│   ├── new fab/ramp lead time > shortage horizon
│   └── qualification delay persists
│
├── WTP
│   ├── HBM price ↑
│   └── committed quantity not ↓ materially
│
└── NOSUB
    ├── no architecture removes HBM need
    └── substitute adoption below threshold
```

Every leaf should eventually be reducible to a typed observation or deterministic calculation.

## The 10 historical worlds tell us what circuits we need

The trick is not to force all 10 into identical leaves.

Keep the **top five gates universal**, while the lower-level circuits are domain-specific.

### Fiber 2000

The system must output:

```text
NEED   TRUE
GAP    FALSE
LAG    FALSE
WTP    weakening
NOSUB  FALSE-ish
```

The killer is:

> Internet still needed bandwidth, but deployed/effective bandwidth exploded faster than traffic.

So our system learns:

**NEED can remain TRUE while the trade is dead.**

### Palladium 2001

```text
NEED   TRUE-ish
GAP    maybe TRUE initially
LAG    TRUE
WTP    weakening
NOSUB  FALSE
```

The key kill was substitution.

So:

**NOSUB must be capable of killing the scarcity premium before raw demand disappears.**

### Lumber 2021

```text
NEED   TRUE
GAP    TRUE initially
LAG    FALSE
WTP    weakening
NOSUB  TRUE
```

The important discovery:

**shortage duration matters more than shortage existence.**

If mills can restart quickly, `LAG` flips before `GAP`.

### Container shipping 2022

Installed fleet did not suddenly change much.

But:

```text
EFFECTIVE_CAPACITY
```

did.

So the logic needs:

```text
effective_supply != installed_supply
```

That becomes a reusable primitive.

## Therefore the historical test suite should work backwards like this

For each historical trade:

### Step 1 — define the expected state timeline

Example:

```text
DRAM 1987
ACTIVE

DRAM 1988
ACTIVE

DRAM early 1989
WARNING

DRAM late 1989
KILLED
```

### Step 2 — identify the first predicate that should have flipped

Example:

```text
first flip:
LAG TRUE → FALSE
```

### Step 3 — identify the observable leaves that justify that flip

Example:

```text
new fab output committed
yield improvement
inventory rebuild
next-gen DRAM supply ramp
```

### Step 4 — make those leaves machine-readable

```text
capacity_growth_12m > demand_growth_12m
inventory_days > threshold
lead_time_change < 0
```

### Step 5 — verify the gate produces the historical transition

Then freeze it.

That's how we work backwards.

## This means the actual protocol is probably a typed boolean circuit language

Something like:

```yaml
claim: memory.hbm.active

op: AND

children:
  - memory.hbm.need
  - memory.hbm.gap
  - memory.hbm.lag
  - memory.hbm.wtp
  - memory.hbm.nosub
```

Then:

```yaml
claim: memory.hbm.gap

op: GT

left:
  metric: memory.hbm.demand_12m

right:
  op: MUL
  args:
    - metric: memory.hbm.effective_supply_12m
    - const: 1.05
```

Now the claim graph is literally executable.

## You only need a handful of logical primitives

Probably:

```text
AND
OR
NOT
GT
GTE
LT
LTE
EQ
IN_RANGE
FRESH
COUNT_VALID_SOURCES
CHANGED_BY
TREND_UP
TREND_DOWN
```

Plus temporal operators:

```text
TRUE_FOR
FALSE_FOR
CHANGED_WITHIN
BEFORE
AFTER
```

And maybe uncertainty operators:

```text
UNKNOWN_IF_MISSING
TRUE_IF_LOW_BOUND_GT_HIGH_BOUND
```

That's enough for most of Killfeed.

## The killer insight

We should not ask:

> “What does the AI think about the trade?”

We ask:

> “What is the current truth value of each gate in the causal circuit?”

And then:

```text
price action
news
tweets
research reports
```

are just candidate evidence that might flip one leaf.

That is much cleaner.

## The 10 historical examples become unit tests for economic logic

Exactly like:

```text
input vector
→ expected output
```

For each date snapshot:

```text
[NEED, GAP, LAG, WTP, NOSUB]
→ expected trade state
```

Then deeper:

```text
raw metrics
→ leaf predicates
→ intermediate predicates
→ top five
→ trade state
```

This is essentially a circuit.

And then live Killfeed is just:

```text
new evidence arrives
↓
affected leaves recompute
↓
dependency graph propagates
↓
top-level gate changes
↓
emit kill event
```

So yes, we're reinventing logic gates, but for **economic causal state**.

The nice part is that once this is rigid, agents become incredibly useful again: they are not deciding truth; they are continuously searching for **new evidence that could flip a gate**.
