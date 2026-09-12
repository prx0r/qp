"""A_t state variables + canonical feeds (beautyy.md §9).

A_t is not one number: it is the named vector the thesis lists
(coding autonomy, research horizon, discovery rate, cyber/bio
capability, parallelism, cost per human hour) PLUS Anthropic's five
measured primitives (complexity, skills, use case, autonomy, success).
Each variable is an append-only time series; latest() is the snapshot
Seesaw reasons over. Automation-weighted exposure follows the Stanford
finding encoded here: automation share moves employment, augmentation
share does not.
"""


VARIABLES = ("AI_CODING_AUTONOMY", "AI_RESEARCH_HORIZON",
             "AI_SCIENCE_DISCOVERY_RATE", "AI_CYBER_CAPABILITY",
             "AI_BIO_CAPABILITY", "AGENT_PARALLELISM",
             "AGENT_COST_PER_HUMAN_HOUR", "TASK_COMPLEXITY", "SKILL_LEVEL",
             "USE_CASE_MIX", "AI_AUTONOMY", "TASK_SUCCESS")


class Feeds:
    """Named time series. Values are illustrative until a real ingestor
    lands; the shape (variable → [(date, value, source)]) is the contract
    that ingestor must satisfy."""

    def __init__(self):
        self.series = {v: [] for v in VARIABLES}

    def append(self, variable: str, date: str, value: float, source: str):
        if variable not in self.series:
            raise ValueError(f"unknown variable {variable}")
        self.series[variable].append({"date": date, "value": float(value),
                                      "source": source})
        self.series[variable].sort(key=lambda r: r["date"])

    def latest(self) -> dict:
        return {v: (s[-1] if s else None) for v, s in self.series.items()}

    def automation_exposure(self, task_mix: dict) -> float:
        """Exposure = automation-weighted share (augmentation excluded).
        task_mix: {task: (automation_share_0_1, success_0_1)}."""
        tot = sum(a * s for a, s in task_mix.values())
        n = len(task_mix)
        return round(tot / n, 4) if n else 0.0

    def hazard(self, sector_exposures: dict) -> float:
        """H(t) = sum of sector hazard rates. Rising H means more sectors
        per unit time face repricing risk from capability jumps."""
        return round(sum(sector_exposures.values()), 4)
