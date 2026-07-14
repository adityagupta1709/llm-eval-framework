from eval_framework.metrics.base import Metric, MetricResult


class ExactMatch(Metric):
    """The simplest possible metric: does the output exactly equal the expected
    output (case-insensitive, whitespace-trimmed)? Only useful for tasks with
    one genuinely correct answer - most open-ended generation needs a softer
    metric like SemanticSimilarity or an LLM judge instead."""

    name = "exact_match"
    threshold = 1.0

    def evaluate(self, test_case) -> MetricResult:
        if test_case.expected_output is None:
            return MetricResult(
                self.name, 0.0, True,
                "Not applicable - no expected_output provided", applicable=False,
            )

        match = test_case.actual_output.strip().lower() == test_case.expected_output.strip().lower()
        score = 1.0 if match else 0.0
        reason = "Exact match" if match else "Output differs from expected_output"
        return MetricResult(self.name, score, match, reason)
