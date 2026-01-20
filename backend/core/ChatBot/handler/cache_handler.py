"""
Cache handling module for the RAG Chatbot.
Handles all cache operations including semantic cache, response cache, and cache augmentation.
"""

import time
from typing import Dict, Any, Optional


class CacheHandler:
    """Handler for all cache operations."""
    
    def __init__(self, chatbot):
        """
        Initialize Cache handler with reference to chatbot instance.
        
        Args:
            chatbot: The RAGChatbot instance to access shared methods and attributes
        """
        self.chatbot = chatbot
        self._last_semantic_cache_age_update = time.time()
    
    def update_cache_ages(self):
        """
        Update cache ages periodically (runs every 5 minutes).
        Should be called at the start of each query.
        """
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.semantic_cache:
            current_time = time.time()
            if current_time - self._last_semantic_cache_age_update > 300:
                self.chatbot.query_rewriter.semantic_cache.update_ages()
                self._last_semantic_cache_age_update = current_time
    
    def get_semantic_cache(self, query: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result from semantic cache.
        
        Args:
            query: User query
            session_id: Current session ID
            
        Returns:
            Cached result if found, None otherwise
        """
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.semantic_cache:
            return self.chatbot.query_rewriter.semantic_cache.get(query, session_id)
        return None
    
    def get_response_cache(self, query: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result from response cache (legacy cache).
        
        Args:
            query: User query
            session_id: Current session ID
            
        Returns:
            Cached result if found, None otherwise
        """
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.response_cache:
            return self.chatbot.query_rewriter.response_cache.get(query, session_id)
        return None
    
    def set_semantic_cache(
        self,
        query: str,
        result: Dict[str, Any],
        session_id: str,
        quality_score: Optional[float] = None
    ):
        """
        Set result in semantic cache.
        
        Args:
            query: User query
            result: Response dict to cache
            session_id: Current session ID
            quality_score: Optional quality score (defaults to context_quality from result)
        """
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.semantic_cache:
            if quality_score is None:
                quality_score = result.get('context_quality', 0.8)
            self.chatbot.query_rewriter.semantic_cache.set(
                query, result, session_id, quality_score=quality_score
            )
    
    def set_response_cache(self, query: str, result: Dict[str, Any], session_id: str):
        """
        Set result in response cache (legacy cache).
        
        Args:
            query: User query
            result: Response dict to cache
            session_id: Current session ID
        """
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.response_cache:
            self.chatbot.query_rewriter.response_cache.set(query, result, session_id)
    
    def update_caches(
        self,
        query: str,
        result: Dict[str, Any],
        session_id: str,
        quality_score: Optional[float] = None
    ):
        """
        Update both semantic and response caches with the result.
        This is a convenience method that updates both caches at once.
        
        Args:
            query: User query
            result: Response dict to cache
            session_id: Current session ID
            quality_score: Optional quality score (defaults to context_quality from result)
        """
        self.set_semantic_cache(query, result, session_id, quality_score)
        self.set_response_cache(query, result, session_id)
    
    def handle_cached_result(
        self,
        cached_result: Dict[str, Any],
        query: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle a cached result, including augmentation and generation hints.
        
        Args:
            cached_result: Cached result from semantic cache
            query: Original user query
            session_id: Current session ID
            
        Returns:
            Processed result if cache hit should return immediately, None if should continue generation
        """
        if not cached_result:
            return None
        
        # Handle augmentation
        if cached_result.get('_requires_augmentation'):
            self.chatbot.logger.info("🧩 AUGMENTING cached response with new context")
            result = self.augment_cached_response(
                cached_result['_cached_response'],
                cached_result['_original_query'],
                cached_result['_cached_query']
            )
            
            try:
                self.chatbot.conversation_store.add_message(session_id, 'user', query, tokens_used=0)
                self.chatbot.conversation_store.add_message(
                    session_id, 'assistant', result.get('answer', ''), tokens_used=0
                )
            except Exception as e:
                self.chatbot.logger.error(f"Failed to save augmented response: {e}")
            
            return result
        
        # Handle generation with hints
        elif cached_result.get('_requires_generation'):
            self.chatbot.logger.info("💡 Will generate response with cache hints (proceeding to full generation)")
            # Continue to full generation below
            return None
        
        # Direct cache hit - RETURN IMMEDIATELY
        else:
            confidence = cached_result.get('cache_confidence', 'unknown')
            cache_tier = cached_result.get('cache_tier', 'semantic')
            
            self.chatbot.logger.info(
                f"✅ SEMANTIC CACHE HIT | confidence={confidence} | tier={cache_tier}"
            )
            
            try:
                self.chatbot.conversation_store.add_message(session_id, 'user', query, tokens_used=0)
                self.chatbot.conversation_store.add_message(
                    session_id, 'assistant', cached_result.get('answer', ''), tokens_used=0
                )
            except Exception as e:
                self.chatbot.logger.error(f"Failed to save cached exchange: {e}")
            
            return cached_result
    
    def augment_cached_response(
        self,
        cached_response: Dict[str, Any],
        new_query: str,
        original_query: str
    ) -> Dict[str, Any]:
        """
        Augment cached response to specifically answer the new query variant.
        
        Args:
            cached_response: Original cached response
            new_query: New user query
            original_query: Original query that was cached
            
        Returns:
            Augmented response dict
        """
        # Extract differences between queries
        new_words = set(new_query.lower().split())
        orig_words = set(original_query.lower().split())
        unique_words = new_words - orig_words
        
        if not unique_words:
            # No significant differences, return as-is
            return cached_response
        
        query_diff = f"New emphasis on: {', '.join(unique_words)}"
        cached_answer = cached_response.get('answer', '')
        
        # Use fast LLM to augment
        augmentation_prompt = f"""You have a cached response for a similar question. Adjust it slightly to specifically answer the new question.

Original Question: {original_query}
New Question: {new_query}
Key Differences: {query_diff}

Cached Response:
{cached_answer}

Adjusted Response (keep all cached info, just reframe for new question):"""
        
        try:
            augmented_answer = self.chatbot.call_llm(
                "You are adjusting a response to better match a slightly different question.",
                augmentation_prompt
            )
            
            result = cached_response.copy()
            result['answer'] = augmented_answer
            result['augmented'] = True
            result['original_cached_query'] = original_query
            
            self.chatbot.logger.info(
                f"AUGMENTATION | Adjusted response from '{original_query[:40]}' to '{new_query[:40]}'"
            )
            
            return result
        
        except Exception as e:
            self.chatbot.logger.error(f"Augmentation failed: {e}, returning original cached response")
            return cached_response
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get cache statistics.
        
        Returns:
            Cache stats dict if available, None otherwise
        """
        if self.chatbot.query_rewriter and self.chatbot.query_rewriter.semantic_cache:
            return self.chatbot.query_rewriter.semantic_cache.get_stats()
        return None

