# Transistors — gates over noisy cognition (circuitboard2.md)

A transistor: given input state, may current flow? An A-COM gate:
given evidence/state/grant, may this transition flow? Proposals are
the current; receipts are the traces; canonical state is the register.

Tested properties (`tests/test_board.py` + kernel suite):

- A gate with no evidence emits UNKNOWN, never a guess.
- Malformed circuits raise instead of scoring.
- Unknown constraint keys refuse instead of passing.
- An infeasible envelope returns no circuit instead of inventing one.
- A tampered receipt, forged grant, or mutated gate fails settlement.

That is digital logic for probabilistic cognition: constrain the noisy
substrate (LLM output) into hard compositional transitions, then
compose. CG is the expensive coprocessor: invoked only when the
transition matters enough to justify 20s and $0.40.
