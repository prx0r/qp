# qp — A-COM kernel (Phase A) + agent crypto primitive

`theses/northstar.md` is the frozen thesis. This repo is the hard kernel:
tiny, deterministic, dependency-free (stdlib only) — plus public-key
verifiable receipts and capability grants (`docs/CRYPTO.md`).
MIT licensed, see `LICENSE`.

## Use

```bash
python3 -m pytest tests/ killfeed/ -q    # full suite
python3 -m killfeed.verify_all           # Definition of Done → PROVEN
python3 -m acom.cli world replay dram-1987
python3 -m acom.cli killfeed
```

## Map

Docs: `docs/ARCHITECTURE.md` (start here after the northstar),
`docs/OBJECTS.md`, `docs/RECEIPTS.md`, `docs/INVARIANTS.md`,
`docs/CIRCUITS.md` (executable claim graphs), `docs/KILLFEED.md`,
`docs/CRYPTO.md`, `docs/TRANSISTORS.md` (gates as logic).
Theses: `theses/northstar.md`, `theses/qpvalidate.md`,
`theses/circuitboard.md`, `theses/circuitboard2.md`, `theses/plan2.md`,
`theses/qubic-thesis.md`, `theses/crypto-thesis.md`,
`theses/ecosystem.md`, `theses/bayesian.md`, `theses/seesaw.md`.

## Rules (inherited, still binding)

- Game truth lives in pogtown; kernel never touches domains.
- Secrets in vault/env only, never in tree or chat. No spend, ever.
- Small diffs, verified before claimed. Owner pushes.
