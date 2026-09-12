"""WASM gate runner: the ABI proof (plan2 Layer 1).

Wasmtime executes gates/gap.wat; results must equal the Python reference
on every world snapshot. Anyone can rerun these gates without Python.
"""
import os

import wasmtime

_WAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gates",
                    "gap.wat")

_store = wasmtime.Store()
_mod = wasmtime.Module(_store.engine,
                       wasmtime.wat2wasm(open(_WAT).read()))
_linker = wasmtime.Linker(_store.engine)
_inst = _linker.instantiate(_store, _mod)
_gap = _inst.exports(_store)["gap"]

_DECODE = {1: "TRUE", 0: "FALSE", -1: "UNKNOWN"}


def gap_wasm(demand_low, demand_high, supply_low, supply_high,
             threshold=1.0) -> str:
    """NaN for any missing input → UNKNOWN (matches Python UNKNOWN)."""
    out = _gap(_store, float(demand_low), float(demand_high),
               float(supply_low), float(supply_high), float(threshold))
    return _DECODE[out]
