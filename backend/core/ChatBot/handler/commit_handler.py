"""
Commit-specific handling module for the RAG Chatbot.
Handles all Commit related queries and operations.
"""

import re
from typing import Dict, Any, Optional
from ..query_type import QueryType


class CommitHandler:
    """Handler for all Commit-specific operations and queries."""
    
    def __init__(self, chatbot):
        """
        Initialize Commit handler with reference to chatbot instance.
        
        Args:
            chatbot: The RAGChatbot instance to access shared methods and attributes
        """
        self.chatbot = chatbot
    
    def handle_commit_direct_lookup(
        self,
        entity: Dict[str, Any],
        query: str,
        expanded_query: str,
        query_type: str,
        active_session_id: str,
        role: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle direct Commit lookup when entity type is 'commit'.
        
        Args:
            entity: Entity dict with 'type' and 'sha'
            query: Original user query
            expanded_query: Expanded/rewritten query
            query_type: Detected query type
            active_session_id: Current session ID
            role: Optional role parameter
            
        Returns:
            Response dict if Commit found, None otherwise
        """
        if not entity or entity.get("type") != "commit":
            return None
            
        sha = entity.get("sha", "").strip()
        if not sha:
            return None
            
        self.chatbot.logger.info(f"DIRECT LOOKUP | Searching commit metadata for SHA {sha[:7]}")
        
        possible_keys = ["sha", "commit_sha", "commit_id", "id"]
        
        for key in possible_keys:
            commit_results = self.chatbot.vector_db.find(where={key: sha}, top_k=self.chatbot.top_k)
            if commit_results:
                self.chatbot.logger.info(f"DIRECT LOOKUP | Match via key '{key}' → {len(commit_results)} chunks")
                
                result = self.chatbot.response_handler.respond_with_results(
                    commit_results, query_type, query, expanded_query, role=role
                )
                
                self._update_caches(query, result, active_session_id)
                
                return result
        
        # Fallback — match SHA substring in commit message or title
        commit_results = self.chatbot.vector_db.find(where={"message": f"contains: {sha[:7]}"}, top_k=self.chatbot.top_k)
        if not commit_results:
            commit_results = self.chatbot.vector_db.find(where={"title": f"contains: {sha[:7]}"}, top_k=self.chatbot.top_k)
        
        if commit_results:
            self.chatbot.logger.info(f"DIRECT LOOKUP | Fallback match in message/title → {len(commit_results)} chunks")
            
            result = self.chatbot.response_handler.respond_with_results(commit_results, query_type, query, expanded_query, role=role)
            
            self._update_caches(query, result, active_session_id)
            
            return result
        
        self.chatbot.logger.warning(f"DIRECT LOOKUP | No match for Commit {sha[:7]} across metadata keys")
        return None
    
    def handle_commit_override(
        self,
        raw_sha: re.Match,
        query: str,
        expanded_query: str,
        query_lower: str,
        query_type: str,
        active_session_id: str,
        role: Optional[str] = None,
        schema_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle Commit override when query contains commit keywords and a SHA.
        
        Args:
            raw_sha: Regex match object with commit SHA
            query: Original user query
            expanded_query: Expanded/rewritten query
            query_lower: Lowercase query for keyword matching
            query_type: Detected query type
            active_session_id: Current session ID
            role: Optional role parameter
            
        Returns:
            Response dict if Commit found, None otherwise
        """
        if not raw_sha:
            return None
            
        if not (
            query_type == QueryType.COMMIT_SPECIFIC
            or "commit" in query_lower
        ):
            return None
        
        sha = raw_sha.group(1)
        self.chatbot.logger.info(f"DIRECT LOOKUP (COMMIT override) | Commit {sha[:7]}")
        commit_results = self.chatbot.vector_db.find(where={"sha": sha}, top_k=self.chatbot.top_k)
        
        if commit_results:
            self.chatbot.logger.info(f"DIRECT LOOKUP (COMMIT override) | {len(commit_results)} chunks returned")
            
            result = self.chatbot.response_handler.respond_with_results(
                commit_results, QueryType.COMMIT_SPECIFIC, query, expanded_query, role=role
            )
            self._update_caches(query, result, active_session_id)
            return result
        else:
            self.chatbot.logger.warning(f"DIRECT LOOKUP (COMMIT override) | No match for Commit {sha[:7]}")
            return None
    
    def handle_commit_not_found(
        self,
        raw_sha: re.Match,
        query_type: str,
        query: str,
        active_session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle case when Commit is not found in metadata.
        
        Args:
            raw_sha: Regex match object with commit SHA
            query_type: Detected query type
            query: Original user query
            active_session_id: Current session ID
            
        Returns:
            Response dict with not found message, None if not applicable
        """
        if query_type != QueryType.COMMIT_SPECIFIC or not raw_sha:
            return None
        
        sha = raw_sha.group(1)
        self.chatbot.logger.info(f"DIRECT LOOKUP FINAL | Commit {sha[:7]} not found — stopping without semantic search")
        not_found_answer = f"Commit {sha[:7]} was not found in the repository. It may not exist or was not indexed."
        result = self.chatbot.response_handler.package_response(not_found_answer, [], [], QueryType.COMMIT_SPECIFIC)
        
        self._update_caches(query, result, active_session_id)
        return result
    
    def _update_caches(self, query: str, result: Dict[str, Any], active_session_id: str):
        """Update semantic and response caches."""
        self.chatbot.cache_handler.update_caches(query, result, active_session_id)

