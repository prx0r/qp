# API — module map with entry points

Conventions: pure functions, no network, no clock. Every public
function carries a docstring; this file maps where to start.

## `acom/` — the hard kernel

| Module | Start here |
|---|---|
| `canonical` | `canonical()`, `sha256_hex()`, `obj_id()`, `merkle_root()` |
| `objects` | `make_claim/evidence/task/run/gate/grant/state()` |
| `store` | `Store.append/verify_chain/replay/event_root` |
| `gates` | `gate()` decorator, `execute()`, built-ins (`*-v1`) |
| `grants` | `verify_grant()` (expiry, constraints, predicates, signature) |
| `receipts` | `transition()`, `sign_receipt()`, `verify_receipt()`, `settle()` |
| `crypto` | `keypair()`, `sign_id/verify_id()`, `sign_grant/verify_grant_sig()` |
| `ed25519` | `pubkey()`, `sign()`, `verify()` (vendored, cross-tested) |
| `components` | `register/get()`, `record_run()`, `success_prob()`, `save/load()` |
| `versions` | `revise()`, `chain()`, `attach_run()`, `totals()`, `compare()`, `execute()`, `save_all/load_all()` |
| `synthesize` | `voi_decide()`, `synthesize()`, `ensure_defaults()` |
| `modules` | `load()`, `check()`, `seed_model_chips()` |
| `scheduler` | `plan_cost()`, `fits()` (tokens/seconds/dollars/risk) |
| `runs` | `build()`, `verify()` (run receipts) |
| `cli` | `init/demo/verify/chain/evidence/claim/world/state/killfeed` |

## `killfeed/` — historical validation engine

| Module | Start here |
|---|---|
| `engine` | `evaluate_trade()` (§3), `evaluate_snapshot/world()`, `kill_events()`, `world_state_root()`, gate templates |
| `circuit` | `evaluate/evaluate_margin()`, 25 ops, Kleene + margins |
| `validators` | `check_world()`, `v_*` suite (worlds → adversarial) |
| `verify_all` | `main()` — the Definition of Done |
| `dispute` | `minimize()`, `localize()` (no majority votes) |
| `replicas` | `agree()` (agreement or localized divergence) |
| `swarm` | `derive_jobs()` (FILL/REFRESH/CHALLENGE/FALSIFY) |
| `settle` | `anchor()`, `verify_anchors()` (local epoch log) |
| `gym` | `run_task()`, `compare()` (budgeted evidence reads) |
| `wasm_gates` | `gap_wasm()` (reference ABI proof) |

## `seesaw/` — shadow-price layer

| Module | Start here |
|---|---|
| `graph` | `score_node()` (S_i), `ai_exposure()`, `binding_constraint()`, `evaluate_event_claims()` |
| `beliefs` | `Graph.belief/update/finalize/propagate/expected_impact()` |
