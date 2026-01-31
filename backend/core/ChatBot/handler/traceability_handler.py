"""
Traceability-specific handling module for the RAG Chatbot.
Handles all traceability queries and operations.
"""

from typing import Dict, Any, Optional
from ..query_type import QueryType


class TraceabilityHandler:
    """Handler for all traceability-related operations and queries."""
    
    def __init__(self, chatbot):
        """
        Initialize Traceability handler with reference to chatbot instance.
        
        Args:
            chatbot: The RAGChatbot instance to access shared methods and attributes
        """
        self.chatbot = chatbot
    
    def handle_traceability(
        self,
        entity: Dict[str, Any],
        query: str,
        expanded_query: str,
        active_session_id: str,
        role: Optional[str] = None,
        schema_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Handle traceability query for PR or Issue.
        
        Args:
            entity: Entity dict with 'type' and 'number'
            query: Original user query
            expanded_query: Expanded/rewritten query
            active_session_id: Current session ID
            role: Optional role parameter
            
        Returns:
            Response dict if traceability data found, None otherwise
        """
        if not entity:
            return None
        
        self.chatbot.logger.info(f"TRACEABILITY | Handling trace for {entity['type']} #{entity['number']}")
        
        target_key = "pr_number" if entity['type'] == 'pr' else "issue_number"
        
        # Use vector_db directly or multi_index search
        # Since vector_db is aliased to multi_index_store, this works if find() is implemented there
        # Otherwise, use search_by_metadata on the specific index
        if self.chatbot.multi_index_store:
            idx_type = 'pr' if entity['type'] == 'pr' else 'issue'
            results = self.chatbot.multi_index_store.search_by_metadata(
                filters={target_key: str(entity['number'])}, 
                index_type=idx_type, 
                top_k=self.chatbot.top_k
            )
        else:
            results = self.chatbot.vector_db.find(where={target_key: str(entity['number'])}, top_k=self.chatbot.top_k)
        
        if results:
            self.chatbot.logger.info(f"TRACEABILITY | Found {len(results)} chunks")
            result = self.chatbot.response_handler.respond_with_results(
                results, QueryType.TRACEABILITY, query, expanded_query, role=role
            )
            
            # Update Caches
            self._update_caches(query, result, active_session_id)
            
            return result
        else:
            self.chatbot.logger.warning(f"TRACEABILITY | No match for {entity['type']} #{entity['number']}")
            return None
    
    def _update_caches(self, query: str, result: Dict[str, Any], active_session_id: str):
        """Update semantic and response caches."""
        self.chatbot.cache_handler.update_caches(query, result, active_session_id)

