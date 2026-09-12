# Seesaw — shadow-price tracking for constraint migration (2026-09-12, verbatim thesis)

Yes — the **seesaw** framing is mathematically better.

The thing making a bottleneck valuable and the thing that kills it are the **same variable viewed from opposite sides**.

If HBM is valuable because:

$$
AI\_Value \uparrow
\quad\land\quad
HBM\_Need \uparrow
\quad\land\quad
Supply\_Response \downarrow
$$

then the trade dies when one of those reverses:

$$
HBM\_Need \downarrow
\quad\lor\quad
Supply\_Response \uparrow
\quad\lor\quad
AI\_Value \downarrow
$$

That is a seesaw, not five unrelated conditions.

## The cleaner mathematical formulation

Forget `NEED/GAP/LAG/WTP/NOSUB` for a second.

Suppose the economy is maximizing output:

$$
\max_x U(x)
$$

subject to constraints:

$$
g_i(x) \leq b_i
$$

Each constrained resource has a **shadow price**:

$$
\lambda_i
=
\frac{\partial U^*}{\partial b_i}
$$

Interpretation:

> How much more economic value would the system create if it had **one additional unit** of resource \(i\)?

That is almost exactly what we're trying to trade.

If one additional HBM stack lets you deploy highly valuable AI compute:

$$
\lambda_{HBM} \gg 0
$$

HBM has scarcity rent.

If AI discovers a radically different architecture that barely needs external memory:

$$
\lambda_{HBM} \rightarrow 0
$$

Trade dead.

That's much cleaner than “NOSUB became false.”

---

# Seesaw

I'd define the protocol around:

$$
\boxed{
SV_i = \lambda_i
}
$$

where `SV` = **scarcity value** of constraint \(i\).

We don't directly observe \(\lambda\), so we infer it from observable signals:

$$
\hat{\lambda_i}
=
f(
\text{marginal downstream value},
\text{constraint tightness},
\text{supply response},
\text{substitutability}
)
$$

The trade is:

$$
\boxed{
\hat{\lambda_i} \uparrow
}
$$

Killfeed is:

$$
\boxed{
\Delta\hat{\lambda_i} < 0
}
$$

And a hard kill is approximately:

$$
\boxed{
\hat{\lambda_i}\rightarrow0
}
$$

Now the whole system has one conceptual variable.

## Why this matters for Post-AGI

Your deeper insight is:

> AGI doesn't merely increase demand for existing things. It continuously **moves the binding constraint**.

That's much more profound.

Today:

```text
AI capability
    ↓
GPU shortage
    ↓
HBM shortage
    ↓
CoWoS shortage
    ↓
power shortage
```

Tomorrow AI improves chip design.

Maybe:

```text
HBM bottleneck ↓↓↓
```

But that does **not** imply “hardware industries die.”

It means the constraint migrates.

Maybe the new architecture creates:

```text
novel materials bottleneck
fabrication bottleneck
analog-memory manufacturing bottleneck
packaging bottleneck
power-delivery bottleneck
experimental-validation bottleneck
```

Current research already illustrates that possibility. AI hardware is being pushed toward specialized accelerators, 3D compute-memory integration, and potentially memristor-based compute-in-memory specifically because moving data between memory and compute is itself a bottleneck. ([Nature][1])

So Seesaw should not ask:

> Is memory valuable?

It asks:

> **Where is the binding constraint on the production of valuable intelligence right now?**

That's the trade.

---

# The AGI equation

Imagine economic output depends on:

$$
Y =
F(
I,
E,
M,
P,
D,
R,
V,
...
)
$$

Where:

* \(I\) = intelligence/cognition
* \(E\) = energy
* \(M\) = memory
* \(P\) = physical manufacturing
* \(D\) = data
* \(R\) = real-world experimentation
* \(V\) = verification

Pre-AGI, intelligence itself is scarce:

$$
\lambda_I \gg 0
$$

As AI improves:

$$
Supply_I \rightarrow \infty
$$

therefore:

$$
\lambda_I \downarrow
$$

But complementary constraints become binding:

$$
\lambda_E,\lambda_M,\lambda_P,\lambda_R,\lambda_V \uparrow
$$

Then AI solves one of those constraints.

Maybe it invents a vastly better memory architecture:

$$
\lambda_M \downarrow
$$

Value moves somewhere else.

**Seesaw is the system that tracks that migration.**

---

# This explains the “AI cures cancer tomorrow” nightmare

Exactly.

Suppose pharma valuation currently depends on:

```text
scarce therapeutic discovery
+
scarce medicinal chemistry
+
scarce target identification
```

Then AGI suddenly makes target identification/drug design almost free.

Does pharma disappear?

No.

The value chain moves.

