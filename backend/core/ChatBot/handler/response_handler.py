"""
Response handling module for the RAG Chatbot.
Handles response packaging, formatting, and multi-query merging.
"""

import re
from typing import Dict, Any, List, Optional
from ..query_type import QueryType

PR_INTENT_SYSTEM_PROMPTS = {

    "status": """
You are answering a GitHub Pull Request STATUS question.

STRICT RULES:
- ONLY return the PR status information.
- Do NOT describe files, code, diffs, or implementation.
- Do NOT add overview, summary, or explanation sections.
- Be concise and factual.

FORMAT (MUST FOLLOW EXACTLY):

PR #<number> Status:
- State: <Open | Closed | Merged>
- Created: <date>
- Merged: <date or N/A>
""",

    "summary": """
You are answering a HIGH-LEVEL SUMMARY of a GitHub Pull Request.

RULES:
- Briefly explain what the PR does and why it exists.
- Mention the main subsystems or areas affected.
- Keep it high-level and readable.
- Do NOT include code diffs, patches, or line-by-line explanations.
- Do NOT list every file unless explicitly asked.

FORMAT:
- 2–4 concise bullet points OR a short paragraph.
""",

    "files": """
You are answering a question about FILES CHANGED in a GitHub Pull Request.

STRICT RULES:
- ONLY list files that were modified in the PR.
- Include file path and change summary (+X/-Y) if available.
- Do NOT describe code logic or behavior.
- Do NOT include diffs or explanations.
- Do NOT mention PR status unless explicitly asked.

FORMAT (MUST FOLLOW):

Files changed in PR #<number>:
- <file_path> (modified) [+X/-Y]
""",

    "changes": """
You are answering a question about CODE CHANGES in a GitHub Pull Request.

RULES:
- Describe WHAT changed in the code and at a conceptual level.
- Mention key functions, logic, or behaviors that were modified.
- Do NOT include raw diffs unless explicitly asked.
- Do NOT mention PR status, dates, or authors.

FORMAT:
- Short structured explanation or bullet points.
""",

    "author": """
You are answering a question about PR AUTHORSHIP.

RULES:
- ONLY mention who created the PR and any contributors or reviewers if available.
- Do NOT describe changes, files, or PR status.
- Be concise and factual.

FORMAT:
PR #<number> Author:
- Created by: <author>
- Contributors: <list or N/A>
""",

    "motivation": """
You are answering WHY a GitHub Pull Request was created.

RULES:
- Explain the problem, bug, or limitation that motivated the PR.
- Mention related issues if available.
- Do NOT describe implementation details or code changes.

FORMAT:
- Short paragraph or 2–3 bullet points.
"""
}

ISSUE_INTENT_SYSTEM_PROMPTS = {
    "status": """
You are answering a GitHub Issue STATUS question.

STRICT RULES:
- ONLY return the Issue status information.
- Do NOT describe description, comments, or implementation.
- Do NOT add overview, summary, or explanation sections.
- Be concise and factual.

FORMAT (MUST FOLLOW EXACTLY):

Issue #<number> Status:
- State: <Open | Closed>
- Created: <date>
- Closed: <date or N/A>
- Updated: <date>
""",

    "summary": """
You are answering a HIGH-LEVEL SUMMARY of a GitHub Issue.

RULES:
- Briefly explain what the issue is about and why it exists.
- Mention the main problem or feature request.
- Keep it high-level and readable.
- Do NOT include detailed code or implementation discussions.
- Do NOT list every comment unless explicitly asked.

FORMAT:
- 2–4 concise bullet points OR a short paragraph.
""",

    "assignee": """
You are answering a question about Issue ASSIGNEE/OWNERSHIP.

RULES:
- ONLY mention who is assigned to the issue and any contributors if available.
- Do NOT describe the issue content, status, or comments.
- Be concise and factual.

FORMAT:
Issue #<number> Assignee:
- Assigned to: <assignee or Unassigned>
- Contributors: <list or N/A>
""",

    "labels": """
You are answering a question about Issue LABELS/TAGS.

RULES:
- ONLY list the labels/tags associated with the issue.
- Do NOT describe the issue content, status, or other details.
- Be concise and factual.

FORMAT:
Issue #<number> Labels:
- <label1>, <label2>, <label3>
""",

    "description": """
You are answering a question about Issue DESCRIPTION/CONTENT.

RULES:
- Describe WHAT the issue is about and the problem/request.
- Mention key details from the issue description.
- Do NOT include all comments or discussion history.
- Do NOT mention status, assignee, or labels unless relevant.

FORMAT:
- Short structured explanation or bullet points.
""",

    "comments": """
You are answering a question about Issue COMMENTS/DISCUSSION.

RULES:
- Summarize key discussion points and comments.
- Mention important updates or resolutions if available.
- Do NOT include the full issue description.
- Do NOT mention status, assignee, or labels unless relevant.

FORMAT:
- Short structured summary of discussion or bullet points.
""",

    "timeline": """
You are answering a question about Issue TIMELINE/HISTORY.

RULES:
- Provide a chronological list of key events (created, updated, closed, major comments).
- Include dates and important milestones.
- Do NOT describe the issue content in detail.
- Be concise and factual.

FORMAT:
Issue #<number> Timeline:
- Created: <date> by <author>
- Updated: <date> - <event>
- Closed: <date> (if applicable)
"""
}


