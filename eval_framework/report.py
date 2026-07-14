import json
from eval_framework.config import REPORTS_DIR


def print_report(case_results: list):
    print("\n=== Evaluation report ===")
    for case in case_results:
        status = "PASS" if case.all_passed else "FAIL"
        print(f"\n[{status}] {case.test_case_name}")
        for r in case.results:
            if not r.applicable:
                mark = "-  "
            else:
                mark = "OK " if r.passed else "X  "
            reason = f" - {r.reason}" if r.reason else ""
            print(f"   {mark}{r.metric_name}: {r.score}{reason}")

    total = len(case_results)
    passed = sum(1 for c in case_results if c.all_passed)
    print(f"\n{passed}/{total} test cases passed\n")


def save_json_report(case_results: list, filename: str = "report.json") -> str:
    data = []
    for case in case_results:
        data.append(
            {
                "test_case": case.test_case_name,
                "all_passed": case.all_passed,
                "metrics": [
                    {
                        "name": r.metric_name, "score": r.score, "passed": r.passed,
                        "reason": r.reason, "applicable": r.applicable,
                    }
                    for r in case.results
                ],
            }
        )
    path = REPORTS_DIR / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=float)
    return str(path)
