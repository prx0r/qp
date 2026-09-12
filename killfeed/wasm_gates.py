"""WASM gate runner: the ABI proof (plan2 Layer 1).

Wasmtime executes gates/*.wat; results must equal the Python reference
on every world snapshot. Anyone can rerun these gates without Python.
"""
import os

import wasmtime

_GDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gates")


def _load(name: str, export: str):
    store = wasmtime.Store()
    with open(os.path.join(_GDIR, name)) as f:
        mod = wasmtime.Module(store.engine, wasmtime.wat2wasm(f.read()))
    inst = wasmtime.Linker(store.engine).instantiate(store, mod)
    fn = inst.exports(store)[export]
    return store, fn


_STORES = {}


def _fn(name, export):
    if name not in _STORES:
        _STORES[name] = _load(name, export)
    return _STORES[name]


_DECODE = {1: "TRUE", 0: "FALSE", -1: "UNKNOWN"}


def gap_wasm(demand_low, demand_high, supply_low, supply_high,
             threshold=1.0) -> str:
    """NaN for any missing input → UNKNOWN (matches Python UNKNOWN)."""
    store, fn = _fn("gap.wat", "gap")
    out = fn(store, float(demand_low), float(demand_high),
             float(supply_low), float(supply_high), float(threshold))
    return _DECODE[out]


def need_wasm(intensity, minimum, relevant, kill) -> str:
    """relevant: 1/0 (NaN → UNKNOWN)."""
    store, fn = _fn("need.wat", "need")
    out = fn(store, float(intensity), float(minimum), float(relevant),
             float(kill))
    return _DECODE[out]


def lag_wasm(close_ymd: float, horizon_ymd: float) -> str:
    """Dates as YYYYMMDD numbers (NaN → UNKNOWN)."""
    store, fn = _fn("lag.wat", "lag")
    return _DECODE[fn(store, float(close_ymd), float(horizon_ymd))]


def wtp_wasm(price, qty, x=15.0, y=10.0) -> str:
    store, fn = _fn("wtp.wat", "wtp")
    return _DECODE[fn(store, float(price), float(qty), float(x), float(y))]


def nosub_wasm(share, threshold=0.25, redesign=0.0) -> str:
    """redesign: 1/0 (NaN → UNKNOWN)."""
    store, fn = _fn("nosub.wat", "nosub")
    return _DECODE[fn(store, float(share), float(threshold),
                       float(redesign))]
