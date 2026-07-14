from eval_framework.metrics.base import Metric, MetricResult
from eval_framework.judge import judge

RELEVANCY_CRITERIA = """Score how directly the output addresses the input question, from
0 (does not address the question at all) to 1 (directly and completely addresses it).
Penalize vague, evasive, or off-topic answers even if they contain some factually correct
information about something else."""


class AnswerRelevancy(Metric):
    """Catches a specific failure mode ExactMatch and Faithfulness both miss:
    an answer that's fluent and even factually fine, but doesn't actually
    answer what was asked."""

    name = "answer_relevancy"
    threshold = 0.7

    def evaluate(self, test_case) -> MetricResult:
        content = f"Question: {test_case.input}\nAnswer: {test_case.actual_output}"
        result = judge(RELEVANCY_CRITERIA, content)
        score = float(result.get("score", 0.0))
        passed = score >= self.threshold
        return MetricResult(self.name, round(score, 3), passed, result.get("reasoning", ""))
