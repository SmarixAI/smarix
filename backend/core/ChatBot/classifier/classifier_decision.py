# classifier_decision.py
from typing import Dict
from ..query_type import QueryType


class ClassificationDecider:
    """
    Converts score map → final QueryType
    Applies confidence rules before LLM fallback
    """

    def __init__(self, min_confidence: int = 2):
        self.min_confidence = min_confidence

    def decide(self, scores: Dict[QueryType, int]) -> QueryType:
        """
        Decide final QueryType based on scores.
        """

        if not scores:
            return QueryType.GENERAL

        # Sort by highest score first
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        top_type, top_score = ranked[0]

        # 🟢 Strong confident winner
        if top_score >= self.min_confidence:
            return top_type

        # 🟡 Weak signals → GENERAL
        return QueryType.GENERAL
