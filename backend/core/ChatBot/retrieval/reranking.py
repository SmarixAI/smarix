"""
Reranking and diversity selection for retrieval results.
"""
from typing import List, Dict, Any
import numpy as np
from concurrent.futures import ThreadPoolExecutor


class RerankingMixin:
    """Mixin for reranking and diversity selection."""
    
    def _rerank_with_cross_encoder(
        self,
        results: List[Dict[str, Any]],
        query_text: str
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using cross-encoder for better relevance.
        Uses sentence-transformers CrossEncoder model.
        
        Args:
            results: List of search results with 'content' or 'text' field
            query_text: Original query text
            
        Returns:
            Reranked results sorted by cross-encoder score (descending)
        """
        if not results:
            return results
        
        try:
            from sentence_transformers import CrossEncoder
            
            # Lazy load cross-encoder model (cache it to avoid reloading)
            if not hasattr(self, '_cross_encoder_model') or self._cross_encoder_model is None:
                try:
                    # Use lightweight cross-encoder model
                    self.logger.info("RERANK | Loading cross-encoder model (first time, may take ~30s)...")
                    self._cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                    self.logger.info("RERANK | Cross-encoder model loaded successfully")
                except Exception as e:
                    self.logger.warning(f"RERANK | Failed to load cross-encoder: {e}, skipping reranking")
                    self._cross_encoder_model = None  # Mark as failed to avoid retrying
                    return results
            
            # Extract text content from results
            pairs = []
            for result in results:
                # Get text content from various possible fields (check all common locations)
                metadata = result.get('metadata', {})
                content = (
                    result.get('content') or 
                    result.get('text') or 
                    metadata.get('full_content') or
                    metadata.get('content') or
                    metadata.get('text') or
                    metadata.get('chunk_text') or
                    str(metadata)
                )
                if content and len(str(content).strip()) > 10:  # Ensure meaningful content
                    pairs.append([query_text, str(content)])
                else:
                    # If no content, use original score
                    pairs.append(None)
            
            # Filter out None pairs and keep track of indices
            valid_pairs = []
            valid_indices = []
            for i, pair in enumerate(pairs):
                if pair is not None:
                    valid_pairs.append(pair)
                    valid_indices.append(i)
            
            if not valid_pairs:
                self.logger.warning("RERANK | No valid content found for reranking")
                return results
            
            # Get rerank scores (batch processing for efficiency)
            try:
                rerank_scores = self._cross_encoder_model.predict(valid_pairs, show_progress_bar=False)
            except Exception as e:
                self.logger.warning(f"RERANK | Cross-encoder prediction failed: {e}, using original scores")
                return results
            
            # Update scores for valid results
            for idx, score in zip(valid_indices, rerank_scores):
                # Combine original score with rerank score (weighted average)
                original_score = results[idx].get('score', 0.0)
                # Normalize rerank score (usually 0-1, but can be negative)
                normalized_rerank = max(0.0, min(1.0, float(score)))
                
                # Weighted combination: 70% rerank, 30% original (rerank is more accurate)
                combined_score = 0.7 * normalized_rerank + 0.3 * original_score
                results[idx]['score'] = combined_score
                results[idx]['rerank_score'] = float(score)
                results[idx]['original_score'] = original_score
            
                # === Intent-aware reranking boost ===
                try:
                    from ..query_type import QueryType
                    if hasattr(self, "last_query_type") and self.last_query_type == QueryType.CODE_LOCATION:
                        filename = (results[idx].get('metadata', {}).get('name') or
                                    results[idx].get('metadata', {}).get('file') or
                                    results[idx].get('metadata', {}).get('path') or "").lower()

                        # Direct filename hit boost
                        q = query_text.lower().replace(" ", "").replace("_", "").replace("-", "")
                        f = filename.replace("_", "").replace("-", "")
                        if q in f or any(token in f for token in q.split()):
                            results[idx]['score'] += 2.5

                        # Strong priority boost for pure code chunks
                        if results[idx].get('metadata', {}).get('type') == "code":
                            results[idx]['score'] += 1.8
                except Exception:
                    pass

            # Sort by combined score (descending)
            results.sort(key=lambda x: x.get('score', 0.0), reverse=True)
            
            return results
            
        except ImportError:
            self.logger.warning("RERANK | sentence-transformers not available, skipping cross-encoder reranking")
            return results
        except Exception as e:
            self.logger.warning(f"RERANK | Cross-encoder reranking error: {e}, using original scores")
            return results
    
    def _select_diverse_chunks(
        self,
        results: List[Dict[str, Any]],
        query_text: str,
        top_k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Select diverse chunks using Maximal Marginal Relevance (MMR).
        Balances relevance (score) with diversity (content similarity).
        
        Args:
            results: List of reranked results (already sorted by score)
            query_text: Query text for diversity calculation
            top_k: Number of diverse chunks to select
            
        Returns:
            List of diverse chunks
        """
        if len(results) <= top_k:
            return results
        
        try:
            # Use embedding similarity for diversity calculation
            if not hasattr(self, '_diversity_model'):
                # Reuse sentence-transformers model if available
                if hasattr(self, '_sentence_model'):
                    self._diversity_model = self._sentence_model
                elif self.embedding_provider == 'sentence-transformers':
                    from sentence_transformers import SentenceTransformer
                    self._diversity_model = SentenceTransformer(self.embedding_model)
                else:
                    # Fallback: just return top-k by score (no diversity)
                    self.logger.warning("DIVERSITY | No embedding model for diversity, using top-k by score")
                    return results[:top_k]
            
            # Extract embeddings for all chunks
            chunk_texts = []
            for result in results:
                metadata = result.get('metadata', {})
                content = (
                    result.get('content') or 
                    result.get('text') or 
                    metadata.get('full_content') or
                    metadata.get('content') or
                    metadata.get('text') or
                    metadata.get('chunk_text') or
                    str(metadata)
                )
                chunk_texts.append(str(content) if content else "")
            
            # Get embeddings
            try:
                chunk_embeddings = self._diversity_model.encode(chunk_texts, convert_to_numpy=True, show_progress_bar=False)
                query_embedding = self._diversity_model.encode([query_text], convert_to_numpy=True)[0]
            except Exception as e:
                self.logger.warning(f"DIVERSITY | Embedding generation failed: {e}, using top-k by score")
                return results[:top_k]
            
            # MMR algorithm
            selected = []
            remaining = list(range(len(results)))
            lambda_param = 0.7  # Balance: 0.7 = more relevance, 0.3 = more diversity
            
            # Start with highest scoring chunk
            if remaining:
                selected.append(remaining.pop(0))
            
            # Select remaining chunks using MMR
            while len(selected) < top_k and remaining:
                best_idx = None
                best_mmr_score = -float('inf')
                
                for candidate_idx in remaining:
                    # Relevance: similarity to query
                    relevance = np.dot(chunk_embeddings[candidate_idx], query_embedding)
                    
                    # Diversity: max similarity to already selected chunks
                    if selected:
                        max_similarity = max([
                            np.dot(chunk_embeddings[candidate_idx], chunk_embeddings[sel_idx])
                            for sel_idx in selected
                        ])
                    else:
                        max_similarity = 0.0
                    
                    # MMR score: relevance - diversity penalty
                    mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                    
                    if mmr_score > best_mmr_score:
                        best_mmr_score = mmr_score
                        best_idx = candidate_idx
                
                if best_idx is not None:
                    selected.append(best_idx)
                    remaining.remove(best_idx)
                else:
                    break
            
            # Return selected chunks in order
            diverse_results = [results[idx] for idx in selected]
            
            # Add diversity metadata
            for i, result in enumerate(diverse_results):
                result['diversity_rank'] = i + 1
                result['source'] = result.get('index_type', 'unknown')
            
            self.logger.info(f"DIVERSITY | Selected {len(diverse_results)} diverse chunks from {len(results)} candidates")
            
            return diverse_results
            
        except Exception as e:
            self.logger.warning(f"DIVERSITY | Diversity selection failed: {e}, using top-k by score")
            return results[:top_k]

