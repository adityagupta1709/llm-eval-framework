import json
from groq import Groq
from eval_framework.config import GROQ_API_KEY, JUDGE_MODEL

client = Groq(api_key=GROQ_API_KEY)

PAIRWISE_SYSTEM_PROMPT = """You are comparing two candidate responses to the same input.
Decide which one is better overall, or whether they're roughly equal. Consider correctness,
clarity, and completeness.

Respond with ONLY valid JSON, no other text, no markdown fences:
{"winner": "A", "reasoning": "<1-2 sentences>"}
or {"winner": "B", "reasoning": "<1-2 sentences>"}
or {"winner": "tie", "reasoning": "<1-2 sentences>"}
"""


def compare(input_text: str, output_a: str, output_b: str) -> dict:
    """Not a Metric subclass on purpose - pairwise comparison doesn't score one
    TestCase, it judges two candidate outputs against each other. Useful for
    A/B testing two prompt versions or two models on the same input, which is
    a genuinely different question than 'how good is this one output.'"""
    user_prompt = f"Input: {input_text}\n\nResponse A:\n{output_a}\n\nResponse B:\n{output_b}"
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        max_tokens=250,
        messages=[
            {"role": "system", "content": PAIRWISE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"winner": "tie", "reasoning": "Could not parse judge output.", "raw": raw}
