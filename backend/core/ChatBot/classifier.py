import re
from typing import Dict, Any, Optional

from .query_type import QueryType
from .classifier.orchestrator import classify_with_scoring
from .classifier.confidence import compute_confidence


class Classifier:
    """
    Industry-grade classifier.

    Combines:
    - Deterministic scorer-based classification
    - Confidence estimation
    - LLM fallback
    - Greeting detection
    - Query rewrite
    - Entity extraction

    This is a STRICT superset of the old SmartClassifier.
    """

    def __init__(
        self,
        logger,
        provider: Optional[str] = None,
        client: Optional[Any] = None,
        model: Optional[str] = None,
        verbose: bool = False,
    ):
        self.logger = logger
        self.provider = provider
        self.client = client
        self.model = model
        self.verbose = verbose

    # ==================================================
    # 1️⃣ PRIMARY ENTRY POINT
    # ==================================================

    def classify(self, query: str) -> Dict[str, Any]:
        query = query.strip()

        if not query:
            return self._result(QueryType.GENERAL, 0.0)

        # 1️⃣ Greeting → hard stop
        if self.is_greeting(query):
            return self._result(QueryType.GREETING, 1.0)

        # 2️⃣ Deterministic scorer-based classification
        intent = classify_with_scoring(query)

        # 3️⃣ Confidence estimation
        confidence = compute_confidence(intent, query)

        # 4️⃣ Low-confidence → LLM fallback
        if confidence < 0.55:
            self.logger.info(
                f"CLASSIFIER | Low confidence ({confidence:.2f}), invoking LLM fallback"
            )
            intent = self.llm_classify_query(query)
            confidence = 0.70

        return self._result(intent, confidence)

    # ==================================================
    # 2️⃣ RESULT FORMATTER
    # ==================================================

    def _result(self, intent: QueryType, confidence: float) -> Dict[str, Any]:
        return {
            "query_type": intent,
            "confidence": round(confidence, 2),
        }

    # ==================================================
    # 3️⃣ GREETING DETECTION (UNCHANGED)
    # ==================================================

    GREETING_WORDS = {"hi", "hello", "hey", "howdy", "sup"}
    GREETING_PATTERNS = [
        r"^(hi+|hello+|hey+)[\s!?.]*$",
        r"^(what'?s up|sup)[\s!?.]*$",
        r"^good\s+(morning|afternoon|evening)[\s!?.]*$",
        r"^(help|start)[\s!?.]*$",
    ]

    def is_greeting(self, query: str) -> bool:
        q = query.lower().strip()
        if q in self.GREETING_WORDS:
            return True
        return any(re.match(p, q) for p in self.GREETING_PATTERNS)

    # ==================================================
    # 4️⃣ LLM FALLBACK CLASSIFICATION
    # ==================================================

    def llm_classify_query(self, query: str) -> QueryType:
        if not self.provider or not self.client:
            return QueryType.GENERAL

        prompt = f"""
Classify the following user query into ONE category.

QUERY:
"{query}"

CATEGORIES:
- file_lookup
- issue_specific
- pr_specific
- commit_specific
- repository_metrics
- tech_stack
- code_structure
- flow_architecture
- impact_analysis
- traceability
- question_generation
- pr_issue_tutorial
- pr_issue_coding_question
- random_pr_generator
- troubleshooting
- conceptual
- general

Respond with ONLY the category name.
"""

        try:
            if self.provider == "openai":
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=20,
                )
                category = resp.choices[0].message.content.strip().lower()

            elif self.provider == "anthropic":
                resp = self.client.messages.create(
                    model=self.model,
                    max_tokens=20,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}],
                )
                category = resp.content[0].text.strip().lower()
            else:
                return QueryType.GENERAL

            return QueryType.from_string(category)

        except Exception as e:
            self.logger.error(f"LLM CLASSIFIER FAILED: {e}")
            return QueryType.GENERAL

    # ==================================================
    # 5️⃣ QUERY REWRITE (PRESERVED)
    # ==================================================

    def rewrite_query(self, query: str) -> str:
        """
        Lightweight rewrite for better retrieval.
        Preserved exactly from SmartClassifier.
        """
        if len(query.split()) < 3:
            return query

        if not self.provider or not self.client:
            return query

        prompt = f"""
Rewrite the query to be clearer for searching a codebase.
Keep meaning identical.

Original: "{query}"
Rewritten:
"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=60,
            )
            rewritten = resp.choices[0].message.content.strip()
            return rewritten if rewritten else query
        except Exception:
            return query

    # ==================================================
    # 6️⃣ ENTITY EXTRACTION (UNCHANGED)
    # ==================================================

    def extract_entity(
        self, query: str, intent: QueryType
    ) -> Optional[Dict[str, Any]]:
        q = query.lower()

        if intent == QueryType.ISSUE_SPECIFIC:
            m = re.search(r"issue\s*#?\s*(\d+)", q)
            return {"type": "issue", "number": int(m.group(1))} if m else None

        if intent == QueryType.PR_SPECIFIC:
            m = re.search(r"(pr|pull request)\s*#?\s*(\d+)", q)
            return {"type": "pr", "number": int(m.group(2))} if m else None

        if intent == QueryType.COMMIT_SPECIFIC:
            m = re.search(r"commit\s+([a-f0-9]{7,40})", q)
            return {"type": "commit", "sha": m.group(1)} if m else None

        return None
