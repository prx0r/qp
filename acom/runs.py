"""AComRunReceipt (plan2 Layer 2): bind everything a run controls.

No bitwise-reproducible AI needed: hash task, model id, prompt/context
root, tool calls, inputs, outputs, cost, event trace. Later Gensyn
REE / Pearl adapters strengthen attestation; the receipt shape stays.
"""
from .canonical import canonical, sha256_hex


def build(task: dict, model: str, prompt_root: str, tool_calls: list,
          inputs: list, outputs: list, cost: float, trace: list) -> dict:
    body = {
        "protocol": "acom/0.1",
        "kind": "RUN_RECEIPT",
        "task": task.get("id", "?"),
        "model": model,
        "prompt_root": prompt_root,
        "tool_calls": tool_calls,
        "inputs_root": _root(inputs),
        "outputs_root": _root(outputs),
        "cost": cost,
        "trace_root": _root(trace),
    }
    body["id"] = "runrcpt:" + sha256_hex(canonical(body))[:16]
    return body


def _root(items: list) -> str:
    from .canonical import merkle_root
    return merkle_root([sha256_hex(canonical(x)) for x in items])


def verify(receipt: dict, task=None, outputs=None) -> dict:
    """Recompute id; optionally rebind task id and outputs."""
    want = "runrcpt:" + sha256_hex(canonical(
        {k: v for k, v in receipt.items() if k != "id"}))[:16]
    if receipt.get("id") != want:
        return {"ok": False, "reason": "id mismatch"}
    if task is not None and receipt.get("task") != task.get("id"):
        return {"ok": False, "reason": "task mismatch"}
    if outputs is not None and receipt.get("outputs_root") != _root(outputs):
        return {"ok": False, "reason": "outputs mismatch"}
    return {"ok": True, "reason": "run receipt binds"}
