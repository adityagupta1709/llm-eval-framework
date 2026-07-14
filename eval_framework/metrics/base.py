from dataclasses import dataclass


@dataclass
class MetricResult:
    metric_name: str
    score: float
    passed: bool
    reason: str = ""
    applicable: bool = True


class Metric:
    """Every metric implements evaluate(test_case) -> MetricResult. Score is
    always 0.0-1.0, and `passed` is score >= threshold, so results from very
    different metric types can still be aggregated and reported consistently."""

    name = "base_metric"
    threshold = 0.5

    def evaluate(self, test_case) -> MetricResult:
        raise NotImplementedError
