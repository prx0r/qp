"""Root settlement adapter (plan2 Layer 7): anchor roots, nothing else.

Epoch struct mirrors the Base-ready shape from plan2 (epoch,
state_root, evidence_root, rules_hash). v0 anchors to a local
append-only log (hash-chained via acom.store); a chain writer later
posts the same struct without changing it. No chain calls, no spend.
"""
from acom import store as store_mod


def anchor(path: str, epoch: int, state_root: str, evidence_root: str,
           rules_hash: str) -> dict:
    """Append one epoch struct to the local anchor log. Same struct a
    chain writer would post later; no chain calls, no spend."""
    st = store_mod.Store(path)
    entry = st.append("epoch", {"epoch": epoch, "state_root": state_root,
                                "evidence_root": evidence_root,
                                "rules_hash": rules_hash})
    return {"ok": True, "epoch": epoch, "hash": entry["hash"],
            "cursor": st.cursor}


def verify_anchors(path: str) -> dict:
    """Recount epochs and re-verify the hash chain. Any rewrite, however
    small, fails here."""
    st = store_mod.Store(path)
    n = st.replay(lambda acc, t, p: acc + (1 if t == "epoch" else 0), 0)
    return {"ok": st.verify_chain(), "epochs": n}
