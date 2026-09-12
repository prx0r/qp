# qp — A-COM kernel (Phase A)

`northstar.md` is the frozen thesis. This repo is the hard kernel:
tiny, deterministic, dependency-free (stdlib only).

## Use

```bash
python3 -m pytest tests/ -q            # 12 checks
python3 -m acom.cli demo               # HBM claim + atask, same receipt type
python3 -m acom.cli verify runs/hbm-claim/receipt.json runs/hbm-claim/evidence.json
python3 -m acom.cli chain runs/hbm-claim/events.jsonl
```

## Map

Docs: `docs/ARCHITECTURE.md` (start here after northstar),
`docs/OBJECTS.md`, `docs/RECEIPTS.md`, `docs/INVARIANTS.md`.
Schemas: `schemas/acom.json`. Demos: `examples/`.

## Rules (inherited, still binding)

- Game truth lives in pogtown; kernel never touches domains.
- Secrets in vault/env only, never in tree or chat. No spend, ever.
- Small diffs, verified before claimed. Owner pushes.
