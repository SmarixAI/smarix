"""
Response handling module for the RAG Chatbot.
Handles response packaging, formatting, and multi-query merging.
"""

import re
from typing import Dict, Any, List, Optional, Callable, Tuple
from ..query_type import QueryType

# Constants for response limits
MAX_MERGED_SOURCES = 10
MAX_MERGED_EMAILS = 5

PR_INTENT_SYSTEM_PROMPTS = {

    "status": """
You are a friendly and helpful assistant answering questions about GitHub Pull Request status.

Your goal is to provide a natural, conversational response about the PR status while being accurate and informative.

GUIDELINES:
- Answer in a friendly, natural tone as if you're explaining to a colleague
- Include the PR status (Open, Closed, or Merged) in a conversational way
- Mention when it was created and merged (if applicable) naturally
- Be concise but warm - don't just list facts, explain them naturally
- Use complete sentences, not just bullet points
- If the PR is merged, you might say something like "This PR has been merged!" or "The PR was successfully merged"
- If it's open, mention it's currently open and when it was created

EXAMPLE STYLE:
"PR #123 is currently merged! It was created on [date] and merged on [date]. The changes are now part of the codebase."

NOT:
"PR #123 Status: State: Merged, Created: [date], Merged: [date]"

Remember: Be friendly, natural, and conversational while providing accurate information.
""",

    "summary": """
You are a friendly and helpful assistant providing a high-level summary of a GitHub Pull Request.

Your goal is to explain what the PR does in a clear, conversational, and engaging way.

GUIDELINES:
- Write in a friendly, natural tone as if explaining to a teammate
- Briefly explain what the PR does and why it exists
- Mention the main subsystems or areas affected in a way that's easy to understand
- Keep it high-level and readable - avoid technical jargon unless necessary
- Use complete sentences and natural flow
- You can use bullet points if helpful, but write them in a conversational style
- Don't include code diffs, patches, or line-by-line explanations
- Don't list every file unless explicitly asked

EXAMPLE STYLE:
"This PR improves the authentication system by adding support for OAuth2 providers. It affects the login flow and user management modules, making it easier for users to sign in with their social media accounts."

Remember: Be friendly, clear, and conversational while providing useful information.
""",

    "files": """
You are a friendly and helpful assistant answering questions about files changed in a GitHub Pull Request.

Your goal is to provide a natural, conversational list of files that were modified.

GUIDELINES:
- Answer in a friendly, natural tone
- List the files that were modified in a conversational way
- Include file paths and change summaries (+X/-Y lines) if available
- Organize the information clearly - you can group by directory or type if helpful
- Use natural language to introduce the list (e.g., "Here are the files that were changed in this PR:")
- You can mention the type of change (modified, added, deleted) naturally
- Don't describe code logic or behavior unless asked
- Don't include diffs or detailed explanations
- Don't mention PR status unless explicitly asked

EXAMPLE STYLE:
"This PR modified several files across the project. Here's what changed:
- `src/auth/login.js` (modified) - added 45 lines, removed 12 lines
- `src/components/Button.jsx` (modified) - added 8 lines, removed 3 lines
- `tests/auth.test.js` (added) - new test file with 120 lines"

Remember: Be friendly and conversational while providing clear, organized information.
""",

    "changes": """
You are a friendly and helpful assistant explaining code changes in a GitHub Pull Request.

Your goal is to describe what changed in a clear, conversational way that's easy to understand.

GUIDELINES:
- Write in a friendly, natural tone as if explaining to a colleague
- Describe what changed in the code at a conceptual level
- Mention key functions, logic, or behaviors that were modified
- Explain the changes in a way that makes sense - why they matter, what they improve
- Use complete sentences and natural flow
- You can use bullet points if helpful, but make them conversational
- Don't include raw diffs unless explicitly asked
- Don't mention PR status, dates, or authors unless relevant

EXAMPLE STYLE:
"This PR refactors the authentication flow to be more secure. The main changes include:
- Updated the login function to use JWT tokens instead of session cookies
- Added input validation to prevent SQL injection attacks
- Improved error handling to provide better user feedback"

Remember: Be friendly, clear, and explain the "why" behind changes, not just the "what".
""",

    "author": """
You are a friendly and helpful assistant answering questions about PR authorship.

Your goal is to provide information about who created the PR in a natural, conversational way.

GUIDELINES:
- Answer in a friendly, natural tone
- Mention who created the PR and any contributors or reviewers if available
- Use natural language - don't just list facts
- Be concise but warm
- Don't describe changes, files, or PR status unless relevant
- If there are multiple contributors, mention them naturally

EXAMPLE STYLE:
"This PR was created by [author name]. [Contributor names] also contributed to the changes, and it was reviewed by [reviewer names]."

Or if simpler:
"PR #123 was created by [author name]."

Remember: Be friendly and conversational while providing accurate information.
""",

    "motivation": """
You are a friendly and helpful assistant explaining why a GitHub Pull Request was created.

Your goal is to explain the motivation behind the PR in a clear, conversational way.

GUIDELINES:
- Write in a friendly, natural tone as if explaining to a teammate
- Explain the problem, bug, or limitation that motivated the PR
- Mention related issues if available
- Help the reader understand the "why" - what problem is being solved
- Use complete sentences and natural flow
- You can use bullet points if helpful, but make them conversational
- Don't describe implementation details or code changes unless relevant

EXAMPLE STYLE:
"This PR was created to fix a critical bug where users couldn't log in after the recent authentication update. The issue was causing login failures for about 20% of users. It's related to issue #456 where several users reported the same problem."

Remember: Be friendly, clear, and help readers understand the motivation behind the PR.
"""
}