Current 2026 drug-discovery reviews actually make the relevant point: computational discovery is improving, but clinical translation, conditional biological data, validation, trials and approvals remain the major real-world constraints. ([Nature][2])

So:

Before:

```text
DISCOVERY          █████████
PRECLINICAL        █████
CLINICAL TRIALS    ██████████
MANUFACTURING      ████
REGULATION         █████
```

After superhuman drug design:

```text
DISCOVERY          █
PRECLINICAL        █████████
CLINICAL TRIALS    ███████████████
MANUFACTURING      ███████
REGULATION         █████████
```

The constraint migrates.

Potentially:

$$
\lambda_{drug\ discovery} \downarrow
$$

while:

$$
\lambda_{clinical\ trial\ capacity} \uparrow
$$

$$
\lambda_{biological\ validation} \uparrow
$$

$$
\lambda_{manufacturing} \uparrow
$$

The pharma company whose moat was:

> our scientists discover molecules better than others

could be destroyed.

The company whose moat is:

> global trial network + manufacturing + regulatory dataset + patient access

might become *more valuable*.

That's exactly what Seesaw needs to detect.

---

# Same with Navier–Stokes

Suppose AI suddenly solves some class of fluid dynamics problems far better.

That doesn't make aerospace worthless.

It changes:

```text
scarce CFD reasoning
```

into abundant.

Then new bottlenecks could become:

```text
wind-tunnel validation
materials
certification
manufacturing tolerances
test aircraft
engine production
```

The design space suddenly expands.

That can actually make physical validation **more scarce**, because AI proposes vastly more candidates.

This is the pattern:

$$
CandidateGeneration \uparrow\uparrow\uparrow
$$

while:

$$
PhysicalValidationCapacity
$$

doesn't instantly increase.

Therefore:

$$
\lambda_{validation} \uparrow
$$

This is probably one of the most important Post-AGI trades.

---

# So the real Seesaw primitive is a dependency chain

For any valuable output:

```text
VALUABLE OUTPUT
    ↓
required inputs
    ↓
required inputs of those inputs
    ↓
...
```

Example:

```text
AI inference
├── algorithms
├── compute
│   ├── accelerator
│   │   ├── logic
│   │   ├── HBM
│   │   └── packaging
│   ├── power
│   └── cooling
└── data
```

Each edge has:

$$
RequirementIntensity_{a\rightarrow b}
$$

Each node has:

$$
Capacity_b
$$

Then constraint pressure can be approximated as:

$$
CP_b
=
\frac{
Demand_b
}{
EffectiveCapacity_b
}
$$

And scarcity value:

$$
SV_b
\approx
CP_b
\times
MarginalValueUnlocked_b
\times
ResponseTime_b
\times
(1-Substitutability_b)
$$

That is a better continuous formula.

---

# The seesaw itself

For input \(i\):

