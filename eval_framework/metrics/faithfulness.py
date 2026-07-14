from eval_framework.metrics.base import Metric, MetricResult
from eval_framework.judge import judge

FAITHFULNESS_CRITERIA = """Score how well the output is grounded in the provided context,
from 0 (the output makes claims not supported by the context - hallucination) to 1 (every
claim in the output is directly supported by the context). Penalize any information in the
output that cannot be traced back to the context, even if that information happens to be
true in general - faithfulness measures grounding, not general correctness."""


class Faithfulness(Metric):
    """A RAG-specific metric: does the generated answer actually stick to what
    was retrieved, or does it add unsupported claims? This is the metric that
    catches an LLM confidently stating something plausible-sounding that isn't
    actually in the source material it was given."""

    name = "faithfulness"
    threshold = 0.7

    def evaluate(self, test_case) -> MetricResult:
        if not test_case.retrieval_context:
            return MetricResult(
                self.name, 0.0, True,
                "Not applicable - no retrieval_context provided (this isn't a RAG test case)",
                applicable=False,
            )

        context_text = "\n".join(test_case.retrieval_context)
        content = f"Context:\n{context_text}\n\nOutput:\n{test_case.actual_output}"
        result = judge(FAITHFULNESS_CRITERIA, content)
        score = float(result.get("score", 0.0))
        passed = score >= self.threshold
        return MetricResult(self.name, round(score, 3), passed, result.get("reasoning", ""))
