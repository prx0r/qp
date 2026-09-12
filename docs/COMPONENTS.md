# Versioned components — history is the product

`acom/versions.py` over `acom/components.py`. Every version is
content-hashed and chained (`supersedes`); nothing is ever edited in
place. Each version carries its complete run history — receipt id,
model, latency, cost, outcome, outputs root — and totals derive from
that log on every call, so a total can never disagree with its runs.

- `revise()` snapshots the old spec into the archive first; the old
  version stays queryable forever.
- `execute()` runs the handler twice and refuses to record on any
  byte difference: determinism verified, not assumed.
- Duplicate receipt ids are refused (replay is not a new run).
- `compare()` needs history on BOTH sides or declines to judge.
- `save_all`/`load_all` persist registry + archive together.

New versions start with empty history: past performance belongs to
the version that earned it. Promotion compares, never inherits.
