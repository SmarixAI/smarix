"""
Chronological-specific handling module for the RAG Chatbot.
Handles all chronological queries (first/last issue/PR) and operations.
"""

import re
from typing import Dict, Any, Optional, Iterator
from ..query_type import QueryType
from utils.metadata_normalizer import MetadataNormalizer


class ChronologicalHandler:
    """Handler for all chronological query operations."""

    def __init__(self, chatbot):
        self.chatbot = chatbot

    def handle_chronological(
        self,
        chrono_query: Dict[str, Any],
        query: str,
        expanded_query: str,
        active_session_id: str,
        role: Optional[str] = None,
        schema_name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Handle chronological query (first/last issue/PR).
        Returns response dict if found, None otherwise.
        """
        if not chrono_query:
            return None

        self.chatbot.logger.info(
            f"CHRONOLOGICAL QUERY | Type: {chrono_query['type']}, Order: {chrono_query['order']}"
        )

        if self.chatbot.verbose:
            print(f"Chronological query detected: {chrono_query}")

        query_embedding = self.chatbot.get_query_embedding(expanded_query)
        chrono_result = self.chatbot.find_chronological_entity(
            chrono_query["type"], chrono_query["order"], query_embedding
        )

        if not chrono_result:
            return None

        entity = {"type": chrono_result["type"], "number": chrono_result["number"]}
        github_results = chrono_result["results"]

        self.chatbot.logger.info(
            f"CHRONOLOGICAL RESULT | Found {chrono_query['type']} #{chrono_result['number']}"
        )
        self.chatbot.logger.info(f"RETRIEVAL | Retrieved {len(github_results)} chunks")

        for i, result in enumerate(github_results[:5], 1):
            meta_norm = MetadataNormalizer(result.get("metadata", {}), result)
            self.chatbot.logger.info(
                f"CHUNK {i} | File: {meta_norm.get_file_path('N/A')}, "
                f"Score: {result.get('score', 0):.4f}, Type: {meta_norm.get_chunk_type('N/A')}"
            )

        query_type = (
            QueryType.ISSUE_SPECIFIC
            if chrono_result["type"] == "issue"
            else QueryType.PR_SPECIFIC
        )

        if self.chatbot.verbose:
            print(
                f"Found {chrono_query['order']} {chrono_query['type']}: #{chrono_result['number']}"
            )

        context = self.chatbot.build_context_from_chunks(github_results, query_type)

        gmail_results = self.chatbot.retrieve_gmail_correlated(
            github_results, query_embedding, []
        )

        if gmail_results:
            self.chatbot.logger.info(
                f"EMAIL RETRIEVAL | Found {len(gmail_results)} correlated emails"
            )

        email_context = (
            self.chatbot.build_email_context(gmail_results) if gmail_results else ""
        )

        system_prompt = self.chatbot.get_dynamic_system_prompt(
            query_type, expanded_query, role=role
        )
        user_prompt = self.chatbot.build_user_prompt(
            expanded_query, context, email_context, query_type, entity, None
        )

        if self.chatbot.verbose:
            print("Generating response...")

        self.chatbot.logger.info("LLM GENERATION | Started")
        answer = self.chatbot.call_llm(system_prompt, user_prompt)
        self.chatbot.logger.info(
            f"LLM GENERATION | Completed, Length: {len(answer)} chars"
        )

        self.chatbot.logger.info("VERIFICATION | Starting response verification")
        refined_answer = self.chatbot.verify_and_refine_response(
            answer, query, query_type
        )

        sources = []
        for i, result in enumerate(github_results[:5], 1):
            meta_norm = MetadataNormalizer(result.get("metadata", {}), result)
            sources.append(
                {
                    "rank": i,
                    "file": meta_norm.get_file_path("unknown"),
                    "type": meta_norm.get_chunk_type("unknown"),
                    "score": result.get("score", 0.0),
                    "chunk_id": result.get("chunk_id", "")
                    or meta_norm.get("chunk_id", ""),
                }
            )

        emails = []
        for email in gmail_results:
            metadata = email.get("metadata", {})
            emails.append(
                {
                    "subject": metadata.get("subject", ""),
                    "from": metadata.get("from", ""),
                    "date": metadata.get("date", ""),
                    "relevance": email.get("relevance_score", 0),
                }
            )

        self.chatbot.history.append({"role": "user", "content": query})
        self.chatbot.history.append({"role": "assistant", "content": refined_answer})

        context_quality = (
            min(github_results[0].get("score", 0), 1.0) if github_results else 0.0
        )

        self.chatbot.logger.info(
            f"RESPONSE COMPLETE | Quality: {context_quality:.2f}, "
            f"Sources: {len(sources)}, Emails: {len(emails)}"
        )
        self.chatbot.logger.info("=" * 80)

        result = {
            "answer": refined_answer,
            "sources": sources,
            "chunks_retrieved": len(github_results),
            "query_type": query_type,
            "context_quality": context_quality,
            "emails": emails,
            "has_diagram": bool(re.search(r"```mermaid", refined_answer or "")),
            "related_knowledge": None,
            "is_metrics_query": False,
            "chronological_entity": f"{chrono_query['order']} {chrono_query['type']} #{chrono_result['number']}",
        }

        self._update_caches(query, result, active_session_id)

        return result

    # ------------------------------------------------------------------ #

    def handle_chronological_stream(
        self,
        chrono_query: Dict[str, Any],
        query: str,
        expanded_query: str,
        active_session_id: str,
        role: Optional[str] = None,
        schema_name: Optional[str] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Handle chronological query with streaming response.
        Yields status, token, and done chunks.
        """
        if not chrono_query:
            return

        self.chatbot.logger.info(
            f"CHRONOLOGICAL STREAM | Type: {chrono_query['type']}, Order: {chrono_query['order']}"
        )

        if self.chatbot.verbose:
            print(f"Chronological query detected: {chrono_query}")

        yield {'type': 'status', 'content': f'Finding {chrono_query["order"]} {chrono_query["type"]}...'}

        query_embedding = self.chatbot.get_query_embedding(expanded_query)
        chrono_result = self.chatbot.find_chronological_entity(
            chrono_query['type'],
            chrono_query['order'],
            query_embedding
        )

        # ── no result guard ──────────────────────────────────────────────
        if not chrono_result:
            no_result_msg = (
                f"No {chrono_query['type']} found matching your query. "
                f"The repository may not have any {chrono_query['type']}s indexed, "
                f"or the '{chrono_query['order']}' {chrono_query['type']} could not be determined."
            )
            yield {'type': 'token', 'content': no_result_msg}
            yield {
                'type': 'done',
                'content': no_result_msg,
                'metadata': {
                    'sources': [], 'chunks_retrieved': 0,
                    'query_type': QueryType.ISSUE_SPECIFIC if chrono_query['type'] == 'issue' else QueryType.PR_SPECIFIC,
                    'context_quality': 0.0, 'emails': [], 'has_diagram': False,
                    'related_knowledge': None, 'is_metrics_query': False,
                    'chronological_entity': None
                }
            }
            return

        entity = {'type': chrono_result['type'], 'number': chrono_result['number']}
        github_results = chrono_result['results']

        self.chatbot.logger.info(
            f"CHRONOLOGICAL RESULT | Found {chrono_query['type']} #{chrono_result['number']}"
        )

        query_type = QueryType.ISSUE_SPECIFIC if chrono_result['type'] == 'issue' else QueryType.PR_SPECIFIC

        yield {'type': 'status', 'content': f'Found {chrono_query["type"]} #{chrono_result["number"]}, retrieving context...'}

        context = self.chatbot.build_context_from_chunks(github_results, query_type)

        gmail_results = self.chatbot.retrieve_gmail_correlated(
            github_results, query_embedding, []
        )

        email_context = self.chatbot.build_email_context(gmail_results) if gmail_results else ""

        if gmail_results:
            yield {'type': 'status', 'content': f'Found {len(gmail_results)} related emails'}

        system_prompt = self.chatbot.get_dynamic_system_prompt(query_type, expanded_query, role=role)
        user_prompt = self.chatbot.build_user_prompt(
            expanded_query, context, email_context, query_type, entity, None
        )

        yield {'type': 'status', 'content': 'Generating response...'}

        full_answer = ""
        buffer = ""
        for chunk in self.chatbot.call_llm_stream(system_prompt, user_prompt):
            full_answer += chunk
            buffer += chunk
            if '\n' in buffer or len(buffer) > 150:
                yield {'type': 'token', 'content': buffer}
                buffer = ""

        if buffer:
            yield {'type': 'token', 'content': buffer}

        self.chatbot.logger.info(
            f"LLM GENERATION | Completed streaming, Length: {len(full_answer)} chars"
        )

        # Skip verify_and_refine in stream mode to preserve low latency
        refined_answer = full_answer

        sources = []
        for i, result in enumerate(github_results[:5], 1):
            meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
            sources.append({
                'rank': i,
                'file': meta_norm.get_file_path('unknown'),
                'type': meta_norm.get_chunk_type('unknown'),
                'score': result.get('score', 0.0),
                'chunk_id': result.get('chunk_id', '') or meta_norm.get('chunk_id', '')
            })

        emails = []
        for email in gmail_results:
            metadata = email.get('metadata', {})
            emails.append({
                'subject': metadata.get('subject', ''),
                'from': metadata.get('from', ''),
                'date': metadata.get('date', ''),
                'relevance': email.get('relevance_score', 0)
            })

        self.chatbot.history.append({'role': 'user', 'content': query})
        self.chatbot.history.append({'role': 'assistant', 'content': refined_answer})

        # Fix: github_results is a list, index with  not .get()
        context_quality = min(github_results.get('score', 0), 1.0) if github_results else 0.0

        self.chatbot.logger.info(f"RESPONSE COMPLETE | Quality: {context_quality:.2f}")
        self.chatbot.logger.info("=" * 80)

        yield {
            'type': 'done',
            'content': refined_answer,
            'metadata': {
                'sources': sources,
                'chunks_retrieved': len(github_results),
                'query_type': query_type,
                'context_quality': context_quality,
                'emails': emails,
                'has_diagram': bool(re.search(r'```mermaid', refined_answer or '')),
                'related_knowledge': None,
                'is_metrics_query': False,
                'chronological_entity': f"{chrono_query['order']} {chrono_query['type']} #{chrono_result['number']}"
            }
        }

    # ------------------------------------------------------------------ #

    def _update_caches(self, query: str, result: Dict[str, Any], active_session_id: str):
        """Update semantic and response caches."""
        self.chatbot.cache_handler.update_caches(query, result, active_session_id)