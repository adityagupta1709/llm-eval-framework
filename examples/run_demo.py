"""
Demo: evaluating a tiny FAQ-answering function with the eval framework.

This bot is intentionally minimal - a single free Groq call with no memory,
no tools, no RAG. Its only purpose is to give the framework something real
to evaluate, so this demo shows the framework working end to end rather
than just unit-testing metrics in isolation.

Run from the project root with: python -m examples.run_demo
"""
import json
from pathlib import Path
from groq import Groq
from eval_framework.config import GROQ_API_KEY
from eval_framework.test_case import TestCase
from eval_framework.runner import EvalRunner
from eval_framework.metrics.exact_match import ExactMatch
from eval_framework.metrics.semantic_similarity import SemanticSimilarity
from eval_framework.metrics.answer_relevancy import AnswerRelevancy
from eval_framework.report import print_report, save_json_report

client = Groq(api_key=GROQ_API_KEY)


def faq_bot(question: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        max_tokens=100,
        messages=[
            {"role": "system", "content": "Answer the question in one concise sentence."},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content.strip()


def main():
    dataset_path = Path(__file__).parent / "demo_dataset.json"
    with open(dataset_path) as f:
        raw_cases = json.load(f)

    test_cases = []
    for item in raw_cases:
        actual_output = faq_bot(item["input"])
        test_cases.append(
            TestCase(
                name=item.get("name"),
                input=item["input"],
                actual_output=actual_output,
                expected_output=item.get("expected_output"),
            )
        )
        print(f"Generated answer for: {item['name']}")

    runner = EvalRunner([ExactMatch(), SemanticSimilarity(), AnswerRelevancy()])
    results = runner.run(test_cases)

    print_report(results)
    report_path = save_json_report(results, filename="demo_report.json")
    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()
