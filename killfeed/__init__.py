"""Killfeed historical-validation engine (qpvalidate.md §1–§11)."""
from .engine import (  # noqa: F401
    ENGINE_VERSION, PREDICATES, evaluate_snapshot, evaluate_trade,
    evaluate_world, independent_sources,
)
