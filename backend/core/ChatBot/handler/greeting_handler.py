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
        active_session_id: str
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
        greeting_response = ""
        for chunk in self.chatbot.generate_greeting_response_streaming():
            greeting_response += chunk
            # printing is optional; caller may handle streaming
            try:
                print(chunk, end='', flush=True)
            except Exception:
                pass

        self.chatbot.history.append({'role': 'user', 'content': query})
        self.chatbot.history.append({'role': 'assistant', 'content': greeting_response})

        try:
            self.chatbot.conversation_store.add_message(active_session_id, "user", query, tokens_used=0)
            self.chatbot.conversation_store.add_message(active_session_id, "assistant", greeting_response, tokens_used=0)
            self.chatbot.logger.info(f"CONVERSATION_STORE | Saved greeting exchange to session {active_session_id[:8]}...")
        except Exception as e:
            self.chatbot.logger.error(f"CONVERSATION_STORE | Failed to save greeting: {e}")

        result = {
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
        self.chatbot.history.append({'role': 'user', 'content': query})
        greeting_response = ""

        for chunk in self.chatbot.generate_greeting_response_streaming():
            greeting_response += chunk
            yield {'type': 'chunk', 'content': chunk}

        self.chatbot.history.append({'role': 'assistant', 'content': greeting_response})

        yield {
            'type': 'complete',
            'content': {
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
        }
    
    def _update_caches(self, query: str, result: Dict[str, Any], active_session_id: str):
        """Update semantic and response caches."""
        self.chatbot.cache_handler.update_caches(query, result, active_session_id)

