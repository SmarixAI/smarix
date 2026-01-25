# classifier_scoring.py
import re
from collections import defaultdict
from typing import Dict
from ..query_type import QueryType


class QueryScorer:
    """
    Pure scoring-based classifier.
    Does NOT make final decisions.
    Only assigns confidence scores to QueryTypes.
    """

    def __init__(self):
        self.file_evidence_patterns = [
            r'\.(py|js|ts|dart|java|go|rs|cpp|c|h|hpp|md|json|yaml|yml)',
            r'[\w\-_/\\]+\.(py|js|ts|dart|java|go|rs|cpp|c|h|hpp)',
            r'[\w\-_/\\]+/[\w\-_/\\]+',
        ]

        self.class_name_pattern = (
            r'\b[A-Z][a-zA-Z0-9]+'
            r'(Controller|Service|Manager|Repository|Bloc|ViewModel)\b'
        )

        self.snake_case_pattern = r'\b[a-z][a-z0-9_]{2,}\b'

    def score(self, query: str) -> Dict[QueryType, int]:
        """
        Returns a score map for all possible QueryTypes
        """
        scores = defaultdict(int)
        query_lower = query.lower().strip()

        # ----------------------------------
        # FILE_LOOKUP signals
        # ----------------------------------

        if any(re.search(p, query_lower) for p in self.file_evidence_patterns):
            scores[QueryType.FILE_LOOKUP] += 3

        if re.search(self.class_name_pattern, query):
            scores[QueryType.FILE_LOOKUP] += 2

        if 'file' in query_lower and re.search(self.snake_case_pattern, query_lower):
            scores[QueryType.FILE_LOOKUP] += 2

        if re.search(r'\bfile\b', query_lower):
            scores[QueryType.FILE_LOOKUP] += 1

        # ----------------------------------
        # CONCEPTUAL signals (LOW weight)
        # ----------------------------------

        if any(k in query_lower for k in ['what is', 'what does', 'explain', 'describe', 'define']):
            scores[QueryType.CONCEPTUAL] += 1

        # ----------------------------------
        # HOW_TO signals
        # ----------------------------------

        if any(k in query_lower for k in ['how do i', 'how to', 'steps to', 'guide to']):
            scores[QueryType.HOW_TO] += 2

        # ----------------------------------
        # TROUBLESHOOTING signals
        # ----------------------------------

        if any(k in query_lower for k in ['error', 'bug', 'fix', 'not working', 'issue with']):
            scores[QueryType.TROUBLESHOOTING] += 2

        return dict(scores)
