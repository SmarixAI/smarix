"""
PR-specific handling module for the RAG Chatbot.
Handles all Pull Request related queries and operations.
"""

import re
from typing import Dict, Any, Optional, List
from ..query_type import QueryType


class PRHandler:
    """Handler for all PR-specific operations and queries."""
    
    def __init__(self, chatbot):
        """
        Initialize PR handler with reference to chatbot instance.
        
        Args:
            chatbot: The RAGChatbot instance to access shared methods and attributes
        """
        self.chatbot = chatbot
    
    def handle_pr_direct_lookup(
        self,
        entity: Dict[str, Any],
        query: str,
        expanded_query: str,
        active_session_id: str,
        role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle direct PR lookup when entity type is 'pr'.
        
        Args:
            entity: Entity dict with 'type' and 'number'
            query: Original user query
            expanded_query: Expanded/rewritten query
            active_session_id: Current session ID
            role: Optional role parameter
            
        Returns:
            Response dict if PR found, None otherwise
        """
        if not entity or entity.get("type") != "pr":
            return None
            
        num = str(entity["number"]).strip()
        possible_keys = ["pr_number", "number", "id", "pr_id"]
        
        for key in possible_keys:
            pr_results = self.chatbot.vector_db.find(where={key: num}, top_k=self.chatbot.top_k)
            if pr_results:
                self.chatbot.logger.info(f"DIRECT LOOKUP | Match via key '{key}' → {len(pr_results)} chunks")
                result = self.chatbot.response_handler.respond_with_results(
                    pr_results, QueryType.PR_SPECIFIC, query, expanded_query, role=role
                )
                
                self._update_caches(query, result, active_session_id)
                self._save_conversation(active_session_id, query, result)
                
                return result
        
        # Fallback — match numeric substring inside title
        pr_results = self.chatbot.vector_db.find(where={"title": f"contains: {num}"}, top_k=self.chatbot.top_k)
        if pr_results:
            self.chatbot.logger.info(f"DIRECT LOOKUP | Fallback match in title → {len(pr_results)} chunks")
            result = self.chatbot.response_handler.respond_with_results(
                pr_results, QueryType.PR_SPECIFIC, query, expanded_query, role=role
            )
            self._update_caches(query, result, active_session_id)
            self._save_conversation(active_session_id, query, result)
            return result
        
        self.chatbot.logger.warning(f"DIRECT LOOKUP | No match for PR #{num} across metadata keys")
        return None
    
    def detect_pr_intent(self, query_lower: str) -> str:
        if any(k in query_lower for k in ["status", "merged", "open", "closed"]):
            return "status"

        if any(k in query_lower for k in ["file", "files", "changed files", "files changed"]):
            return "files"

        if any(k in query_lower for k in ["change", "diff", "what changed", "modify"]):
            return "changes"

        if any(k in query_lower for k in ["who", "author", "made", "created"]):
            return "author"

        if any(k in query_lower for k in ["why", "reason", "motivation"]):
            return "motivation"

        return "summary"


    
    def handle_pr_override(
        self,
        raw_num: re.Match,
        query: str,
        expanded_query: str,
        query_lower: str,
        query_type: str,
        active_session_id: str,
        role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle PR override when query contains PR keywords and a number.
        
        Args:
            raw_num: Regex match object with PR number
            query: Original user query
            expanded_query: Expanded/rewritten query
            query_lower: Lowercase query for keyword matching
            query_type: Detected query type
            active_session_id: Current session ID
            role: Optional role parameter
            
        Returns:
            Response dict if PR found, None otherwise
        """
        if not raw_num:
            return None
            
        if not (
            query_type == QueryType.PR_SPECIFIC
            or "pr" in query_lower
            or "pull request" in query_lower
            or "merge request" in query_lower
            or "mr" in query_lower
        ):
            return None
        
        num = int(raw_num.group(1))
        self.chatbot.logger.info(f"DIRECT LOOKUP (PR override) | PR #{num}")
        pr_results = self.chatbot.vector_db.find(where={"pr_number": str(num)}, top_k=self.chatbot.top_k)
        
        if pr_results:
            self.chatbot.logger.info(f"DIRECT LOOKUP (PR override) | {len(pr_results)} chunks returned")
            
            try:
                self.chatbot.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
            except Exception as e:
                self.chatbot.logger.error(f"CONVERSATION_STORE | Failed to save user query: {e}")
            
            intent = self.detect_pr_intent(query_lower)
    
            result = self.chatbot.response_handler.respond_with_results(
                pr_results, QueryType.PR_SPECIFIC, query, expanded_query, role=role, intent=intent
            )
            self._update_caches(query, result, active_session_id)
            return result
        else:
            self.chatbot.logger.warning(f"DIRECT LOOKUP (PR override) | No match for PR #{num}")
            return None
    
    def handle_pr_not_found(
        self,
        raw_num: re.Match,
        query_type: str,
        query: str,
        active_session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle case when PR is not found in metadata.
        
        Args:
            raw_num: Regex match object with PR number
            query_type: Detected query type
            query: Original user query
            active_session_id: Current session ID
            
        Returns:
            Response dict with not found message, None if not applicable
        """
        if query_type != QueryType.PR_SPECIFIC or not raw_num:
            return None
        
        num = int(raw_num.group(1))
        self.chatbot.logger.info(f"DIRECT LOOKUP FINAL | PR #{num} not found — stopping without semantic search")
        not_found_answer = f"PR #{num} was not found in the repository. It may not exist or was not indexed."
        result = self.chatbot.response_handler.package_response(not_found_answer, [], [], QueryType.PR_SPECIFIC)
        
        self._update_caches(query, result, active_session_id)
        return result
    
    def handle_pr_issue_tutorial(
        self,
        entity: Dict[str, Any],
        original_query: str,
        expanded_query: str
    ) -> Dict[str, Any]:
        """
        Generate a step-by-step tutorial based on a specific PR or Issue.
        Retrieves comprehensive context about the PR/Issue and creates educational content.
        
        Args:
            entity: Entity dict with 'type' and 'number'
            original_query: Original user query
            expanded_query: Expanded/rewritten query
            
        Returns:
            Response dict with tutorial content
        """
        entity_type = entity['type']
        entity_number = entity['number']
        
        self.chatbot.logger.info(f"TUTORIAL GENERATION | Starting for {entity_type} #{entity_number}")
        
        # Retrieve comprehensive context (use higher top_k for tutorials)
        query_embedding = self.chatbot.get_query_embedding(expanded_query)
        
        if entity_type == 'pr':
            github_results = self.chatbot.vector_db.find(where={"pr_number": str(entity_number)}, top_k=20)
        else:  # issue
            github_results = self.chatbot.vector_db.find(where={"issue_number": str(entity_number)}, top_k=20)
        
        if not github_results:
            self.chatbot.logger.warning(f"TUTORIAL GENERATION | No data found for {entity_type} #{entity_number}")
            return self.chatbot.response_handler.package_response(
                f"I couldn't find any information about {entity_type} #{entity_number} in the repository.",
                [], [], QueryType.PR_ISSUE_TUTORIAL
            )
        
        self.chatbot.logger.info(f"TUTORIAL GENERATION | Retrieved {len(github_results)} chunks")
        
        # Build comprehensive context
        context = self.chatbot.build_context_from_chunks(github_results, QueryType.PR_ISSUE_TUTORIAL)
        
        # Create specialized tutorial prompt
        system_prompt = f"""You are an expert technical educator creating step-by-step tutorials from code changes.

        Your task: Create a comprehensive, beginner-friendly tutorial based on {entity_type.upper()} #{entity_number}.

        TUTORIAL STRUCTURE:
        1. **Overview** - What was changed and why
        2. **Problem Context** - What issue/challenge this addresses
        3. **Step-by-Step Implementation** - Detailed walkthrough of each change
        4. **Code Explanation** - Explain key code sections with inline comments
        5. **Testing** - How to test these changes
        6. **Key Takeaways** - Important concepts learned
        7. **Practice Exercises** - 2-3 exercises for learners to try

        GUIDELINES:
        - Use clear, simple language suitable for intermediate developers
        - Include code snippets with explanations
        - Explain the "why" behind each decision
        - Provide context about the broader system
        - Add helpful tips and best practices
        - Use markdown formatting with headers, code blocks, and lists
        - Be thorough but concise

        Generate a complete tutorial now."""
        
        user_prompt = f"""Generate a tutorial based on this {entity_type}:

        {context}

        Create a comprehensive, educational tutorial following the structure provided."""
        
        # Generate tutorial
        self.chatbot.logger.info("TUTORIAL GENERATION | Calling LLM for tutorial content")
        tutorial_answer = self.chatbot.call_llm(system_prompt, user_prompt)
        
        self.chatbot.logger.info(f"TUTORIAL GENERATION | Completed, Length: {len(tutorial_answer)} chars")
        
        # Extract sources
        sources = []
        for i, result in enumerate(github_results[:10], 1):
            metadata = result.get('metadata', {})
            sources.append({
                'rank': i,
                'file': metadata.get('file_path') or metadata.get('file') or 'unknown',
                'type': metadata.get('type') or 'unknown',
                'score': result.get('score', 0.0),
                'chunk_id': metadata.get('chunk_id', '')
            })
        
        self.chatbot.history.append({'role': 'user', 'content': original_query})
        self.chatbot.history.append({'role': 'assistant', 'content': tutorial_answer})
        
        return {
            'answer': tutorial_answer,
            'sources': sources,
            'chunks_retrieved': len(github_results),
            'query_type': QueryType.PR_ISSUE_TUTORIAL,
            'context_quality': min(github_results[0].get('score', 0), 1.0) if github_results else 0.0,
            'emails': [],
            'has_diagram': False,
            'related_knowledge': None,
            'is_metrics_query': False,
            'entity': f"{entity_type} #{entity_number}"
        }
    
    def handle_pr_issue_coding_question(
        self,
        entity: Dict[str, Any],
        original_query: str,
        expanded_query: str
    ) -> Dict[str, Any]:
        """
        Generate a coding challenge/question based on a specific PR or Issue.
        Creates practice problems that help learners understand the concepts.
        
        Args:
            entity: Entity dict with 'type' and 'number'
            original_query: Original user query
            expanded_query: Expanded/rewritten query
            
        Returns:
            Response dict with coding question content
        """
        entity_type = entity['type']
        entity_number = entity['number']
        
        self.chatbot.logger.info(f"CODING QUESTION GENERATION | Starting for {entity_type} #{entity_number}")
        
        # Retrieve comprehensive context
        query_embedding = self.chatbot.get_query_embedding(expanded_query)
        
        if entity_type == 'pr':
            github_results = self.chatbot.vector_db.find(where={"pr_number": str(entity_number)}, top_k=20)
        else:  # issue
            github_results = self.chatbot.vector_db.find(where={"issue_number": str(entity_number)}, top_k=20)
        
        if not github_results:
            self.chatbot.logger.warning(f"CODING QUESTION GENERATION | No data found for {entity_type} #{entity_number}")
            return self.chatbot.response_handler.package_response(
                f"I couldn't find any information about {entity_type} #{entity_number} in the repository.",
                [], [], QueryType.PR_ISSUE_CODING_QUESTION
            )
        
        self.chatbot.logger.info(f"CODING QUESTION GENERATION | Retrieved {len(github_results)} chunks")
        
        # Build comprehensive context
        context = self.chatbot.build_context_from_chunks(github_results, QueryType.PR_ISSUE_CODING_QUESTION)
        
        # Create specialized coding question prompt
        system_prompt = f"""You are an expert technical interviewer creating coding challenges based on real-world code changes.

        Your task: Create a coding question/challenge inspired by {entity_type.upper()} #{entity_number}.

        QUESTION STRUCTURE:
        1. **Problem Statement** - Clear description of what to build/fix
        2. **Background Context** - Why this problem matters
        3. **Requirements** - Specific functional requirements
        4. **Constraints** - Technical constraints and limitations
        5. **Input/Output Examples** - 2-3 test cases with expected results
        6. **Hints** (Optional) - Helpful hints for solving the problem
        7. **Solution Outline** - High-level approach (spoiler-protected with markdown)
        8. **Follow-up Questions** - 2-3 deeper thinking questions

        GUIDELINES:
        - Make the question realistic and practical
        - Base it on the concepts/patterns from the PR/Issue
        - Make it challenging but solvable
        - Include clear examples and edge cases
        - Provide hints without giving away the solution
        - Use markdown formatting
        - Focus on understanding, not memorization

        Generate a complete coding challenge now."""
        
        user_prompt = f"""Generate a coding question based on this {entity_type}:

        {context}

        Create a comprehensive coding challenge following the structure provided."""
        
        # Generate coding question
        self.chatbot.logger.info("CODING QUESTION GENERATION | Calling LLM for question content")
        question_answer = self.chatbot.call_llm(system_prompt, user_prompt)
        
        self.chatbot.logger.info(f"CODING QUESTION GENERATION | Completed, Length: {len(question_answer)} chars")
        
        # Extract sources
        sources = []
        for i, result in enumerate(github_results[:10], 1):
            metadata = result.get('metadata', {})
            sources.append({
                'rank': i,
                'file': metadata.get('file_path') or metadata.get('file') or 'unknown',
                'type': metadata.get('type') or 'unknown',
                'score': result.get('score', 0.0),
                'chunk_id': metadata.get('chunk_id', '')
            })
        
        self.chatbot.history.append({'role': 'user', 'content': original_query})
        self.chatbot.history.append({'role': 'assistant', 'content': question_answer})
        
        return {
            'answer': question_answer,
            'sources': sources,
            'chunks_retrieved': len(github_results),
            'query_type': QueryType.PR_ISSUE_CODING_QUESTION,
            'context_quality': min(github_results[0].get('score', 0), 1.0) if github_results else 0.0,
            'emails': [],
            'has_diagram': False,
            'related_knowledge': None,
            'is_metrics_query': False,
            'entity': f"{entity_type} #{entity_number}"
        }
    
    def _update_caches(self, query: str, result: Dict[str, Any], active_session_id: str):
        """Update semantic and response caches."""
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.semantic_cache:
            quality_score = result.get('context_quality', 0.8)
            self.chatbot.query_rewriter.semantic_cache.set(
                query, result, active_session_id, quality_score=quality_score
            )
        
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.response_cache:
            self.chatbot.query_rewriter.response_cache.set(query, result, active_session_id)
    
    def _save_conversation(self, active_session_id: str, query: str, result: Dict[str, Any]):
        """Save conversation to conversation store."""
        try:
            self.chatbot.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
            self.chatbot.conversation_store.add_message(
                active_session_id, "assistant", result.get("answer", ""), tokens_used=0
            )
        except Exception as e:
            self.chatbot.logger.error(f"CONVERSATION_STORE | Failed to save user query: {e}")

