"""
Multi-index retrieval strategy with query routing, parallel retrieval, and reranking.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from ..query_type import QueryType
from utils.metadata_normalizer import MetadataNormalizer


class MultiIndexRetrievalMixin:
    """Mixin for multi-index retrieval with hybrid strategy."""
    
    def _retrieve_multi_index(
        self,
        query_embedding: np.ndarray,
        query_type: str,
        entity: Optional[Dict[str, Any]],
        keywords: List[str],
        top_k: Optional[int],
        query_text: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        HYBRID RETRIEVAL STRATEGY:
        STEP 1: Query Routing (LLM) - Route to TOP-3 indexes + overall_embedding fallback
        STEP 2: Parallel Retrieval - Retrieve weighted chunks: 7-5-3 (highest to lowest confidence)
        STEP 3: Cross-Encoder Reranking - Rerank ALL chunks with cross-encoder
        STEP 4: Context Fusion - Select TOP-8 diverse chunks with source attribution
        """
        retrieve_k = top_k or self.top_k
        # Weighted retrieval: 7-5-3 based on confidence scores (total: 15 chunks)
        top_k_weights = [7, 5, 3]  # Highest confidence gets 7, second gets 5, third gets 3
        final_k = 8  # TOP-8 diverse chunks after reranking
        
        # STEP 1: Query Routing - Get TOP-3 indexes
        top3_indexes = self._route_to_indexes(query_text or "", query_type)
        
        # STEP 2: Parallel Retrieval - Weighted retrieval (7-5-3) based on confidence
        # Sort top3_indexes by confidence (descending) to ensure correct order
        top3_indexes_sorted = sorted(top3_indexes, key=lambda x: x[1], reverse=True)[:3]
        
        all_results = []
        repo_filters = self._get_repo_filters()
        
        def search_index(index_type: str, top_k_count: int) -> List[Dict[str, Any]]:
            """Search a single index in parallel with specified top_k"""
            try:
                target_index = 'graph_nodes' if index_type == 'impact_analysis' else index_type
                results = self.multi_index_store.search_by_type(
                    query_embedding,
                    index_type=target_index,
                    top_k=top_k_count
                )
                # Add index type and routing confidence
                for result in results:
                    result['index_type'] = target_index
                    # Find confidence for this index
                    conf = next((conf for idx, conf in top3_indexes_sorted if idx == index_type), 0.5)
                    result['routing_confidence'] = conf
                return results
            except Exception as e:
                self.logger.warning(f"SEARCH | Failed to search '{index_type}' index: {e}")
                return []
        
        # Parallel retrieval from TOP-3 indexes with weighted top_k (7-5-3)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for i, (idx_type, conf) in enumerate(top3_indexes_sorted):
                top_k_count = top_k_weights[i] if i < len(top_k_weights) else 5
                future = executor.submit(search_index, idx_type, top_k_count)
                futures.append((future, idx_type, top_k_count))
            
            for future, idx_type, top_k_count in futures:
                try:
                    results = future.result()
                    all_results.extend(results)
                    self.logger.info(f"SEARCH | '{idx_type}' index: {len(results)} results (requested: {top_k_count})")
                except Exception as e:
                    self.logger.error(f"SEARCH | Error retrieving from '{idx_type}': {e}")
        
        # STEP 2b: ALWAYS include 'all' index (combined/fallback index) as fallback
        # Use 5 chunks from combined index (same as before)
        try:
            combined_results = self.multi_index_store.search_all(
                query_embedding,
                top_k=5,  # Fixed 5 for fallback
                filters=repo_filters
            )
            for result in combined_results:
                result['index_type'] = result.get('index_type', 'all')
                result['routing_confidence'] = 0.3  # Lower confidence for fallback
            all_results.extend(combined_results)
            self.logger.info(f"SEARCH | 'all' index (fallback): {len(combined_results)} results")
        except Exception as e:
            self.logger.warning(f"SEARCH | 'all' index search failed: {e}")
        
        # Deduplicate by chunk_id
        seen_ids = set()
        unique_results = []
        for result in all_results:
            chunk_id = result.get('chunk_id', '')
            if chunk_id and chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_results.append(result)
        
        # CRITICAL: Filter by repo after deduplication
        unique_results = self._filter_by_repo(unique_results)

        # 🚨 HARD STOP: Ambiguous filename for CODE_LOCATION
        if query_type == QueryType.CODE_LOCATION and query_text:
            # Normalize filename from query (e.g. Contents.json)
            query_filename = query_text.strip().lower()

            matching_paths = {
                MetadataNormalizer(r.get("metadata", {}), r).get_file_path()
                for r in unique_results
                if MetadataNormalizer(r.get("metadata", {}), r)
                .get_file_path()
                .lower()
                .endswith(query_filename)
            }

            if len(matching_paths) > 1:
                self.logger.warning(
                    "AMBIGUOUS_FILENAME | '%s' found in multiple paths: %s",
                    query_filename,
                    sorted(matching_paths),
                )

                # Annotate for ResponseHandler
                for r in unique_results:
                    r["_ambiguous_filename"] = True
                    r["_all_matching_paths"] = sorted(matching_paths)

                return unique_results


        
        self.logger.info(f"RETRIEVAL | Total unique chunks retrieved: {len(unique_results)} (target: 15+)")
        
        if not unique_results:
            self.logger.warning("RETRIEVAL | No results found, returning empty list")
            return []
        
        # For CODE_LOCATION: Try file path index first, then merge with vector results
        if query_type == QueryType.CODE_LOCATION and query_text:
            # Get file index results (from RepoFilterMixin)
            if hasattr(self, '_retrieve_by_file_path'):
                file_path_results = self._retrieve_by_file_path(query_text, keywords)
                
                if file_path_results:
                    # Merge file index results with vector results
                    file_chunk_ids = {r.get('chunk_id') for r in file_path_results if r.get('chunk_id')}
                    
                    # Add file index results to unique_results
                    for file_result in file_path_results:
                        chunk_id = file_result.get('chunk_id')
                        if chunk_id:
                            # Check if already in unique_results
                            existing = next((r for r in unique_results if r.get('chunk_id') == chunk_id), None)
                            if existing:
                                # Update score to be higher (file index takes priority)
                                existing['score'] = max(existing.get('score', 0), file_result.get('score', 0))
                            else:
                                unique_results.append(file_result)
                    
                    self.logger.info(f"HYBRID_FILE_RETRIEVAL | Added {len(file_path_results)} file index results to {len(unique_results)} total")
        
        # Filename keyword boost to help CODE_LOCATION find the right file
        # Also prioritize code chunks and filter out PR/issue chunks
        if query_type == QueryType.CODE_LOCATION and query_text:
            normalized_query = query_text.lower().replace(" ", "").replace("_", "").replace("-", "")
            filtered_results = []
            
            for r in unique_results:
                # Use metadata normalizer for unified file path access
                meta_norm = MetadataNormalizer(r.get("metadata", {}), r)
                chunk_type = meta_norm.get_chunk_type("")
                
                # For CODE_LOCATION queries, strongly prioritize code chunks
                # Filter out PR/issue chunks unless they're highly relevant
                if chunk_type in ['pr', 'issue', 'email']:
                    # Only keep if it has a very high score (might be relevant)
                    if r.get("score", 0) < 0.8:  # Threshold for keeping PR/issue chunks
                        continue
                
                file_path = meta_norm.get_file_path("")
                filename = file_path.lower() if file_path else ""
                normalized_file = filename.replace(" ", "").replace("_", "").replace("-", "")
                
                # Strong boost for file path matches
                if normalized_query in normalized_file or any(token in normalized_file for token in normalized_query.split()):
                    r["score"] = r.get("score", 0) + 5.0   # very strong boost
                
                # Additional boost for code chunks
                if chunk_type == "code":
                    r["score"] = r.get("score", 0) + 3.0   # prioritize code chunks
                
                filtered_results.append(r)
            
            unique_results = filtered_results

        # STEP 3: Cross-Encoder Reranking
        if query_text:
            try:
                unique_results = self._rerank_with_cross_encoder(unique_results, query_text)
                self.logger.info(f"RERANK | Cross-encoder reranking completed: {len(unique_results)} chunks")
            except Exception as e:
                self.logger.warning(f"RERANK | Cross-encoder reranking failed: {e}, using original scores")
        
        # Apply entity filters if provided
        if entity:
            entity_type = entity.get('type')
            filtered_results = []
            for result in unique_results:
                # Use metadata normalizer for unified access
                meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
                if entity_type == 'issue' and meta_norm.get_issue_number() == entity.get('number'):
                    filtered_results.append(result)
                elif entity_type == 'pr' and meta_norm.get_pr_number() == entity.get('number'):
                    filtered_results.append(result)
                elif entity_type == 'commit' and result.get('metadata', {}).get('sha', '').startswith(entity.get('sha', '')):
                    filtered_results.append(result)
            
            if filtered_results:
                unique_results = filtered_results
                self.logger.info(f"FILTER | Entity filter applied: {len(filtered_results)} results")
        
        # Apply hybrid retrieval boost if enabled
        if self.use_hybrid_retrieval:
            unique_results = self.boost_by_metadata(unique_results, keywords, query_type)
        
        # STEP 4: Context Fusion - Select TOP-8 diverse chunks
        final_results = self._select_diverse_chunks(unique_results, query_text or "", final_k)
        
        # CRITICAL: Post-filter to ensure only current repo (safeguard)
        final_results = self._filter_by_repo(final_results)
        
        self.logger.info(f"FINAL | Returning {len(final_results)} diverse chunks (requested: {retrieve_k})")

        # 🔥 Normalize metadata → promote fields to top-level for context builder + logs
        for r in final_results:
            # Use metadata normalizer for unified access
            meta_norm = MetadataNormalizer(r.get("metadata", {}), r)
            r["file_path"] = meta_norm.get_file_path()
            r["type"] = meta_norm.get_chunk_type()
            r["repo_name"] = meta_norm.get_repo_name()
            r["issue_number"] = meta_norm.get_issue_number()
            r["pr_number"] = meta_norm.get_pr_number()

        return final_results