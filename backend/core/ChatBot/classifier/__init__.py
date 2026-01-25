import re
from typing import Optional, Dict, Any

from ..query_type import QueryType
from ..classifier import Classifier   # your new scorer-based classifier


class ClassifierMixin:
    """
    Backward-compatible adapter.

    RAGChatbot expects:
      - classify_query()
      - extract_entity_from_query()
      - expand_query()
      - is_greeting()

    Internally uses the NEW scorer-based Classifier.
    """

    def __init__(self, *args, **kwargs):
        self._smart_classifier = Classifier(
            logger=getattr(self, "logger", None),
            provider=getattr(self, "provider", None),
            client=getattr(self, "client", None),
            model=getattr(self, "model", None),
            verbose=getattr(self, "verbose", False),
        )

    # --------------------------------------------------
    # CORE CLASSIFICATION (USED BY RAGChatbot)
    # --------------------------------------------------

    def classify_query(self, query: str) -> QueryType:
        result = self._smart_classifier.classify(query)
        return result["query_type"]

    # --------------------------------------------------
    # GREETING
    # --------------------------------------------------

    def is_greeting(self, query: str) -> bool:
        return self._smart_classifier.is_greeting(query)

    # --------------------------------------------------
    # QUERY EXPANSION (LEGACY)
    # --------------------------------------------------

    def expand_query(self, query: str) -> str:
        return self._smart_classifier.rewrite_query(query)

    # --------------------------------------------------
    # ENTITY EXTRACTION (LEGACY CONTRACT)
    # --------------------------------------------------

    def extract_entity_from_query(
        self, query: str, query_type: QueryType
    ) -> Optional[Dict[str, Any]]:

        q = query.lower()

        if query_type == QueryType.ISSUE_SPECIFIC:
            m = re.search(r'issue\s*#?\s*(\d+)', q)
            return {"type": "issue", "number": int(m.group(1))} if m else None

        if query_type == QueryType.PR_SPECIFIC:
            m = re.search(r'(pr|pull request)\s*#?\s*(\d+)', q)
            return {"type": "pr", "number": int(m.group(2))} if m else None

        if query_type == QueryType.COMMIT_SPECIFIC:
            m = re.search(r'commit\s+([a-f0-9]{7,40})', q)
            return {"type": "commit", "sha": m.group(1))} if m else None

        return None
