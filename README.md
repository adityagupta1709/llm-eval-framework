# LLM Eval Framework

A standalone, zero-cost LLM evaluation framework, built from scratch to actually
understand the mechanics behind tools like RAGAS and DeepEval rather than just
using them as a black box.

**Author:** Aditya Gupta ([GitHub](https://github.com/adityagupta1709))

---

<img width="1050" height="746" alt="image" src="https://github.com/user-attachments/assets/172bf95e-a9ab-4a49-84ab-924861960f07" />


## Why this exists

Every LLM-powered application eventually hits the same wall: you tweak a prompt,
it looks fine on the three examples you tried by hand, and you ship it - with no
real way to know whether it silently got worse on everything else. Eyeballing
outputs doesn't scale, and traditional unit tests (exact string match) are
useless against probabilistic, open-ended generation.

This framework treats evaluation as infrastructure, not an afterthought: a
reusable way to score any LLM system's outputs, track whether quality is
improving or regressing over time, and catch the difference between "this
model judge likes it" and "a human would actually agree."

## What it can evaluate

This is framework-agnostic and subject-agnostic on purpose - it doesn't assume
anything about the system under test. Feed it any `(input, actual_output)`
pair, optionally with `expected_output` (ground truth) or `retrieval_context`
(for RAG systems), and it can score it.

## Architecture

```
   TestCase(s)
        |
        v
   EvalRunner  ---runs each metric against each test case--->  MetricResult(s)
        |                                                            |
        v                                                            v
  Report (console + JSON)                              SQLite run history
                                                                      |
                                                                      v
                                                          Regression detection
                                                       (compares this run's avg
                                                        score per metric against
                                                        the previous run)
```

Every metric implements one interface - `evaluate(test_case) -> MetricResult`
- so reference-based metrics, LLM-judge metrics, and RAG-specific metrics can
all be mixed in the same run and reported on consistently.

## The metrics

| Metric | Type | What it needs | What it catches |
|---|---|---|---|
| `ExactMatch` | Reference-based | `expected_output` | Wrong answer, verbatim |
| `SemanticSimilarity` | Reference-based (embeddings) | `expected_output` | Right idea, different wording vs. actually wrong |
| `GEval` | LLM-as-judge, custom rubric | Just a criteria string | Any quality you can describe in English - tone, safety, style |
| `AnswerRelevancy` | LLM-as-judge | Nothing extra | Fluent but off-topic answers |
| `Faithfulness` | LLM-as-judge, RAG-specific | `retrieval_context` | Hallucination - claims not backed by retrieved context |
| `compare()` (pairwise) | LLM-as-judge, head-to-head | Two candidate outputs | Which of two prompt/model versions is actually better |

### Why the judge reasons before scoring

Every LLM-as-judge metric goes through one shared `judge()` function
(`eval_framework/judge.py`) that forces the model to produce a short chain of
reasoning *before* the numeric score, not just a bare number. Asking for a bare
score tends to collapse toward a default middling value ("rubber stamping");
forcing reasoning first measurably improves how much the score actually reflects
the content, which is the same idea behind the G-Eval technique this framework's
`GEval` metric is named after.

### Why judge scores need calibration, not blind trust

`calibration/calibrate.py` runs the judge against a small hand-labeled sample
(`calibration/sample_labeled_set.json`) and reports how often the judge's
pass/fail agrees with a human-assigned score. This exists because LLM judges
are not ground truth - real-world agreement between LLM judges and human raters
is typically in the 85-92% range, not 100%. Treating a judge's score as
infallible without ever checking it against real judgment is a genuine failure
mode, and this script is the guardrail against it.

## Setup

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   ```
   Mac/Linux: `source venv/bin/activate` · Windows: `venv\Scripts\activate`

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Get a free Groq API key at https://console.groq.com/keys (no card required).

4. Set up your `.env`:
   ```
   cp .env.example .env
   ```
   (Windows: `copy .env.example .env`) - then paste your key after `GROQ_API_KEY=`.

## Using it

### Command line

**Run the demo end to end** (generates real answers from a tiny FAQ bot, then evaluates them):
```
python -m examples.run_demo
```

**Run the CLI against your own dataset:**
```
python main.py --dataset examples/demo_dataset.json --metrics exact_match,semantic_similarity --label baseline
```
Run it again after changing something, with a new `--label`, and the CLI will
flag it if any metric's average score dropped compared to the previous run -
this is the regression-tracking loop in action.

**Run the pytest-style suite** (for CI integration):
```
pytest examples/test_with_pytest.py -v
```

**Run judge calibration:**
```
python -m calibration.calibrate
```

### Web app

A browser dashboard over the same core framework - useful when you want to
paste in test cases, see pass/fail visually, and watch regression trends as a
chart instead of reading console output.

```
python web_main.py
```
Then open **http://127.0.0.1:8000**

Four tabs:
- **Run evaluation** - paste a JSON test case array (or click "Load demo dataset"), pick metrics, run, see per-case results with reasoning
- **History** - pick a metric, see a bar chart of average score across every labeled run, so a regression is visible at a glance instead of buried in console text
- **Pairwise compare** - paste an input and two candidate responses, see which one the judge prefers and why
- **Judge calibration** - run the judge against the hand-labeled sample directly from the browser and see per-item agreement

## Example: writing your own eval

```python
from eval_framework.test_case import TestCase
from eval_framework.metrics.g_eval import GEval

tc = TestCase(
    input="Write a product description for a water bottle.",
    actual_output="This sleek, insulated bottle keeps drinks cold for 24 hours...",
)

no_marketing_fluff = GEval(
    name="conciseness",
    criteria="Score how concise and free of generic marketing fluff the writing "
             "is, from 0 (full of cliches) to 1 (sharp and specific).",
    threshold=0.6,
)

result = no_marketing_fluff.evaluate(tc)
print(result.score, result.passed, result.reason)
```

This is the whole point of `GEval` - most of the interesting things worth
evaluating about LLM output don't have a single correct string to compare
against. Describing the quality you care about in plain English and letting a
judge reason about it is what makes evaluation possible for open-ended tasks.

## How this compares to RAGAS / DeepEval

RAGAS and DeepEval are the real, production-grade versions of this idea -
RAGAS focused on RAG-specific metrics without needing ground truth, DeepEval
broader with agentic evaluation and native pytest/CI integration. This project
deliberately reimplements a slice of the same core ideas (LLM-as-judge with
reasoning, faithfulness, regression tracking, pytest integration) from scratch,
because building the mechanism yourself is what makes it possible to actually
explain *why* an eval framework is built the way it is, rather than just
knowing which library to `pip install`.

## Known limitations

- The judge and the system-under-test can end up being the same model family
  (both via Groq) - a real production setup would ideally use a stronger,
  independent model as the judge to reduce self-bias.
- `SemanticSimilarity` uses Chroma's small bundled embedding model, which is
  fast and free but less accurate than larger dedicated embedding models.
- Regression detection compares only against the immediately preceding run,
  not a longer trend - a small extension, not a redesign.
- No web dashboard - reports are JSON + console output, viewable directly or
  easy to load into a notebook if you want charts.
