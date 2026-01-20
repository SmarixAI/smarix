"""
Multi-query handling module for the RAG Chatbot.
Handles intent-aware splitting of queries into sub-queries and merging responses.
"""

import re
from typing import List, Dict, Any


class MultiQueryHandler:
    """Handler for all multi-query operations."""

    def __init__(self, chatbot):
        self.chatbot = chatbot

    # -------------------------------
    # Intent-aware multi-query logic
    # -------------------------------

    def split_into_subqueries(self, query: str) -> List[str]:
        """
        Split query into sub-queries ONLY when it has multiple independent intents.
        Prefer intent-based splitting over punctuation-based splitting.
        """

        query_clean = query.strip()
        query_lower = query_clean.lower()

        # 1️⃣ Detect intent overlap first (MOST IMPORTANT)
        if self._has_multiple_pr_intents(query_lower):
            subqueries = self._split_by_pr_intent(query_clean)
            if len(subqueries) > 1:
                self._log_split(query_clean, subqueries, reason="intent_overlap")
                return subqueries

        # 2️⃣ Fallback: sentence-based split (safe + conservative)
        if len(query_clean) >= 40:
            parts = re.split(
                r'\?\s+|[.]\s+(?=(?:and|also|then|plus|what|how|where|when|why|tell)\b)',
                query_clean,
                flags=re.IGNORECASE
            )
            subqueries = [p.strip() for p in parts if p.strip() and len(p.strip()) > 10]

            if 2 <= len(subqueries) <= 3:
                self._log_split(query_clean, subqueries, reason="sentence_split")
                return subqueries

        # 3️⃣ Default: single query
        return [query_clean]

    # -------------------------------
    # Intent detection helpers
    # -------------------------------

    def _has_multiple_pr_intents(self, query_lower: str) -> bool:
        """
        Detect whether query contains multiple PR-related intents.
        """
        intent_groups = {
            "status": ["status", "merged", "open", "closed"],
            "files": ["file", "files", "changed files"],
            "changes": ["change", "changes", "diff"],
            "author": ["who", "author", "created"],
            "motivation": ["why", "reason"]
        }

        detected = [
            name for name, keywords in intent_groups.items()
            if any(k in query_lower for k in keywords)
        ]

        return len(detected) >= 2

    def _split_by_pr_intent(self, query: str) -> List[str]:
        """
        Convert a multi-intent PR query into focused sub-queries.
        """
        ql = query.lower()
        subs = []

        if any(k in ql for k in ["status", "merged", "open", "closed"]):
            subs.append(f"What is the status of {query}")

        if any(k in ql for k in ["file", "files", "changed files"]):
            subs.append(f"What files changed in {query}")

        if any(k in ql for k in ["change", "changes", "diff"]):
            subs.append(f"What changed in {query}")

        if any(k in ql for k in ["who", "author", "created"]):
            subs.append(f"Who created {query}")

        if any(k in ql for k in ["why", "reason"]):
            subs.append(f"Why was {query} created")

        # Limit to 3 to prevent explosion
        return subs[:3] if subs else [query]

    # -------------------------------
    # Execution & merging
    # -------------------------------

    def handle_multi_query(
        self,
        subqueries: List[str],
        original_query: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process sub-queries and merge responses into a single answer.
        """

        self.chatbot.logger.info(
            f"MULTI-QUERY | {len(subqueries)} sub-queries for: '{original_query[:60]}...'"
        )

        answers = []
        for i, sq in enumerate(subqueries, 1):
            self.chatbot.logger.info(
                f"MULTI-QUERY | Sub-query {i}/{len(subqueries)}: '{sq[:60]}...'"
            )

            result = self.chatbot.chat(
                sq,
                filters={"is_subquery": True},
                session_id=session_id
            )
            answers.append(result)

        merged = self.chatbot.response_handler.merge_multi_answers(
            answers, original_query
        )

        # Save merged response
        try:
            self.chatbot.conversation_store.add_message(
                session_id, "user", original_query, tokens_used=0
            )
            self.chatbot.conversation_store.add_message(
                session_id, "assistant", merged["answer"], tokens_used=0
            )
        except Exception as e:
            self.chatbot.logger.error(
                f"CONVERSATION_STORE | Failed to save multi-query response: {e}"
            )

        return merged

    # -------------------------------
    # Logging helpers
    # -------------------------------

    def _log_split(self, original: str, subqueries: List[str], reason: str):
        self.chatbot.logger.info(
            f"MULTI-QUERY SPLIT | reason={reason} | parts={len(subqueries)}"
        )
        for i, sq in enumerate(subqueries, 1):
            self.chatbot.logger.info(f"  Sub-query {i}: {sq}")
