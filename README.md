# LLM Eval Framework

A standalone LLM evaluation tool I built from scratch to actually
understand how tools like RAGAS and DeepEval work under the hood, rather than
just using one as a black box. LLM-as-judge scoring with reasoning-before-score,
RAG faithfulness checks, regression tracking across runs, and a script that
checks whether the judge actually agrees with a human. CLI and a web
dashboard, $0 to run. Setup is in [Setup](#setup) below.

**Author:** Aditya Gupta ([GitHub](https://github.com/adityagupta1709))

<img width="1050" height="746" alt="image" src="https://github.com/user-attachments/assets/5b27f1ea-4a3b-4297-80e8-f4dd66a02670" />


---

## Why I built this

Every LLM app I've touched hits the same problem: you tweak a prompt, it
looks fine on the couple of examples you tried by hand, and you ship it with
no real way to know if it silently got worse on everything else. I wanted to
understand the actual mechanics behind LLM-as-judge evaluation and regression
tracking well enough to explain them, not just know which library to
`pip install`. This reimplements a slice of what RAGAS/DeepEval do, on
purpose, as a learning exercise that turned into a genuinely usable tool.

## What it does

- Scores any `(input, actual_output)` pair - doesn't assume anything about
  the system under test
- Six metrics spanning reference-based, LLM-as-judge, and RAG-specific checks
  (full list below)
- Tracks every run in SQLite and flags it when a metric's average score drops
  compared to the previous run
- Includes a judge calibration script - checks the LLM judge's scores against
  a small hand-labeled sample, because judge scores are not ground truth
- CLI, pytest integration, and a web dashboard, all calling the same core code

## The metrics

| Metric | Type | Needs | Catches |
|---|---|---|---|
| `ExactMatch` | Reference-based | `expected_output` | Wrong answer, verbatim |
| `SemanticSimilarity` | Reference-based (embeddings) | `expected_output` | Right idea, different wording - though it can also over-penalize a terse ground truth against a verbose answer, worth tuning the threshold per dataset |
| `GEval` | LLM-as-judge, custom rubric | A criteria string | Any quality describable in plain English - tone, safety, style |
| `AnswerRelevancy` | LLM-as-judge | Nothing extra | Fluent but off-topic answers |
| `Faithfulness` | LLM-as-judge, RAG-specific | `retrieval_context` | Hallucination - claims not backed by retrieved context |
| `compare()` (pairwise) | LLM-as-judge, head-to-head | Two outputs | Which of two prompt/model versions is actually better |

A metric that isn't applicable to a given test case (say, `faithfulness` on a
case with no `retrieval_context`) is marked N/A, not failed - it doesn't count
against that case's pass/fail. I got this wrong in an early version (N/A was
counted as a failure) and fixed it after actually running real test cases
through it and noticing the results didn't make sense.

## Why the judge reasons before scoring

Every LLM-as-judge metric shares one `judge()` function that forces a short
chain of reasoning before the numeric score, instead of asking for a bare
number. Bare-number requests tend to collapse toward a default middling
value; reasoning first measurably changes how much the score reflects the
actual content. This is the same idea behind the G-Eval technique.

## Why judge scores get calibrated, not trusted blindly

`calibration/calibrate.py` runs the judge against a small hand-labeled sample
and reports how often its pass/fail agrees with the human-assigned score.
Published agreement between LLM judges and human raters is typically 85-92%,
not 100% - so a judge that's never been checked against real human judgment
is a real failure mode, not a hypothetical one.

## Architecture

```
   TestCase(s)
        |
        v
   EvalRunner ---runs each metric---> MetricResult(s)
        |                                   |
        v                                   v
  Report (console + JSON)          SQLite run history
                                            |
                                            v
                                  Regression detection
                              (this run's avg score per
                               metric vs. the previous run)
```

## Tech stack

Groq (free tier, both for the judge and the demo bot), ChromaDB's bundled
local embedding model, SQLite, FastAPI + vanilla JS for the web dashboard,
pytest for CI-style usage. $0 to run.

## Setup

1. `python -m venv venv` then activate it
2. `pip install -r requirements.txt`
3. Free key at https://console.groq.com/keys
4. `cp .env.example .env`, paste the key in

## Using it

- **Demo, end to end:** `python -m examples.run_demo`
- **CLI:** `python main.py --dataset examples/demo_dataset.json --metrics exact_match,semantic_similarity --label baseline`
- **Web dashboard:** `python web_main.py`, open http://127.0.0.1:8000
- **pytest:** `pytest examples/test_with_pytest.py -v`
- **Calibration:** `python -m calibration.calibrate`

## Honest limitations

- The judge and the system-under-test are often the same model family (both
  via Groq) - a stronger setup would use an independent judge model to reduce
  self-bias
- `SemanticSimilarity`'s default threshold assumes similar-length expected vs.
  actual output, and needs tuning per dataset when that's not true
- Regression detection compares only against the immediately preceding run,
  not a longer trend
- No dashboard persistence beyond SQLite - reports are JSON + console/web,
  not a hosted service
