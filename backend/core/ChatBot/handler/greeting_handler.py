"""
Greeting-specific handling module for the RAG Chatbot.
Handles all greeting queries and responses.
"""

from typing import Dict, Any, Iterator
from ..query_type import QueryType


class GreetingHandler:
    """Handler for all greeting-related operations and queries."""
    
    def __init__(self, chatbot):
        """
        Initialize Greeting handler with reference to chatbot instance.
        
        Args:
            chatbot: The RAGChatbot instance to access shared methods and attributes
        """
        self.chatbot = chatbot
    
    def handle_greeting(
        self,
        query: str,
        query_type: str,
        active_session_id: str,
        schema_name: str
    ) -> Dict[str, Any]:
        """
        Handle greeting query in the main chat method.
        
        Args:
            query: Original user query
            query_type: Detected query type (should be QueryType.GREETING)
            active_session_id: Current session ID
            
        Returns:
            Response dict with greeting content
        """
        # Collect greeting response from streaming generator
        greeting_response = self._collect_greeting_response()

        # Update conversation history
        self._update_history(query, greeting_response)

        # Build result dictionary
        result = self._build_response_dict(greeting_response, query_type)

        # Update caches
        self._update_caches(query, result, active_session_id)

        return result
    
    def handle_greeting_stream(
        self,
        query: str,
        query_type: str
    ) -> Iterator[Dict[str, Any]]:
        """
        Handle greeting query in the streaming chat method.
        
        Args:
            query: Original user query
            query_type: Detected query type (should be QueryType.GREETING)
            
        Yields:
            Streaming response chunks and final complete response
        """
        # Update history with user query
        self.chatbot.history.append({'role': 'user', 'content': query})
        
        greeting_response = ""

        # Stream greeting response chunks
        for chunk in self.chatbot.generate_greeting_response_streaming():
            greeting_response += chunk
            yield {'type': 'token', 'content': chunk}

        # Update history with complete response
        self.chatbot.history.append({'role': 'assistant', 'content': greeting_response})

        # Yield final complete response
        yield {
            'type': 'done',                   
            'content': greeting_response,       
            'metadata': {
                k: v for k, v in self._build_response_dict(greeting_response, query_type).items()
                if k != 'answer'               
            }
        }
    
    def _collect_greeting_response(self) -> str:
        """
        Collect greeting response from streaming generator.
        
        Returns:
            Complete greeting response string
        """
        greeting_response = ""
        for chunk in self.chatbot.generate_greeting_response_streaming():
            greeting_response += chunk
        return greeting_response
    
    def _update_history(self, query: str, response: str) -> None:
        """
        Update conversation history with user query and assistant response.
        
        Args:
            query: User query
            response: Assistant response
        """
        self.chatbot.history.append({'role': 'user', 'content': query})
        self.chatbot.history.append({'role': 'assistant', 'content': response})
    
    
    def _build_response_dict(self, greeting_response: str, query_type: str) -> Dict[str, Any]:
        """
        Build standardized response dictionary for greeting.
        
        Args:
            greeting_response: Complete greeting response text
            query_type: Detected query type
            
        Returns:
            Response dictionary with all required fields
        """
        return {
            'answer': greeting_response,
            'sources': [],
            'chunks_retrieved': 0,
            'query_type': query_type,
            'context_quality': 1.0,
            'emails': [],
            'has_diagram': False,
            'related_knowledge': None,
            'is_metrics_query': False
        }
    
    def _update_caches(self, query: str, result: Dict[str, Any], active_session_id: str) -> None:
        """
        Update semantic and response caches.
        
        Args:
            query: Original user query
            result: Response dictionary
            active_session_id: Current session ID
        """
        self.chatbot.cache_handler.update_caches(query, result, active_session_id)

