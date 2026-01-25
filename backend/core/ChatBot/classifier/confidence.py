# confidence.py
from typing import Dict
from ..query_type import QueryType

CONFIDENCE_THRESHOLD = 5  # tune this

def is_low_confidence(scores: Dict[QueryType, int]) -> bool:
    if not scores:
        return True

    sorted_scores = sorted(scores.values(), reverse=True)

    # If top intent is weak
    if sorted_scores[0] < CONFIDENCE_THRESHOLD:
        return True

    # If top two intents are too close → ambiguity
    if len(sorted_scores) > 1 and (sorted_scores[0] - sorted_scores[1]) <= 1:
        return True

    return False
