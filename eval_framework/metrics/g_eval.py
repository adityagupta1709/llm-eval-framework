from eval_framework.metrics.base import Metric, MetricResult
from eval_framework.judge import judge


class GEval(Metric):
    """A custom, rubric-driven LLM-as-judge metric - inspired by the G-Eval
    technique. Unlike ExactMatch or SemanticSimilarity, this doesn't need a
    ground-truth expected_output: you describe *what good looks like* in plain
    English, and the judge reasons about whether the output meets it.

    Use this for qualities that don't reduce to a single correct string -
    tone, helpfulness, safety, adherence to a style guide, and so on.
    """

    def __init__(self, name: str, criteria: str, threshold: float = 0.7):
        self.name = name
        self.criteria = criteria
        self.threshold = threshold

    def evaluate(self, test_case) -> MetricResult:
        content = f"Input: {test_case.input}\nOutput: {test_case.actual_output}"
        result = judge(self.criteria, content)
        score = float(result.get("score", 0.0))
        passed = score >= self.threshold
        return MetricResult(self.name, round(score, 3), passed, result.get("reasoning", ""))
