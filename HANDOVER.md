# HANDOVER — qp (2026-09-12, Phase A built)

`northstar.md` frozen thesis. Phase A kernel BUILT, all green:
12/12 pytest, both demos settle against one receipt type, CLI
verify + chain clean, no secrets, stdlib only.

## Run it

```bash
python3 -m pytest tests/ -q
python3 -m acom.cli demo && python3 -m acom.cli chain runs/hbm-claim/events.jsonl
```

## What's real

`acom/` (canonical, objects, store, gates, grants, receipts, cli),
`schemas/acom.json`, `examples/` (hbm-claim V7 + atask-backup V4),
`docs/` (ARCHITECTURE, OBJECTS, RECEIPTS, INVARIANTS).
Deterministic: same inputs → same receipt ids (tested).

## What's next (northstar §40)

Phase B adapters (atask, cg, WorkerKit, Killfeed), then Phase C
procedures (REPLAY, RED_TEAM, TOOL_DISCOVERY, VOI). PROMOTE path does
not exist yet by design (invariant 10). WASM gate ABI declared in
schema; native predicates behind the same interface until a runner lands.
Signatures carried, authority layer signs later; grants fail closed now.
