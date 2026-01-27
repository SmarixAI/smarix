"""
Issue-specific handling module for the RAG Chatbot.
Handles all Issue related queries and operations.
"""

import re
from typing import Dict, Any, Optional
from ..query_type import QueryType


class IssueHandler:
    """Handler for all Issue-specific operations and queries."""
    
    def __init__(self, chatbot):
        """
        Initialize Issue handler with reference to chatbot instance.
        
        Args:
            chatbot: The RAGChatbot instance to access shared methods and attributes
        """
        self.chatbot = chatbot
    
    def detect_issue_intent(self, query_lower: str) -> str:
        """
        Detect the intent of an issue query to provide more targeted responses.
        
        Args:
            query_lower: Lowercase query string
            
        Returns:
            Intent string: 'status', 'assignee', 'labels', 'description', 'comments', 'timeline', or 'summary'
        """
        if any(k in query_lower for k in ["status", "open", "closed", "state"]):
            return "status"
        
        if any(k in query_lower for k in ["assignee", "assigned", "who", "owner", "responsible"]):
            return "assignee"
        
        if any(k in query_lower for k in ["label", "labels", "tag", "tags", "category"]):
            return "labels"
        
        if any(k in query_lower for k in ["comment", "comments", "discussion", "conversation"]):
            return "comments"
        
        if any(k in query_lower for k in ["timeline", "history", "when", "created", "updated", "closed"]):
            return "timeline"
        
        if any(k in query_lower for k in ["description", "what", "about", "details"]):
            return "description"
        
        return "summary"
    
    def handle_issue_direct_lookup(
        self,
        entity: Dict[str, Any],
        query: str,
        expanded_query: str,
        query_type: str,
        active_session_id: str,
        role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle direct Issue lookup when entity type is 'issue'.
        
        Args:
            entity: Entity dict with 'type' and 'number'
            query: Original user query
            expanded_query: Expanded/rewritten query
            query_type: Detected query type
            active_session_id: Current session ID
            role: Optional role parameter
            
        Returns:
            Response dict if Issue found, None otherwise
        """
        if not entity or entity.get("type") != "issue":
            return None
            
        num = str(entity["number"]).strip()
        self.chatbot.logger.info(f"DIRECT LOOKUP | Searching issue metadata for #{num}")
        
        possible_keys = ["issue_number", "number", "id", "issue_id"]
        issue_results = []
        
        # Pick the ISSUE index metadata directly for debugging
        if hasattr(self.chatbot.vector_db, 'indices'):
            issue_index = self.chatbot.vector_db.indices.get("issue")
            if issue_index and issue_index.metadata:
                self.chatbot.logger.info(f"DIRECT LOOKUP DEBUG | Issue metadata keys: {list(issue_index.metadata[0].keys())}")
            else:
                self.chatbot.logger.info("DIRECT LOOKUP DEBUG | Issue index has no metadata")
        
        query_lower = query.lower()
        intent = self.detect_issue_intent(query_lower)
        
        for key in possible_keys:
            issue_results = self.chatbot.vector_db.find(where={key: num}, top_k=self.chatbot.top_k)
            if issue_results:
                self.chatbot.logger.info(f"DIRECT LOOKUP | Match via key '{key}' → {len(issue_results)} chunks")
                
                result = self.chatbot.response_handler.respond_with_results(
                    issue_results, query_type, query, expanded_query, role=role, intent=intent
                )
                
                self._update_caches(query, result, active_session_id)
                self._save_conversation(active_session_id, query, result, "issue direct-lookup")
                
                return result
        
        # FINAL FALLBACK: substring match inside title
        issue_results = self.chatbot.vector_db.find(where={"title": f"contains: {num}"}, top_k=self.chatbot.top_k)
        if issue_results:
            self.chatbot.logger.info(f"DIRECT LOOKUP | Fallback match in title → {len(issue_results)} chunks")
            
            result = self.chatbot.response_handler.respond_with_results(
                issue_results, query_type, query, expanded_query, role=role, intent=intent
            )
            
            self._update_caches(query, result, active_session_id)
            self._save_conversation(active_session_id, query, result, "issue fallback")
            
            return result
        
        self.chatbot.logger.warning(f"DIRECT LOOKUP | No match for Issue #{num} across all metadata keys")
        return None
    
    def handle_issue_override(
        self,
        raw_num: re.Match,
        query: str,
        expanded_query: str,
        query_type: str,
        active_session_id: str,
        role: Optional[str] = None,
        schema_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle Issue override when query contains issue keywords and a number.
        Similar to PR override logic for consistency.
        
        Args:
            raw_num: Regex match object with Issue number
            query: Original user query
            expanded_query: Expanded/rewritten query
            query_type: Detected query type
            active_session_id: Current session ID
            role: Optional role parameter
            
        Returns:
            Response dict if Issue found, None otherwise
        """
        if not raw_num:
            return None
        
        query_lower = query.lower()
        
        # Check if query type is ISSUE_SPECIFIC or contains issue-related keywords
        if not (
            query_type == QueryType.ISSUE_SPECIFIC
            or "issue" in query_lower
            or "bug" in query_lower
            or "ticket" in query_lower
            or "report" in query_lower
        ):
            return None
        
        num = int(raw_num.group(1))
        self.chatbot.logger.info(f"DIRECT LOOKUP (ISSUE override) | Issue #{num}")
        
        # Try multiple possible keys for issue lookup
        possible_keys = ["issue_number", "number", "id", "issue_id"]
        issue_results = None
        
        for key in possible_keys:
            issue_results = self.chatbot.vector_db.find(where={key: str(num)}, top_k=self.chatbot.top_k)
            if issue_results:
                self.chatbot.logger.info(f"DIRECT LOOKUP (ISSUE override) | Match via key '{key}' → {len(issue_results)} chunks")
                break
        
        if issue_results:
            try:
                self.chatbot.conversation_store.add_message(active_session_id, "user", query, schema_name=schema_name, tokens_used=0)
            except Exception as e:
                self.chatbot.logger.error(f"CONVERSATION_STORE | Failed to save user query: {e}")
            
            intent = self.detect_issue_intent(query_lower)
            
            result = self.chatbot.response_handler.respond_with_results(
                issue_results, QueryType.ISSUE_SPECIFIC, query, expanded_query, role=role, intent=intent
            )
            
            self._update_caches(query, result, active_session_id)
            self._save_conversation(active_session_id, query, result, "issue override")
            
            return result
        else:
            self.chatbot.logger.warning(f"DIRECT LOOKUP (ISSUE override) | No match for Issue #{num}")
            return None
    
    def handle_issue_not_found(
        self,
        raw_num: re.Match,
        query_type: str,
        query: str,
        active_session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle case when Issue is not found in metadata.
        Similar to PR not found handling for consistency.
        
        Args:
            raw_num: Regex match object with Issue number
            query_type: Detected query type
            query: Original user query
            active_session_id: Current session ID
            
        Returns:
            Response dict with not found message, None if not applicable
        """
        if query_type != QueryType.ISSUE_SPECIFIC or not raw_num:
            return None
        
        num = int(raw_num.group(1))
        self.chatbot.logger.info(f"DIRECT LOOKUP FINAL | Issue #{num} not found — stopping without semantic search")
        not_found_answer = f"Issue #{num} was not found in the repository. It may not exist or was not indexed."
        result = self.chatbot.response_handler.package_response(
            not_found_answer, [], [], QueryType.ISSUE_SPECIFIC
        )
        
        self._update_caches(query, result, active_session_id)
        return result
    
    def _update_caches(self, query: str, result: Dict[str, Any], active_session_id: str):
        """Update semantic and response caches."""
        self.chatbot.cache_handler.update_caches(query, result, active_session_id)
    
    def _save_conversation(self, active_session_id: str, query: str, result: Dict[str, Any], context: str = "issue", schema_name: Optional[str] = None):
        """Save conversation to conversation store."""
        try:
            self.chatbot.conversation_store.add_message(active_session_id, "user", query, schema_name=schema_name, tokens_used=0)
            self.chatbot.conversation_store.add_message(
                active_session_id, "assistant", result.get("answer", ""), schema_name=schema_name, tokens_used=0
            )
        except Exception as e:
            self.chatbot.logger.error(f"CONVERSATION_STORE | Failed to save {context} exchange: {e}")

