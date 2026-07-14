import json
from groq import Groq
from eval_framework.config import GROQ_API_KEY, JUDGE_MODEL

client = Groq(api_key=GROQ_API_KEY)

JUDGE_SYSTEM_PROMPT = """You are an impartial evaluator. You will be given evaluation
criteria and some content to evaluate against it. Reason step by step about how well the
content meets the criteria before assigning a score - this reduces the tendency to just
give a default middling score without real judgment.

Respond with ONLY valid JSON, no other text, no markdown fences:
{"reasoning": "<2-3 sentences of step by step reasoning>", "score": <float between 0.0 and 1.0>}
"""


def judge(criteria: str, content: str) -> dict:
    """Runs one LLM-as-judge call. Kept as a single shared function so every
    metric that needs a judge call goes through the same prompt discipline
    and JSON parsing/fallback behavior."""
    user_prompt = f"Evaluation criteria:\n{criteria}\n\nContent to evaluate:\n{content}"
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        max_tokens=400,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content.strip()
    try:
        parsed = json.loads(raw)
        parsed["score"] = max(0.0, min(1.0, float(parsed.get("score", 0.0))))
        return parsed
    except (json.JSONDecodeError, ValueError, TypeError):
        return {"reasoning": "Could not parse judge output.", "score": 0.0, "raw": raw}