$$
\boxed{
S_i
=
\frac{
M_i \cdot D_i \cdot T_i
}{
C_i \cdot A_i
}
$$

Where:

* \(M_i\) = marginal downstream value unlocked by another unit
* \(D_i\) = excess demand / constraint pressure
* \(T_i\) = time required to expand supply
* \(C_i\) = effective capacity
* \(A_i\) = availability of alternatives

Not rigorous economics in the theorem sense, but much closer to the correct object.

Then:

### Bull trade

$$
S_i \uparrow
$$

### Peak warning

$$
S_i > 0
\quad\land\quad
\frac{dS_i}{dt}<0
$$

### Dead trade

$$
S_i \approx0
$$

---

# The critical derivative is actually with respect to AI capability

This is where Seesaw becomes explicitly Post-AGI.

For every industry/input:

$$
\boxed{
AI\ Exposure_i
=
\frac{\partial S_i}{\partial A}
}
$$

where \(A\) = AI capability.

Three categories:

### Positive AI derivative

$$
\frac{\partial S_i}{\partial A}>0
$$

AI getting smarter makes the bottleneck **more valuable**.

Examples potentially:

* power;
* transformer capacity;
* physical experiments;
* calibration;
* verification;
* privacy;
* authenticated data.

### Negative AI derivative

$$
\frac{\partial S_i}{\partial A}<0
$$

AI directly attacks the scarcity.

Potentially:

* routine coding;
* generic research;
* some chip-design labor;
* some molecule-discovery labor;
* some legal analysis.

### Ambiguous / migration

AI reduces one constraint but induces another.

Memory could be exactly this.

Today:

$$
\partial S_{HBM}/\partial A > 0
$$

because scaling AI increases HBM demand.

But if AI discovers compute architectures that dramatically reduce data movement:

$$
\partial S_{HBM}/\partial A
$$

could flip negative.

Research on compute-in-memory and memristive architectures is explicitly motivated by the energy/time bottleneck of transferring data between separate compute and memory units. ([Nature][1])

**That derivative flip is the ultimate Killfeed event.**

---

# This gives Seesaw a beautiful state representation

For every node:

```text
HBM

CURRENT SHADOW VALUE       HIGH
d(shadow value)/dt         POSITIVE
d(shadow value)/dAI        POSITIVE

CONSTRAINT                 BINDING
SUPPLY RESPONSE            SLOW
SUMMARY
SUBSTITUTION               LOW
```

Then one day:

```text
HBM

CURRENT SHADOW VALUE       HIGH
d(shadow value)/dt         NEGATIVE   ← WARNING
d(shadow value)/dAI        NEGATIVE   ← MAJOR REGIME CHANGE
```

Even though HBM prices may still be at all-time highs.

That's exactly the signal we want.

---

# The biggest thing you were missing

AI doesn't just create more demand.

It attacks the **production function itself**.

That's different from previous technological booms.

Railways increased steel demand but steel wasn't simultaneously designing its own replacement.

AI does both:

```text
AI ↑
→ demand for bottleneck X ↑
```

while simultaneously:

```text
AI ↑
→ ability to redesign around bottleneck X ↑
```

So every Post-AGI bottleneck has **two opposing AI forces**.

Call them:

$$
DemandEffect_i(A)
$$

and:

$$
InnovationEffect_i(A)
$$

Then:

$$
\boxed{
\frac{\partial S_i}{\partial A}
=
DemandEffect_i
-
ConstraintDestruction_i
}
$$

This may be the central Seesaw equation.

For HBM today:

$$
DemandEffect_{HBM}
\gg
ConstraintDestruction_{HBM}
$$

Bullish.

Eventually maybe:

$$
ConstraintDestruction_{HBM}
>
DemandEffect_{HBM}
$$

Dead.

For software developers:

probably already:

$$
ConstraintDestruction
>
DemandEffect
$$

for some classes of work.

For electricity:

probably:

$$
DemandEffect
\gg
ConstraintDestruction
$$

because intelligence can't trivially abolish physical energy requirements.

---

# That is Seesaw

I would define the thesis as:

> **As artificial intelligence makes cognition abundant, economic value migrates continuously toward whichever complementary constraints remain hardest to relax. AI simultaneously increases demand for some constraints and accelerates the destruction of others. Seesaw tracks the resulting movement in shadow prices and emits cryptographically reproducible state transitions when a constraint becomes or ceases to be binding.**

That is substantially stronger than “find AI bottlenecks.”

And the trading question becomes:

$$
\boxed{
\text{What becomes the next binding constraint as AI capability increases?}
}
$$

while Killfeed asks:

$$
\boxed{
\text{Which currently binding constraint is AI about to destroy?}
}
$$

Those are the two sides of the seesaw.

[1]: https://www.nature.com/articles/s41928-026-01645-w?utm_source=chatgpt.com "Searching for success with semiconductor start-ups for artificial intelligence | Nature Electronics"
[2]: https://www.nature.com/articles/s41573-026-01496-2?utm_source=chatgpt.com "Artificial intelligence in drug discovery — what it is, where we stand and the path forward | Nature Reviews Drug Discovery"

---

# Live test — Navier–Stokes, September 2026

The immediate effect so far is **mostly on mathematics/research labor, not on engineering-sector economics**.

OpenAI’s September 8 result addresses the **existence/smoothness Millennium problem** by producing a finite-time singularity construction plus a Lean formalization. That is a major theoretical result, but it does **not** make ordinary Navier–Stokes simulation, CFD, turbulence modeling, aircraft design, weather forecasting, or industrial fluid engineering “solved.” ([OpenAI][1])

So in Seesaw terms, the first scarcity that clearly moved was:

$$
\lambda_{\text{elite mathematical discovery}} \downarrow
$$

Not:

$$
\lambda_{\text{CFD software}} \downarrow
$$

and definitely not yet:

$$
\lambda_{\text{wind tunnels / physical validation}} \downarrow
$$

There is already evidence of exactly that first shift. Reporting around the result focuses on mathematicians worrying that AI can now attack frontier problems at a pace humans cannot match; Terence Tao has described the broader trajectory as potentially moving toward an “era of proof abundance.” OpenAI says the Navier–Stokes effort used up to 10,000 agents over roughly 88 hours, which is basically an existence proof that brute-force parallel mathematical cognition has become economically deployable. ([The Wall Street Journal][2])

That gives us a very clean Seesaw event:

```text
BEFORE

Frontier mathematical insight
    scarcity = VERY HIGH
    human lead time = years / decades

AFTER

Frontier mathematical insight
    scarcity ↓ sharply

AI compute
    demand ↑↑

formal verification
    importance ↑↑

human theorem verification / interpretation
    importance ↑

research priority selection
    importance ↑
```

OpenAI itself says people still set research priorities and judge results while agents expand research capacity; internally it reports about **3.1 agent-workdays per human workday** in its research organization. ([OpenAI][3])

That is already a Seesaw shift.

## What *didn't* happen

Searched specifically for evidence that aerospace, CFD, simulation or engineering companies were repriced because of the Navier–Stokes result.

No credible direct market effect found yet.

The broad September 8 equity move was instead about **GPT-6 Astra threatening software companies**: Salesforce, Intuit and ServiceNow fell roughly 4–5%, while the software/services index dropped about 1.4%. Reuters doesn't attribute a CFD/aerospace sector move to the Navier–Stokes announcement. ([Reuters][4])

That's actually useful negative evidence.

The hypothetical:

> “AI solves Navier–Stokes → CFD becomes worthless immediately”

would have been **FALSE**.

Seesaw should have prevented that mistake because we would ask what constraint the theorem actually removes.

## The actual dependency graph

Ordinary fluid-engineering output looks more like:

```text
AIRCRAFT / TURBINE / WEATHER MODEL
            │
            ▼
    physical fluid dynamics
            │
      ┌─────┼─────────────┐
      ▼     ▼             ▼
   theory   numerical    empirical
            solution     validation
      │       │             │
      ▼       ▼             ▼
mathematics  CFD       wind tunnel /
                       sensors / tests
```

OpenAI changed:

```text
theory → understanding of global regularity/singularity
```

It did not automatically change:

```text
mesh resolution
computational cost
turbulence closure
boundary conditions
measurement uncertainty
physical validation
certification
```

Those are different scarcity nodes.

And there's an extra nuance: one tracker notes that the announced construction concerns **smoothly forced 3D Navier–Stokes**, while the unforced global-regularity problem remains distinct. So even saying simply “Navier–Stokes is solved” collapses important technical details. ([Navier-Stokes Equations Explained][5])

## This is a fantastic first live Seesaw test

Encode the event as:

### Claim A

> AI can now solve frontier mathematical problems previously requiring years/decades of elite human research.

Before Sep 8:

`UNKNOWN / increasingly likely`

After Sep 8:

`TRUE`

Evidence:

* OpenAI proof;
* Lean formalization;
* external mathematical response. ([OpenAI][1])

### Claim B

> Navier–Stokes mathematical theory is the binding constraint on industrial CFD deployment.

Result:

`FALSE`

Because industry already routinely solves numerical Navier–Stokes approximations; the Millennium problem concerned global mathematical regularity, not whether engineers could compute flow fields.

### Claim C

> Physical validation becomes obsolete because of this result.

Result:

`FALSE`

No causal mechanism.

### Claim D

> Scarcity of frontier theoretical-math labor falls.

Result:

`TRUE / major warning`

### Claim E

> Scarcity of formal verification rises.

Likely:

`TRUE`

Because when thousands of agents can emit giant mathematical arguments, **checking** increasingly becomes the complement.

That's a quintessential Seesaw transition:

$$
AI\ mathematical\ capability \uparrow
$$

causes:

$$
ShadowPrice(\text{human theorem discovery}) \downarrow
$$

and potentially:

$$
ShadowPrice(\text{verification / trusted proof infrastructure}) \uparrow
$$

## It also shows why Seesaw matters

The headline is:

> **AI SOLVES NAVIER–STOKES**

A dumb thematic trading system could infer:

> short simulation / engineering.

Our circuit should infer:

> identify exactly which production constraint was relaxed.

And the answer currently appears to be:

> **frontier mathematical search**, not physical fluid engineering.

That distinction is probably the whole product.

The next useful exercise would be to take **5–10 actual AI breakthroughs from 2025–26**—Navier–Stokes, major coding capability jumps, protein/drug design advances, cyber capability, robotics—and reconstruct the **before/after shadow-price graph** to see whether Seesaw would have correctly identified what got cheaper and what became the next bottleneck.

[1]: https://openai.com/index/navier-stokes-solution/?utm_source=chatgpt.com "OpenAI | On the Navier–Stokes Millennium Prize Problem"
[2]: https://www.wsj.com/tech/ai/openai-millennium-prize-navier-stokes-math-2bf230f8?utm_source=chatgpt.com "WSJ | OpenAI Says It Has Solved a Millennium Prize Problem-a Holy Grail of Math"
[3]: https://openai.com/index/the-work-now-within-reach/?utm_source=chatgpt.com "The Work Now Within Reach | OpenAI"
[4]: https://www.reuters.com/business/wall-st-futures-slip-oil-surge-puts-markets-edge-2026-09-08/?utm_source=chatgpt.com "Reuters | S&P 500 falls as AI worries hit software makers, not CFD"
[5]: https://navier-stokes.org/navier-stokes-problem-solved/?utm_source=chatgpt.com "Navier-Stokes Equations Explained | September 2026 Update"
