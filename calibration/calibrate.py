"""
Judge calibration: checks whether the LLM judge's scores actually agree with
human judgment on a small labeled sample. This matters because an LLM judge
is not ground truth - published agreement rates between LLM judges and human
raters are typically around 85-92%, not 100%. Treating judge scores as
infallible without ever checking them against real human judgment is a real
failure mode this script is meant to catch.
"""
import json
from pathlib import Path
from eval_framework.test_case import TestCase
from eval_framework.metrics.g_eval import GEval

SAMPLE_PATH = Path(__file__).parent / "sample_labeled_set.json"


def calibrate(labeled_path: str, criteria: str, threshold: float = 0.7) -> float:
    with open(labeled_path) as f:
        labeled_cases = json.load(f)

    metric = GEval(name="calibration_check", criteria=criteria, threshold=threshold)
    agreements = 0

    for item in labeled_cases:
        tc = TestCase(input=item["input"], actual_output=item["actual_output"])
        result = metric.evaluate(tc)
        human_passed = item["human_score"] >= threshold
        agree = result.passed == human_passed
        agreements += int(agree)

        mark = "AGREE   " if agree else "DISAGREE"
        preview = item["input"][:50]
        print(f"{mark}  judge={result.score:.2f}  human={item['human_score']:.2f}  - {preview}")

    rate = agreements / len(labeled_cases) if labeled_cases else 0.0
    print(f"\nJudge-human agreement: {rate:.1%} ({agreements}/{len(labeled_cases)})")
    if rate < 0.8:
        print("This is below the ~85-92% agreement typically reported for LLM judges - "
              "the rubric criteria may need to be more specific, or the judge model may "
              "need to be swapped for a stronger one.")
    return rate


if __name__ == "__main__":
    calibrate(
        str(SAMPLE_PATH),
        criteria="Score how relevant and complete the answer is with respect to the "
                 "question, from 0 to 1.",
    )
