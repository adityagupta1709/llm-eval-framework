"""
Shows the framework used inside pytest, so evaluation becomes part of a
normal test suite instead of a separate manual step - the pattern that
makes 'eval driven development' actually enforceable in CI.

Run from the project root with: pytest examples/test_with_pytest.py -v
"""
from eval_framework.test_case import TestCase
from eval_framework.metrics.answer_relevancy import AnswerRelevancy
from eval_framework.metrics.g_eval import GEval


def test_answer_is_relevant():
    tc = TestCase(
        input="What is the capital of France?",
        actual_output="Paris is the capital of France.",
    )
    result = AnswerRelevancy().evaluate(tc)
    assert result.passed, result.reason


def test_answer_is_polite():
    tc = TestCase(
        input="Can you help me reset my password?",
        actual_output="Sure, I'd be happy to help you reset your password. Here's how...",
    )
    politeness = GEval(
        name="politeness",
        criteria="Score how polite and professional the tone of the response is, from 0 to 1.",
        threshold=0.6,
    )
    result = politeness.evaluate(tc)
    assert result.passed, result.reason
