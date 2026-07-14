import argparse
import json
from eval_framework.test_case import TestCase
from eval_framework.runner import EvalRunner
from eval_framework.metrics.exact_match import ExactMatch
from eval_framework.metrics.semantic_similarity import SemanticSimilarity
from eval_framework.metrics.answer_relevancy import AnswerRelevancy
from eval_framework.metrics.faithfulness import Faithfulness
from eval_framework.report import print_report, save_json_report
from eval_framework.storage import init_db, save_run, detect_regression

METRIC_REGISTRY = {
    "exact_match": ExactMatch(),
    "semantic_similarity": SemanticSimilarity(),
    "answer_relevancy": AnswerRelevancy(),
    "faithfulness": Faithfulness(),
}


def load_test_cases(path: str) -> list[TestCase]:
    with open(path) as f:
        raw = json.load(f)
    return [TestCase(**item) for item in raw]


def main():
    parser = argparse.ArgumentParser(description="Run an LLM evaluation suite.")
    parser.add_argument("--dataset", required=True, help="Path to a JSON test case file")
    parser.add_argument(
        "--metrics",
        default="answer_relevancy",
        help=f"Comma-separated metric names. Available: {', '.join(METRIC_REGISTRY)}",
    )
    parser.add_argument("--label", default="run", help="Label for this run, used for regression tracking")
    args = parser.parse_args()

    init_db()
    test_cases = load_test_cases(args.dataset)
    selected = [name.strip() for name in args.metrics.split(",") if name.strip() in METRIC_REGISTRY]
    if not selected:
        print(f"No valid metrics selected. Available: {', '.join(METRIC_REGISTRY)}")
        return
    metrics = [METRIC_REGISTRY[name] for name in selected]

    runner = EvalRunner(metrics)
    results = runner.run(test_cases)

    print_report(results)
    report_path = save_json_report(results)
    print(f"Full JSON report saved to {report_path}")

    save_run(args.label, results)
    for metric in metrics:
        regression = detect_regression(args.label, metric.name)
        if regression:
            print(
                f"\nREGRESSION on '{regression['metric']}' vs run '{regression['previous_run']}': "
                f"{regression['previous_score']} -> {regression['current_score']} "
                f"(dropped {regression['drop']})"
            )


if __name__ == "__main__":
    main()