class ResponseHandler:
    """Handler for all response packaging and formatting operations."""
    
    def __init__(self, chatbot):
        """
        Initialize Response handler with reference to chatbot instance.
        
        Args:
            chatbot: The RAGChatbot instance to access shared methods and attributes
        """
        self.chatbot = chatbot

    def _slice_pr_context_by_intent(self, chunks, intent):
        if not intent:
            return chunks

        def meta(c):
            return c.get("metadata", {})

        if intent == "status":
            return [
                c for c in chunks
                if meta(c).get("type") == "pr"
            ]

        if intent == "files":
            return [
                c for c in chunks
                if meta(c).get("file_path") and meta(c).get("type") != "diff"
            ]

        if intent == "changes":
            return [
                c for c in chunks
                if meta(c).get("type") == "diff"
            ]

        if intent == "author":
            return [
                c for c in chunks
                if "author" in meta(c)
            ]

        return chunks

    def _slice_issue_context_by_intent(self, chunks, intent):
        if not intent:
            return chunks

        def meta(c):
            return c.get("metadata", {})

        if intent == "status":
            return [
                c for c in chunks
                if meta(c).get("type") == "issue"
            ]

        if intent == "assignee":
            return [
                c for c in chunks
                if "assignee" in meta(c) or "assigned" in str(meta(c)).lower()
            ]

        if intent == "labels":
            return [
                c for c in chunks
                if "label" in str(meta(c)).lower() or "tag" in str(meta(c)).lower()
            ]

        if intent == "description":
            return [
                c for c in chunks
                if meta(c).get("type") == "issue" and "body" in str(meta(c)).lower()
            ]

        if intent == "comments":
            return [
                c for c in chunks
                if "comment" in str(meta(c)).lower() or meta(c).get("type") == "comment"
            ]

        if intent == "timeline":
            return [
                c for c in chunks
                if "created" in str(meta(c)).lower() or "updated" in str(meta(c)).lower() or "closed" in str(meta(c)).lower()
            ]

        return chunks


    def respond_with_results(
        self,
        github_results: List[Dict[str, Any]],
        query_type: str,
        query: str,
        expanded_query: str,
        role: Optional[str] = None,
        intent: Optional[str] = None
    ) -> Dict[str, Any]:

        # 🔒 STEP 1: Slice context HARD by PR/Issue intent
        if query_type == QueryType.PR_SPECIFIC and intent:
            github_results = self._slice_pr_context_by_intent(github_results, intent)
        elif query_type == QueryType.ISSUE_SPECIFIC and intent:
            github_results = self._slice_issue_context_by_intent(github_results, intent)

        # 🔒 STEP 2: Build context ONLY from sliced chunks
        context = self.chatbot.build_context_from_chunks(github_results, query_type)

        email_results = self.chatbot.retrieve_gmail_correlated(
            github_results,
            self.chatbot.get_query_embedding(expanded_query),
            []
        )

        email_context = self.chatbot.build_email_context(email_results)

        # 🔒 STEP 3: INTENT-AWARE PROMPTING
        if query_type == QueryType.PR_SPECIFIC and intent:
            system_prompt = PR_INTENT_SYSTEM_PROMPTS.get(
                intent, PR_INTENT_SYSTEM_PROMPTS["summary"]
            )

            # 🚫 DO NOT use build_user_prompt here
            user_prompt = f"""
    Answer the following strictly according to the instructions.

    Question:
    {expanded_query}

    Context (may be incomplete; do NOT infer beyond it):
    {context}
    """.strip()

        elif query_type == QueryType.ISSUE_SPECIFIC and intent:
            system_prompt = ISSUE_INTENT_SYSTEM_PROMPTS.get(
                intent, ISSUE_INTENT_SYSTEM_PROMPTS["summary"]
            )

            # 🚫 DO NOT use build_user_prompt here
            user_prompt = f"""
    Answer the following strictly according to the instructions.

    Question:
    {expanded_query}

    Context (may be incomplete; do NOT infer beyond it):
    {context}
    """.strip()

        else:
            # Normal non-PR/Issue or non-intent flow
            system_prompt = self.chatbot.get_dynamic_system_prompt(
                query_type, expanded_query, role=role
            )
            user_prompt = self.chatbot.build_user_prompt(
                expanded_query, context, email_context, query_type
            )

        # 🔒 STEP 4: LLM call
        answer = self.chatbot.call_llm(system_prompt, user_prompt)

        refined = self.chatbot.verify_and_refine_response(
            answer, query, query_type
        )

        return self.package_response(
            refined,
            github_results,
            email_results,
            query_type,
            intent=intent
        )


    def package_response(
        self,
        answer: str,
        github_results: List[Dict[str, Any]],
        email_results: List[Dict[str, Any]],
        query_type: str,
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Package response with sources, emails, and metadata.
        
        Args:
            answer: The generated answer text
            github_results: List of retrieved GitHub results
            email_results: List of retrieved email results
            query_type: Detected query type
            
        Returns:
            Packaged response dict
        """
        # Build GitHub sources list
        sources = []
        if github_results:
            limit = None
            if query_type == QueryType.PR_SPECIFIC and intent == "files":
                limit = len(github_results)

            for i, result in enumerate(github_results[:limit], 1):

                meta = result.get("metadata", {})
                sources.append({
                    "rank": i,
                    "file": meta.get("file_path", "unknown"),
                    "type": meta.get("type", "unknown"),
                    "score": result.get("score", 0.0),
                    "chunk_id": meta.get("chunk_id", "")
                })

        # Build email list (optional)
        emails = []
        if email_results:
            for email in email_results:
                meta = email.get("metadata", {})
                emails.append({
                    "subject": meta.get("subject", ""),
                    "from": meta.get("from", ""),
                    "date": meta.get("date", ""),
                    "relevance": email.get("relevance_score", 0)
                })

        context_quality = (
            min(github_results[0].get("score", 0), 1.0)
            if github_results else 0.0
        )

        return {
            "answer": answer,
            "sources": sources,
            "chunks_retrieved": len(github_results) if github_results else 0,
            "query_type": query_type,
            "context_quality": context_quality,
            "emails": emails,
            "has_diagram": False,
            "related_knowledge": None,
            "is_metrics_query": False
        }
    
    def merge_multi_answers(
        self,
        results: List[Dict[str, Any]],
        original_query: str
    ) -> Dict[str, Any]:
        """
        Merge multiple sub-query results into a SINGLE coherent response.
        Returns a properly formatted response dict (not fragmented UI messages).
        
        Args:
            results: List of response dicts from sub-queries
            original_query: Original user query
            
        Returns:
            Merged response dict
        """
        if not results:
            return self.package_response(
                "No results found for your query.",
                [], [], QueryType.GENERAL
            )

        # If only ONE result, return it directly
        if len(results) == 1:
            return results[0]

        self.chatbot.logger.info(f"MULTI-QUERY MERGE | Merging {len(results)} responses into single answer")

        # Collect all sources and emails
        all_sources = []
        all_emails = []
        total_chunks = 0
        avg_quality = 0.0

        for r in results:
            all_sources.extend(r.get('sources', []))
            all_emails.extend(r.get('emails', []))
            total_chunks += r.get('chunks_retrieved', 0)
            avg_quality += r.get('context_quality', 0.0)

        avg_quality = avg_quality / len(results) if results else 0.0

        # Deduplicate sources by chunk_id
        seen_chunks = set()
        unique_sources = []
        for src in all_sources:
            chunk_id = src.get('chunk_id', '')
            if chunk_id and chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                unique_sources.append(src)

        # Build merged answer (keep it concise, not repetitive)
        merged_answer_parts = []

        for i, result in enumerate(results, 1):
            answer_text = result.get('answer', '').strip()
            if answer_text:
                # Remove redundant headers if they exist
                answer_text = re.sub(r'^#+\s*(Combined Response|Answer|Response)\s*\n+', '', answer_text,
                                     flags=re.IGNORECASE)
                merged_answer_parts.append(answer_text)

        # Join with proper spacing
        final_answer = "\n\n".join(merged_answer_parts)

        self.chatbot.logger.info(
            f"MULTI-QUERY MERGE | Final answer: {len(final_answer)} chars, {len(unique_sources)} unique sources")

        return {
            'answer': final_answer,
            'sources': unique_sources[:10],  # Top 10 sources
            'chunks_retrieved': total_chunks,
            'query_type': 'multi_query',
            'context_quality': avg_quality,
            'emails': all_emails[:5],  # Top 5 emails
            'has_diagram': any(r.get('has_diagram', False) for r in results),
            'related_knowledge': None,
            'is_metrics_query': False
        }

