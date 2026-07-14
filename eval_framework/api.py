import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from eval_framework.test_case import TestCase
from eval_framework.runner import EvalRunner
from eval_framework.metrics.exact_match import ExactMatch
from eval_framework.metrics.semantic_similarity import SemanticSimilarity
from eval_framework.metrics.answer_relevancy import AnswerRelevancy
from eval_framework.metrics.faithfulness import Faithfulness
from eval_framework.metrics.g_eval import GEval
from eval_framework.metrics.pairwise import compare as pairwise_compare
from eval_framework.storage import init_db, save_run, detect_regression, get_metric_history

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DEMO_DATASET_PATH = BASE_DIR / "examples" / "demo_dataset.json"
CALIBRATION_SAMPLE_PATH = BASE_DIR / "calibration" / "sample_labeled_set.json"

app = FastAPI(title="LLM Eval Framework")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

init_db()

METRIC_REGISTRY = {
    "exact_match": ExactMatch(),
    "semantic_similarity": SemanticSimilarity(),
    "answer_relevancy": AnswerRelevancy(),
    "faithfulness": Faithfulness(),
}


class TestCaseIn(BaseModel):
    name: Optional[str] = None
    input: str
    actual_output: str
    expected_output: Optional[str] = None
    retrieval_context: Optional[list[str]] = None


class RunRequest(BaseModel):
    dataset: list[TestCaseIn]
    metrics: list[str]
    label: str = "run"


class PairwiseRequest(BaseModel):
    input_text: str
    output_a: str
    output_b: str


@app.get("/")
def root():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/metrics")
def list_metrics():
    return {"metrics": list(METRIC_REGISTRY.keys())}


@app.get("/api/demo-dataset")
def demo_dataset():
    with open(DEMO_DATASET_PATH) as f:
        return json.load(f)


@app.post("/api/run")
def run_eval(req: RunRequest):
    metrics = [METRIC_REGISTRY[m] for m in req.metrics if m in METRIC_REGISTRY]
    if not metrics:
        return {"error": f"No valid metrics selected. Available: {', '.join(METRIC_REGISTRY)}"}

    test_cases = [TestCase(**tc.model_dump()) for tc in req.dataset]
    runner = EvalRunner(metrics)
    results = runner.run(test_cases)
    save_run(req.label, results)

    regressions = []
    for metric in metrics:
        regression = detect_regression(req.label, metric.name)
        if regression:
            regressions.append(regression)

    return {
        "cases": [
            {
                "name": case.test_case_name,
                "all_passed": case.all_passed,
                "metrics": [
                    {
                        "name": r.metric_name, "score": r.score, "passed": r.passed,
                        "reason": r.reason, "applicable": r.applicable,
                    }
                    for r in case.results
                ],
            }
            for case in results
        ],
        "regressions": regressions,
    }


@app.get("/api/history/{metric_name}")
def history(metric_name: str):
    return get_metric_history(metric_name)


@app.post("/api/pairwise")
def pairwise(req: PairwiseRequest):
    return pairwise_compare(req.input_text, req.output_a, req.output_b)


@app.post("/api/calibrate")
def calibrate():
    with open(CALIBRATION_SAMPLE_PATH) as f:
        labeled_cases = json.load(f)

    metric = GEval(
        name="calibration_check",
        criteria="Score how relevant and complete the answer is with respect to the question, from 0 to 1.",
        threshold=0.7,
    )

    results = []
    agreements = 0
    for item in labeled_cases:
        tc = TestCase(input=item["input"], actual_output=item["actual_output"])
        result = metric.evaluate(tc)
        human_passed = item["human_score"] >= 0.7
        agree = result.passed == human_passed
        agreements += int(agree)
        results.append({
            "input": item["input"],
            "judge_score": result.score,
            "human_score": item["human_score"],
            "agree": agree,
        })

    rate = agreements / len(labeled_cases) if labeled_cases else 0.0
    return {"agreement_rate": rate, "agreements": agreements, "total": len(labeled_cases), "results": results}
