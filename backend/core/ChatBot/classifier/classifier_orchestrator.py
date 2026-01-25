# classifier_orchestrator.py
from typing import Dict, Callable, List
from ..query_type import QueryType
from ..classifier import ClassificationDecider


class ClassificationOrchestrator:
    """
    Orchestrates rule-based scoring → decision → LLM fallback
    """

    def __init__(self, llm_fallback_fn: Callable[[str], QueryType]):
        self.decision_engine = ClassificationDecider()
        self.llm_fallback_fn = llm_fallback_fn
        self.scorers: List[Callable[[str], Dict[QueryType, int]]] = []

    def register_scorer(self, scorer: Callable[[str], Dict[QueryType, int]]):
        self.scorers.append(scorer)

    def classify(self, query: str) -> QueryType:
        scores: Dict[QueryType, int] = {}

        # Collect scores from all scorers
        for scorer in self.scorers:
            partial = scorer(query)
            for qtype, value in partial.items():
                scores[qtype] = scores.get(qtype, 0) + value

        # Decide using confidence rules
        decision = self.decision_engine.decide(scores)

        # Low confidence → LLM fallback
        if decision == QueryType.GENERAL:
            return self.llm_fallback_fn(query)

        return decision