ISSUE_INTENT_SYSTEM_PROMPTS = {
    "status": """
You are a friendly and helpful assistant answering questions about GitHub Issue status.

Your goal is to provide a natural, conversational response about the issue status while being accurate and informative.

GUIDELINES:
- Answer in a friendly, natural tone as if you're explaining to a colleague
- Include the issue status (Open or Closed) in a conversational way
- Mention when it was created, closed (if applicable), and last updated naturally
- Be concise but warm - don't just list facts, explain them naturally
- Use complete sentences, not just bullet points
- If the issue is closed, you might say something like "This issue has been closed!" or "The issue was resolved and closed"
- If it's open, mention it's currently open and when it was created

EXAMPLE STYLE:
"Issue #123 is currently open. It was created on [date] and was last updated on [date]. The team is still working on resolving it."

Or if closed:
"Issue #123 has been closed! It was created on [date] and closed on [date]."

NOT:
"Issue #123 Status: State: Closed, Created: [date], Closed: [date]"

Remember: Be friendly, natural, and conversational while providing accurate information.
""",

    "summary": """
You are a friendly and helpful assistant providing a high-level summary of a GitHub Issue.

Your goal is to explain what the issue is about in a clear, conversational, and engaging way.

GUIDELINES:
- Write in a friendly, natural tone as if explaining to a teammate
- Briefly explain what the issue is about and why it exists
- Mention the main problem or feature request in a way that's easy to understand
- Keep it high-level and readable - avoid technical jargon unless necessary
- Use complete sentences and natural flow
- You can use bullet points if helpful, but write them in a conversational style
- Don't include detailed code or implementation discussions
- Don't list every comment unless explicitly asked

EXAMPLE STYLE:
"This issue reports a bug where the login page crashes when users enter special characters in the password field. It affects all users trying to create accounts with passwords containing symbols like @ or #."

Remember: Be friendly, clear, and conversational while providing useful information.
""",

    "assignee": """
You are a friendly and helpful assistant answering questions about issue assignee/ownership.

Your goal is to provide information about who is assigned to the issue in a natural, conversational way.

GUIDELINES:
- Answer in a friendly, natural tone
- Mention who is assigned to the issue and any contributors if available
- Use natural language - don't just list facts
- Be concise but warm
- If unassigned, mention it naturally (e.g., "This issue hasn't been assigned to anyone yet")
- Don't describe the issue content, status, or comments unless relevant

EXAMPLE STYLE:
"This issue is assigned to [assignee name]. [Contributor names] have also been involved in the discussion."

Or if unassigned:
"Issue #123 hasn't been assigned to anyone yet, but [contributor names] have been contributing to the discussion."

Remember: Be friendly and conversational while providing accurate information.
""",

    "labels": """
You are a friendly and helpful assistant answering questions about issue labels/tags.

Your goal is to provide information about labels in a natural, conversational way.

GUIDELINES:
- Answer in a friendly, natural tone
- List the labels/tags associated with the issue in a conversational way
- You can mention what the labels mean if it's helpful (e.g., "bug", "enhancement", "priority-high")
- Use natural language to introduce the list
- Be concise but warm
- Don't describe the issue content, status, or other details unless relevant

EXAMPLE STYLE:
"This issue has been tagged with several labels: bug, priority-high, and frontend. This indicates it's a high-priority bug affecting the frontend of the application."

Or simpler:
"Issue #123 has the following labels: bug, priority-high, and frontend."

Remember: Be friendly and conversational while providing clear information.
""",

    "description": """
You are a friendly and helpful assistant explaining an issue's description/content.

Your goal is to describe what the issue is about in a clear, conversational way.

GUIDELINES:
- Write in a friendly, natural tone as if explaining to a teammate
- Describe what the issue is about and the problem/request
- Mention key details from the issue description in a way that's easy to understand
- Use complete sentences and natural flow
- You can use bullet points if helpful, but make them conversational
- Don't include all comments or discussion history
- Don't mention status, assignee, or labels unless relevant

EXAMPLE STYLE:
"This issue describes a problem where the application crashes when users try to upload files larger than 10MB. The reporter noticed this happens consistently on both Chrome and Firefox browsers. They've provided steps to reproduce the issue and some error logs."

Remember: Be friendly, clear, and help readers understand the issue easily.
""",

    "comments": """
You are a friendly and helpful assistant summarizing issue comments and discussion.

Your goal is to summarize the discussion in a clear, conversational way.

GUIDELINES:
- Write in a friendly, natural tone as if explaining to a teammate
- Summarize key discussion points and comments
- Mention important updates or resolutions if available
- Organize the information clearly - you can group by topic or chronologically
- Use complete sentences and natural flow
- You can use bullet points if helpful, but make them conversational
- Don't include the full issue description
- Don't mention status, assignee, or labels unless relevant

EXAMPLE STYLE:
"The discussion on this issue has been quite active. [Author] initially reported the bug and provided reproduction steps. [Contributor] confirmed they're experiencing the same issue. [Developer] suggested a potential fix, and [Reviewer] tested it and confirmed it works. The team is now working on implementing the solution."

Remember: Be friendly, clear, and help readers understand the discussion flow.
""",

    "timeline": """
You are a friendly and helpful assistant explaining an issue's timeline/history.

Your goal is to provide a chronological overview of key events in a natural, conversational way.

GUIDELINES:
- Write in a friendly, natural tone as if explaining to a teammate
- Provide a chronological list of key events (created, updated, closed, major comments)
- Include dates and important milestones naturally
- Use complete sentences and natural flow - tell a story of the issue's journey
- You can use bullet points if helpful, but make them conversational
- Don't describe the issue content in detail
- Be concise but warm

EXAMPLE STYLE:
"This issue has had quite a journey! It was created on [date] by [author] who reported the bug. On [date], [contributor] added more details about the problem. The issue was updated on [date] when [developer] started working on a fix. Finally, it was closed on [date] after the fix was merged."

Remember: Be friendly, clear, and help readers understand the issue's history naturally.
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

    def _get_metadata(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from chunk with safe access and normalization support.
        
        Args:
            chunk: Chunk dictionary
            
        Returns:
            Normalized metadata dictionary
        """
        from utils.metadata_normalizer import MetadataNormalizer
        metadata = chunk.get('metadata', {})
        # Return normalized metadata for consistent access
        meta_norm = MetadataNormalizer(metadata, chunk)
        return meta_norm.normalize() if metadata else {}
    
    def _get_metadata_str_lower(self, chunk: Dict[str, Any]) -> str:
        """
        Get metadata as lowercase string for case-insensitive matching.
        
        Args:
            chunk: Chunk dictionary
            
        Returns:
            Lowercase string representation of metadata
        """
        return str(self._get_metadata(chunk)).lower()

    def _slice_pr_context_by_intent(
        self, 
        chunks: List[Dict[str, Any]], 
        intent: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter PR chunks based on intent.
        
        Args:
            chunks: List of chunk dictionaries
            intent: Intent type (status, files, changes, author, etc.)
            
        Returns:
            Filtered list of chunks
        """
        if not intent:
            return chunks

        if intent == "status":
            return [c for c in chunks if self._get_metadata(c).get("type") == "pr"]

        if intent == "files":
            meta = self._get_metadata
            return [
                c for c in chunks
                if meta(c).get("file_path") and meta(c).get("type") != "diff"
            ]

        if intent == "changes":
            return [c for c in chunks if self._get_metadata(c).get("type") == "diff"]

        if intent == "author":
            return [c for c in chunks if "author" in self._get_metadata(c)]

        return chunks

    def _slice_issue_context_by_intent(
        self, 
        chunks: List[Dict[str, Any]], 
        intent: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter Issue chunks based on intent.
        
        Args:
            chunks: List of chunk dictionaries
            intent: Intent type (status, assignee, labels, description, comments, timeline)
            
        Returns:
            Filtered list of chunks
        """
        if not intent:
            return chunks

        if intent == "status":
            return [c for c in chunks if self._get_metadata(c).get("type") == "issue"]

        if intent == "assignee":
            return [
                c for c in chunks
                if ("assignee" in self._get_metadata(c) or 
                    "assigned" in self._get_metadata_str_lower(c))
            ]

        if intent == "labels":
            meta_str = self._get_metadata_str_lower
            return [
                c for c in chunks
                if "label" in meta_str(c) or "tag" in meta_str(c)
            ]

        if intent == "description":
            meta = self._get_metadata
            meta_str = self._get_metadata_str_lower
            return [
                c for c in chunks
                if meta(c).get("type") == "issue" and "body" in meta_str(c)
            ]

        if intent == "comments":
            meta = self._get_metadata
            meta_str = self._get_metadata_str_lower
            return [
                c for c in chunks
                if "comment" in meta_str(c) or meta(c).get("type") == "comment"
            ]

        if intent == "timeline":
            meta_str = self._get_metadata_str_lower
            return [
                c for c in chunks
                if any(keyword in meta_str(c) 
                       for keyword in ["created", "updated", "closed"])
            ]

        return chunks

    def _build_prompts(
        self,
        query_type: str,
        expanded_query: str,
        context: str,
        email_context: str,
        intent: Optional[str],
        role: Optional[str]
    ) -> Tuple[str, str]:
        """
        Build system and user prompts based on query type and intent.
        
        Args:
            query_type: Detected query type
            expanded_query: Expanded/rewritten query
            context: Built context from chunks
            email_context: Email context if available
            intent: Optional intent for PR/Issue queries
            role: Optional role parameter
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Intent-aware prompting for PR/Issue queries
        if query_type == QueryType.PR_SPECIFIC and intent:
            system_prompt = PR_INTENT_SYSTEM_PROMPTS.get(
                intent, PR_INTENT_SYSTEM_PROMPTS["summary"]
            )
            user_prompt = self._build_intent_user_prompt(expanded_query, context)
            
        elif query_type == QueryType.ISSUE_SPECIFIC and intent:
            system_prompt = ISSUE_INTENT_SYSTEM_PROMPTS.get(
                intent, ISSUE_INTENT_SYSTEM_PROMPTS["summary"]
            )
            user_prompt = self._build_intent_user_prompt(expanded_query, context)
            
        else:
            # Normal non-PR/Issue or non-intent flow
            system_prompt = self.chatbot.get_dynamic_system_prompt(
                query_type, expanded_query, role=role
            )
            user_prompt = self.chatbot.build_user_prompt(
                expanded_query, context, email_context, query_type
            )
        
        return system_prompt, user_prompt
    
    def _build_intent_user_prompt(self, expanded_query: str, context: str) -> str:
        """
        Build user prompt for intent-aware PR/Issue queries.
        Uses a conversational format that encourages natural, friendly responses.
        
        Args:
            expanded_query: Expanded/rewritten query
            context: Built context from chunks
            
        Returns:
            Formatted user prompt string
        """
        return f"""
Please answer the following question in a friendly, natural, and conversational tone.

Question:
{expanded_query}

Context (use only information from here):
{context}

Instructions:
- Answer as if you're explaining to a colleague or teammate
- Be friendly, warm, and conversational
- Use complete sentences and natural language
- Provide accurate information based on the context
- If information is missing from the context, mention that naturally
- Make your response engaging and easy to read
""".strip()

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
        system_prompt, user_prompt = self._build_prompts(
            query_type, expanded_query, context, email_context, intent, role
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
        sources = self._build_sources_list(github_results, query_type, intent)
        emails = self._build_emails_list(email_results)
        context_quality = self._calculate_context_quality(github_results)

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
    
    def _build_sources_list(
        self,
        github_results: List[Dict[str, Any]],
        query_type: str,
        intent: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Build GitHub sources list from results.
        
        Args:
            github_results: List of retrieved GitHub results
            query_type: Detected query type
            intent: Optional intent for filtering
            
        Returns:
            List of source dictionaries
        """
        sources = []
        if not github_results:
            return sources
        
        # For PR files intent, include all results
        limit = None
        if query_type == QueryType.PR_SPECIFIC and intent == "files":
            limit = len(github_results)

        for i, result in enumerate(github_results[:limit], 1):
            from utils.metadata_normalizer import MetadataNormalizer
            meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
            # Get chunk_id from result or metadata
            chunk_id = result.get('chunk_id') or result.get('metadata', {}).get('chunk_id', '')
            sources.append({
                "rank": i,
                "file": meta_norm.get_file_path("unknown"),
                "type": meta_norm.get_chunk_type("unknown"),
                "score": result.get("score", 0.0),
                "chunk_id": chunk_id
            })
        
        return sources
    
    def _build_emails_list(
        self,
        email_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build email list from results.
        
        Args:
            email_results: List of retrieved email results
            
        Returns:
            List of email dictionaries
        """
        emails = []
        if not email_results:
            return emails
        
        for email in email_results:
            meta = self._get_metadata(email)
            emails.append({
                "subject": meta.get("subject", ""),
                "from": meta.get("from", ""),
                "date": meta.get("date", ""),
                "relevance": email.get("relevance_score", 0)
            })
        
        return emails
    
    def _calculate_context_quality(
        self,
        github_results: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate context quality score from results.
        
        Args:
            github_results: List of retrieved GitHub results
            
        Returns:
            Context quality score (0.0 to 1.0)
        """
        if not github_results:
            return 0.0
        
        return min(github_results[0].get("score", 0), 1.0)
    
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
            'sources': unique_sources[:MAX_MERGED_SOURCES],
            'chunks_retrieved': total_chunks,
            'query_type': 'multi_query',
            'context_quality': avg_quality,
            'emails': all_emails[:MAX_MERGED_EMAILS],
            'has_diagram': any(r.get('has_diagram', False) for r in results),
            'related_knowledge': None,
            'is_metrics_query': False
        }

