# conceptual_scorer.py
from typing import Dict
from ..query_type import QueryType

CONCEPTUAL_PHRASES = [
    'what is',
    'what does',
    'what are',
    'explain',
    'describe',
    'define'
]

HOW_TO_PHRASES = [
    'how do i',
    'how to',
    'how can i',
    'steps to',
    'guide to',
    'tutorial'
]


def conceptual_scorer(query: str) -> Dict[QueryType, int]:
    """
    LOW priority scorer.
    Never allowed to override file / code / entity intents.
    """
    q = query.lower()
    scores = {}

    if any(p in q for p in CONCEPTUAL_PHRASES):
        scores[QueryType.CONCEPTUAL] = 1  # deliberately weak

    if any(p in q for p in HOW_TO_PHRASES):
        scores[QueryType.HOW_TO] = 1  # deliberately weak

    return scores
