# Accretion — work modifies persistent search state (ant pattern)

Qubic's ant direction: mining search accumulates instead of restarting.
Our equivalent, already wired:

- Belief cells persist (`Graph.save/load`): a new session inherits all
  nodes, edges, priors, and update logs, then extends. Proven in
  `test_graph_persistence_inherits_cells`.
- Swarm jobs (`killfeed/swarm.py`) point at unfilled cells: FILL missing
  metrics, REFRESH stale sources, CHALLENGE warnings, FALSIFY thin
  margins. Each completed job appends evidence; nothing researched twice.
- Component versions (`acom/versions.py`) accumulate run history per
  version; promotion compares archives, never vibes.
- Killfeed worlds are append-only; new snapshots extend timelines.

Rule: any agent starting work first loads the cell. Starting from
scratch when a cell exists is measured waste (northstar invariant 14).
