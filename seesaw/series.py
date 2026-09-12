"""Live series store for H1–H3 (atunomousgoal §20): jump counts per
period, impact-vector breadths, consensus errors in event order. Starts
empty — structure first, live ingestion later. The hypotheses functions
adjudicate whatever is stored; nothing here invents data.
"""
from . import hypotheses


class Series:
    def __init__(self):
        self.jumps = []      # [(period, count)]
        self.vectors = []    # [impact dict, ...] in event order
        self.errors = []     # [abs consensus error, ...] in event order

    def record_jump_period(self, period: str, count: int):
        self.jumps.append((period, int(count)))

    def record_vector(self, vector: dict):
        self.vectors.append(dict(vector))

    def record_error(self, err: float):
        self.errors.append(float(err))

    def adjudicate(self) -> dict:
        """Run H1–H3 over stored series. Insufficient history reports
        itself instead of passing vacuously."""
        return {"H1": hypotheses.h1_frequency_shape(self.jumps),
                "H2": hypotheses.h2_complexity_shape(self.vectors),
                "H3": hypotheses.h3_forecast_error_shape(self.errors)}
