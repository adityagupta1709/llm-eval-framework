from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class TestCase:
    """One unit of evaluation: an input, the output produced by the system under
    test, and optional ground truth / retrieval context depending on which
    metrics you plan to run against it."""

    input: str
    actual_output: str
    expected_output: Optional[str] = None
    retrieval_context: Optional[List[str]] = None
    name: Optional[str] = None
