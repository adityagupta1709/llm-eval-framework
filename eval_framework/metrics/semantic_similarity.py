import math
from chromadb.utils import embedding_functions
from eval_framework.metrics.base import Metric, MetricResult

# Chroma's bundled local embedding model - no API call, no cost, runs on-device.
_embedder = embedding_functions.DefaultEmbeddingFunction()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class SemanticSimilarity(Metric):
    """Softer than ExactMatch: embeds both the actual and expected output and
    scores how close they are in meaning, not in exact wording. A rewording of
    the correct answer still scores well; an unrelated answer doesn't, even if
    it happens to share some words with the expected output."""

    name = "semantic_similarity"
    threshold = 0.75

    def evaluate(self, test_case) -> MetricResult:
        if test_case.expected_output is None:
            return MetricResult(
                self.name, 0.0, True,
                "Not applicable - no expected_output provided", applicable=False,
            )

        vectors = _embedder([test_case.actual_output, test_case.expected_output])
        score = _cosine_similarity(vectors[0], vectors[1])
        passed = score >= self.threshold
        return MetricResult(self.name, round(score, 3), passed, f"Cosine similarity: {score:.3f}")
