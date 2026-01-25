# orchestrator.py

from typing import Dict
from collections import defaultdict

from ..query_type import QueryType

from .file_intent_scorer import score_file_intent
from .conceptual_scorer import score_conceptual_intent
from .classifier_decision import ClassificationDecider


# Register scorers explicitly (order does NOT matter)
SCORERS = [
    score_file_intent,
    score_conceptual_intent,
]


def classify_with_scoring(query: str) -> QueryType:
    """
    Industry-grade hybrid classifier

    Flow:
    1. Multiple independent scorers
    2. Aggregate weighted signals
    3. Deterministic decision
    4. Safe fallback
    """

    final_scores: Dict[QueryType, int] = defaultdict(int)

    # 1️⃣ Collect scores
    for scorer in SCORERS:
        scores = scorer(query)
        for intent, weight in scores.items():
            final_scores[intent] += weight

    # 2️⃣ Decide
    decider = ClassificationDecider(min_confidence=2)
    return decider.decide(final_scores)
