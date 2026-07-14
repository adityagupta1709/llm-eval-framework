from dataclasses import dataclass
from typing import List
from eval_framework.metrics.base import Metric, MetricResult


@dataclass
class CaseResult:
    test_case_name: str
    results: List[MetricResult]

    @property
    def all_passed(self) -> bool:
        applicable_results = [r for r in self.results if r.applicable]
        if not applicable_results:
            return True
        return all(r.passed for r in applicable_results)


class EvalRunner:
    def __init__(self, metrics: List[Metric]):
        self.metrics = metrics

    def run(self, test_cases: list) -> List[CaseResult]:
        all_results = []
        for i, tc in enumerate(test_cases):
            name = tc.name or f"case_{i + 1}"
            metric_results = [m.evaluate(tc) for m in self.metrics]
            all_results.append(CaseResult(name, metric_results))
        return all_results
