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
        
        for key in possible_keys:
            issue_results = self.chatbot.vector_db.find(where={key: num}, top_k=self.chatbot.top_k)
            if issue_results:
                self.chatbot.logger.info(f"DIRECT LOOKUP | Match via key '{key}' → {len(issue_results)} chunks")
                
                result = self.chatbot.response_handler.respond_with_results(
                    issue_results, query_type, query, expanded_query, role=role
                )
                
                self._update_caches(query, result, active_session_id)
                self._save_conversation(active_session_id, query, result, "issue direct-lookup")
                
                return result
        
        # FINAL FALLBACK: substring match inside title
        issue_results = self.chatbot.vector_db.find(where={"title": f"contains: {num}"}, top_k=self.chatbot.top_k)
        if issue_results:
            self.chatbot.logger.info(f"DIRECT LOOKUP | Fallback match in title → {len(issue_results)} chunks")
            
            result = self.chatbot.response_handler.respond_with_results(issue_results, query_type, query, expanded_query, role=role)
            
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
        role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle Issue override when query type is ISSUE_SPECIFIC and contains issue keywords.
        
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
        if query_type != QueryType.ISSUE_SPECIFIC or not raw_num:
            return None
        
        # Check if query contains issue-related keywords
        if not any(t in query.lower() for t in ["issue", "bug", "ticket", "report"]):
            return None
        
        num = int(raw_num.group(1))
        self.chatbot.logger.info(f"DIRECT LOOKUP (ISSUE override) | Issue #{num}")
        issue_results = self.chatbot.vector_db.find(where={"issue_number": str(num)}, top_k=self.chatbot.top_k)
        
        if issue_results:
            result = self.chatbot.response_handler.respond_with_results(
                issue_results, QueryType.ISSUE_SPECIFIC, query, expanded_query, role=role
            )
            
            self._update_caches(query, result, active_session_id)
            self._save_conversation(active_session_id, query, result, "issue override")
            
            return result
        else:
            self.chatbot.logger.warning(f"DIRECT LOOKUP (ISSUE override) | No match for Issue #{num}")
            return None
    
    def _update_caches(self, query: str, result: Dict[str, Any], active_session_id: str):
        """Update semantic and response caches."""
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.semantic_cache:
            quality_score = result.get('context_quality', 0.8)
            self.chatbot.query_rewriter.semantic_cache.set(
                query, result, active_session_id, quality_score=quality_score
            )
        
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.response_cache:
            self.chatbot.query_rewriter.response_cache.set(query, result, active_session_id)
    
    def _save_conversation(self, active_session_id: str, query: str, result: Dict[str, Any], context: str = "issue"):
        """Save conversation to conversation store."""
        try:
            self.chatbot.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
            self.chatbot.conversation_store.add_message(
                active_session_id, "assistant", result.get("answer", ""), tokens_used=0
            )
        except Exception as e:
            self.chatbot.logger.error(f"CONVERSATION_STORE | Failed to save {context} exchange: {e}")

