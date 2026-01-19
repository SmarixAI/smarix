# retrieval.py
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import numpy as np
import pickle
import networkx as nx
from pathlib import Path
import json
from .query_type import QueryType

class GraphRetrievalMixin:
    def load_graph_structure(self):
        """Lazy load the NetworkX graph structure"""
        if hasattr(self, 'G') and self.G:
            return self.G
            
        graph_path = Path("../../data/VectorDB") / self.repo_owner / self.repo_name / "graph_structure.pkl"
        if graph_path.exists():
            try:
                with open(graph_path, 'rb') as f:
                    self.G = pickle.load(f)
                print(f"🕸️  Graph loaded: {self.G.number_of_nodes()} nodes")
                return self.G
            except Exception as e:
                print(f"⚠️ Failed to load graph structure: {e}")
        return None
    
    def _get_repo_filters(self) -> Optional[Dict[str, Any]]:
        """Get repo-based filters for VectorDB search - STRICT filtering by both owner and repo name"""
        repo_owner = getattr(self, 'repo_owner', None)
        repo_name = getattr(self, 'repo_name', None)
        
        if not repo_owner or not repo_name:
            return None
        
        # Return filter that matches BOTH owner and repo name
        return {"repo_name": repo_name, "repo_owner": repo_owner}
    
    def _filter_by_repo(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-retrieval filtering to ensure only current repo chunks are returned - STRICT filtering"""
        repo_owner = getattr(self, 'repo_owner', None)
        repo_name = getattr(self, 'repo_name', None)
        
        # If repo info not available, return empty (don't return results from unknown repos)
        if not repo_owner or not repo_name:
            if results:
                self.logger.warning(f"FILTER | No repo info available, filtering out {len(results)} results")
            return []
        
        filtered = []
        for result in results:
            metadata = result.get('metadata', {})
            chunk_repo = metadata.get('repo_name', '').strip()
            chunk_owner = metadata.get('repo_owner', '').strip()
            
            # STRICT matching: BOTH owner AND repo name must match
            # Accept if:
            # 1. Full format matches: "owner/repo" == "owner/repo"
            # 2. Both owner and repo name match separately
            matches = False
            
            # Check full format first
            if chunk_repo == f"{repo_owner}/{repo_name}":
                matches = True
            # Check separate owner and repo name (both must match)
            elif chunk_owner == repo_owner and chunk_repo == repo_name:
                matches = True
            # If repo_name is stored as just the name (without owner), check owner separately
            elif chunk_repo == repo_name and chunk_owner == repo_owner:
                matches = True
            
            if matches:
                filtered.append(result)
        
        if len(filtered) < len(results):
            self.logger.info(f"FILTER | Filtered {len(results)} -> {len(filtered)} results for repo {repo_owner}/{repo_name}")
        
        return filtered

    def retrieve_graph_context(self, query_embedding, top_k=5):
        """
        1. Search 'graph_nodes' index to find Entry Points.
        2. Traverse edges in NetworkX to find connected components.
        """
        G = self.load_graph_structure()
        if not G or not self.multi_index_store:
            return []

        # Step 1: Find Entry Nodes using Vector Search on 'graph_nodes' index
        entry_nodes = self.multi_index_store.search_by_type(
            query_embedding, 
            index_type='graph_nodes', 
            top_k=top_k
        )
        
        graph_results = []
        visited = set()

        for node_hit in entry_nodes:
            node_id = node_hit.get('chunk_id') or node_hit.get('metadata', {}).get('chunk_id')
            if not node_id or node_id not in G.nodes:
                continue
                
            if node_id in visited: continue
            visited.add(node_id)

            # Get Node Data
            node_data = G.nodes[node_id]
            
            # Step 2: Get Neighbors (Traverse 1-hop)
            # Incoming edges (Who calls me?)
            callers = []
            for u, v, attr in G.in_edges(node_id, data=True):
                if attr.get('type') == 'CALLS':
                    callers.append(u.split('::')[-1]) # Simplify ID to Name

            # Outgoing edges (Who do I call?)
            callees = []
            for u, v, attr in G.out_edges(node_id, data=True):
                if attr.get('type') == 'CALLS':
                    callees.append(v.split('::')[-1])

            # Format as a Text Chunk for the Context Window
            context_text = f"Entity: {node_data.get('label')} {node_data.get('name')}\n"
            if callers: context_text += f"Called By: {', '.join(callers[:5])}\n"
            if callees: context_text += f"Calls To: {', '.join(callees[:5])}\n"
            
            graph_results.append({
                "content": context_text,
                "metadata": {
                    "type": "graph_context",
                    "source": "dependency_graph",
                    "node_id": node_id
                },
                "score": node_hit.get('score', 1.0)
            })

        return graph_results

class RetrievalMixin(GraphRetrievalMixin):
    
    
    def retrieve_github_first(
        self,
        query_embedding: np.ndarray,
        query_type: str,
        entity: Optional[Dict[str, Any]] = None,
        keywords: List[str] = [],
        top_k: int = None,
        query_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve from GitHub database (single-index or multi-index).

        Args:
            query_embedding: Query embedding vector
            query_type: Query type classification
            entity: Optional entity filter
            keywords: Keywords for hybrid retrieval
            top_k: Override top_k
            query_text: Original query text (for routing in multi-index mode)
        """

        if query_type == "impact_analysis" and self.multi_index_store:
            print("Executing Graph Impact Analysis...")
            
            vector_results = self._retrieve_multi_index(query_embedding, query_type, entity, keywords, top_k, query_text)
            
            graph_results = self.retrieve_graph_context(query_embedding)
            
            return graph_results + vector_results

        # Multi-index mode → unchanged
        if self.multi_index_store:
            return self._retrieve_multi_index(query_embedding, query_type, entity, keywords, top_k, query_text)

       
        if query_type == "direct_id" and query_text:
            match = re.search(r'\b(?:issue|pr|ticket|bug|id)\s*#?\s*(\d+)\b', query_text.lower())
            if match:
                target_id = int(match.group(1))

                # Direct hit lookup (no embedding required)
                repo_filters = self._get_repo_filters()
                direct_results = []
                # Add repo filter to each search
                issue_filter = {"issue_number": target_id}
                pr_filter = {"pr_number": target_id}
                ticket_filter = {"ticket_number": target_id}
                
                if repo_filters:
                    issue_filter.update(repo_filters)
                    pr_filter.update(repo_filters)
                    ticket_filter.update(repo_filters)
                
                direct_results += self.db.search_by_metadata(filters=issue_filter, top_k=20) or []
                direct_results += self.db.search_by_metadata(filters=pr_filter, top_k=20) or []
                direct_results += self.db.search_by_metadata(filters=ticket_filter, top_k=20) or []

                # Semantic similarity for more context (with repo filtering)
                semantic_results = self.db.search(query_embedding, top_k=self.top_k * 2, filters=repo_filters)

                # Merge → direct hits should dominate
                merged = {}
                for r in direct_results:
                    cid = r.get("chunk_id", id(r))
                    r["score"] = r.get("score", 1) + 10   # huge boost for exact matches
                    merged[cid] = r

                for r in semantic_results:
                    cid = r.get("chunk_id", id(r))
                    if cid not in merged:
                        r["score"] = r.get("score", 1)
                        merged[cid] = r

                final = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
                return final[:self.top_k]

        # -------------------------------------------------------

        # Normal retrieve logic (unchanged)
        if query_type == QueryType.FLOW_ARCHITECTURE:
            retrieve_k = top_k or self.top_k * 6
        elif query_type in [QueryType.HOW_TO, QueryType.CODE_LOCATION]:
            retrieve_k = top_k or self.top_k * 4
        elif query_type in [QueryType.PR_ISSUE_TUTORIAL, QueryType.PR_ISSUE_CODING_QUESTION]:
            retrieve_k = top_k or self.top_k * 8
        elif query_type == QueryType.RANDOM_PR_GENERATOR:
            retrieve_k = top_k or self.top_k * 10
        else:
            retrieve_k = top_k or self.top_k * 3

        # If entity extracted (existing behaviour)
        if entity:
            repo_filters = self._get_repo_filters()
            entity_type = entity.get('type')
            if entity_type == 'issue':
                filters = {'issue_number': entity['number']}
                if repo_filters:
                    filters.update(repo_filters)
                results = self.db.search_by_metadata(query_embedding, filters=filters, top_k=10)
            elif entity_type == 'pr':
                filters = {'pr_number': entity['number']}
                if repo_filters:
                    filters.update(repo_filters)
                results = self.db.search_by_metadata(query_embedding, filters=filters, top_k=10)
            elif entity_type == 'commit':
                filters = {'sha': entity['sha']}
                if repo_filters:
                    filters.update(repo_filters)
                results = self.db.search_by_metadata(query_embedding, filters=filters, top_k=10)
            else:
                results = []

            if results:
                return results

        # Regular similarity search
        repo_filters = self._get_repo_filters()
        results = self.db.search(query_embedding, top_k=retrieve_k, filters=repo_filters)
        
        # CRITICAL: Post-filter to ensure only current repo (safeguard)
        results = self._filter_by_repo(results)

        # Hybrid metadata boost (unchanged)
        if self.use_hybrid_retrieval:
            results = self.boost_by_metadata(results, keywords, query_type)
            results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)

        return results[:self.top_k * 2]

    
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
        top3_indexes = []
        if query_text and hasattr(self, 'query_router'):
            try:
                top3_indexes = self.query_router.route_top3_indexes(query_text)
                self.logger.info(f"ROUTING | TOP-3 indexes: {[(idx, f'{conf:.2f}') for idx, conf in top3_indexes]}")
            except Exception as e:
                self.logger.warning(f"ROUTING | TOP-3 routing failed: {e}, using fallback")
                top3_indexes = [('code', 0.6), ('documentation', 0.4), ('pr', 0.3)]
        else:
            # 🚀 Fallback routing using LLM semantic reasoning instead of keywords
            if hasattr(self, "llm_manager"):
                try:
                    routing_prompt = f"""
                You are ranking search databases for a retrieval augmented GitHub chatbot.
                Available indexes: code, documentation, pr, issue, email, commit, repo_metrics, onboarding.
                Based on the query below, return the indexes in order of priority (most important first).
                Output ONLY a Python list. Example: ["email", "documentation", "code"]

                QUERY: {query_text}
                """
                    response = self.llm_manager.call_llm(
                        system_prompt="Rank priority search indexes for retrieval.",
                        user_prompt=routing_prompt
                    )

                    ranked = eval(response.strip()) if response.strip().startswith("[") else None

                    if ranked and isinstance(ranked, list):
                        # Convert to [('index', confidence), ...]
                        top3_indexes = [(idx, 1.0 - i * 0.15) for i, idx in enumerate(ranked[:3])]
                        self.logger.info(f"ROUTING | LLM priority: {top3_indexes}")
                    else:
                        raise Exception("LLM returned unexpected format")

                except Exception as e:
                    self.logger.warning(f"ROUTING | Semantic routing failed ({e}), using basic fallback")
                    # previous fallback with no change
                    if query_type in [QueryType.ISSUE_SPECIFIC, QueryType.PR_SPECIFIC]:
                        top3_indexes = [('pr', 0.8), ('code', 0.6), ('documentation', 0.4)]
                    elif query_type == QueryType.COMMIT_SPECIFIC:
                        top3_indexes = [('commit', 0.8), ('code', 0.6), ('pr', 0.4)]
                    elif query_type in [QueryType.HOW_TO, QueryType.CONCEPTUAL]:
                        top3_indexes = [('documentation', 0.8), ('code', 0.6), ('pr', 0.4)]
                    else:
                        top3_indexes = [('code', 0.7), ('documentation', 0.5), ('pr', 0.4)]

        adjusted_indexes = []
        for idx_name, conf in top3_indexes:
            if idx_name == 'impact_analysis':
                adjusted_indexes.append(('graph_nodes', conf)) # Map logical intent to physical index
                # Also ensure 'code' is present for context
                if not any(i[0] == 'code' for i in top3_indexes):
                    adjusted_indexes.append(('code', conf * 0.8))
            else:
                adjusted_indexes.append((idx_name, conf))
        top3_indexes = adjusted_indexes

        
        # Extract index types (ensure we have exactly 3)
        index_types = [idx for idx, _ in top3_indexes[:3]]
        if len(index_types) < 3:
            # Fill with defaults
            default_indexes = ['code', 'documentation', 'pr', 'email']
            for idx in default_indexes:
                if idx not in index_types and len(index_types) < 3:
                    index_types.append(idx)
        
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
        
        self.logger.info(f"RETRIEVAL | Total unique chunks retrieved: {len(unique_results)} (target: 15+)")
        
        if not unique_results:
            self.logger.warning("RETRIEVAL | No results found, returning empty list")
            return []
        
        # Filename keyword boost to help CODE_LOCATION find the right file
        if query_type == QueryType.CODE_LOCATION and query_text:
            normalized_query = query_text.lower().replace(" ", "").replace("_", "").replace("-", "")
            for r in unique_results:
                filename = (
                    r.get("metadata", {}).get("file_path") or
                    r.get("metadata", {}).get("file") or
                    r.get("metadata", {}).get("source") or 
                    r.get("metadata", {}).get("path") or ""
                ).lower()
                normalized_file = filename.replace(" ", "").replace("_", "").replace("-", "")
                if normalized_query in normalized_file or any(token in normalized_file for token in normalized_query.split()):
                    r["score"] = r.get("score", 0) + 4.0   # very strong boost


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
                metadata = result.get('metadata', {})
                if entity_type == 'issue' and metadata.get('issue_number') == entity.get('number'):
                    filtered_results.append(result)
                elif entity_type == 'pr' and metadata.get('pr_number') == entity.get('number'):
                    filtered_results.append(result)
                elif entity_type == 'commit' and metadata.get('sha', '').startswith(entity.get('sha', '')):
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
            m = r.get("metadata", {}) or {}
            r["file_path"] = m.get("file_path") or m.get("file") or m.get("path")
            r["type"] = m.get("type") or m.get("chunk_type")
            r["repo_name"] = m.get("repo_name")
            r["issue_number"] = m.get("issue_number")
            r["pr_number"] = m.get("pr_number")

        return final_results

    
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
                    from .query_type import QueryType
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

    def retrieve_gmail_correlated(
        self,
        github_results: List[Dict[str, Any]],
        query_embedding: np.ndarray,
        keywords: List[str] = []
    ) -> List[Dict[str, Any]]:
        if not self.gmail_db or not github_results:
            return []

        github_entities = {
            'authors': set(),
            'issue_numbers': set(),
            'pr_numbers': set()
        }

        for result in github_results[:5]:
            metadata = result.get('metadata', {})
            if metadata.get('author'):
                github_entities['authors'].add(metadata['author'].lower())
            if metadata.get('issue_number'):
                github_entities['issue_numbers'].add(str(metadata['issue_number']))
            if metadata.get('pr_number'):
                github_entities['pr_numbers'].add(str(metadata['pr_number']))

        gmail_results = self.gmail_db.search(query_embedding, top_k=20)

        correlated = []
        for email in gmail_results:
            metadata = email.get('metadata', {})

            if not metadata.get('is_git_related'):
                continue

            correlation = metadata.get('correlation_score', 0)
            correlated_entities = metadata.get('correlated_entities', {})

            entity_matches = 0
            for author in github_entities['authors']:
                if author in str(correlated_entities.get('correlated_authors', [])).lower():
                    entity_matches += 2

            for issue_num in github_entities['issue_numbers']:
                if issue_num in str(correlated_entities.get('correlated_issues', [])):
                    entity_matches += 3

            for pr_num in github_entities['pr_numbers']:
                if pr_num in str(correlated_entities.get('correlated_prs', [])):
                    entity_matches += 3

            if entity_matches > 0 or correlation > 3:
                email['relevance_score'] = correlation + entity_matches
                correlated.append(email)

        return sorted(correlated, key=lambda x: x.get('relevance_score', 0), reverse=True)[:5]

    def boost_by_metadata(self, results: List[Dict], keywords: List[str], query_type: str) -> List[Dict]:
        for result in results:
            metadata = result.get('metadata', {})
            score = result.get('score', 0)

            priority = metadata.get('retrieval_priority', 3)
            if priority == 1:
                score *= 1.3
            elif priority == 2:
                score *= 1.1

            # Try multiple fields for content
            full_content = (metadata.get('full_content') or metadata.get('content') or '').lower()
            keyword_matches = sum(1 for k in keywords if k.lower() in full_content)
            if keyword_matches > 0:
                score *= (1.0 + 0.1 * min(keyword_matches, 5))

            chunk_type = metadata.get('type', '')
            if query_type == QueryType.FLOW_ARCHITECTURE and chunk_type in ['documentation', 'analyzed_file']:
                score *= 1.2
            elif query_type == QueryType.TROUBLESHOOTING and chunk_type == 'issue':
                score *= 1.3
            elif query_type == QueryType.QUESTION_GENERATION and chunk_type in ['documentation', 'analyzed_file', 'code']:
                score *= 1.25
            elif query_type == QueryType.PR_ISSUE_TUTORIAL and chunk_type in ['pr', 'issue', 'code']:
                score *= 1.4
            elif query_type == QueryType.PR_ISSUE_CODING_QUESTION and chunk_type in ['pr', 'issue', 'code']:
                score *= 1.4
            elif query_type == QueryType.RANDOM_PR_GENERATOR and chunk_type == 'pr':
                score *= 2.0

            result['score'] = score

        return results

    def build_context_from_chunks(self, chunks: List[Dict], query_type: str) -> str:
        context_parts: List[str] = []

        if query_type == QueryType.FLOW_ARCHITECTURE:
            max_chunks = 15
        elif query_type in [QueryType.HOW_TO, QueryType.CODE_LOCATION, QueryType.QUESTION_GENERATION]:
            max_chunks = 10
        elif query_type in [QueryType.PR_ISSUE_TUTORIAL, QueryType.PR_ISSUE_CODING_QUESTION]:
            max_chunks = 20
        elif query_type == QueryType.RANDOM_PR_GENERATOR:
            max_chunks = 30
        else:
            max_chunks = 8

        for i, chunk in enumerate(chunks[:max_chunks], 1):
            metadata = chunk.get('metadata', {})

            context_parts.append(f"## Source {i}")
            
            # Handle both 'type' and 'source_type' fields
            chunk_type = metadata.get('type') or metadata.get('source_type') or metadata.get('chunk_type') or 'unknown'
            context_parts.append(f"Type: {chunk_type}")

            # Handle both 'file_path' and 'file' fields
            file_path = metadata.get('file_path') or metadata.get('file') or metadata.get('source')
            if file_path:
                context_parts.append(f"File: {file_path}")

            if metadata.get('line_start') and metadata.get('line_end'):
                context_parts.append(f"Lines: {metadata['line_start']}-{metadata['line_end']}")

            if metadata.get('issue_number'):
                context_parts.append(f"Issue: #{metadata['issue_number']}")
            if metadata.get('pr_number'):
                context_parts.append(f"PR: #{metadata['pr_number']}")
            if metadata.get('author'):
                context_parts.append(f"Author: {metadata['author']}")
            if metadata.get('title'):
                context_parts.append(f"Title: {metadata['title']}")

            # Try multiple fields for content (full_content, content, or from chunk)
            content = metadata.get('full_content') or metadata.get('content') or chunk.get('content', '')
            if content:
                if query_type == QueryType.FLOW_ARCHITECTURE:
                    max_length = 5000
                elif query_type in [QueryType.HOW_TO, QueryType.CODE_LOCATION, QueryType.CONCEPTUAL, QueryType.QUESTION_GENERATION]:
                    max_length = 3500
                elif query_type in [QueryType.PR_ISSUE_TUTORIAL, QueryType.PR_ISSUE_CODING_QUESTION]:
                    max_length = 6000
                elif query_type == QueryType.RANDOM_PR_GENERATOR:
                    max_length = 2000
                elif query_type == QueryType.TROUBLESHOOTING:
                    max_length = 2500
                else:
                    max_length = 2000

                if len(content) <= max_length * 1.1:
                    context_parts.append(f"\nContent:\n{content}")
                else:
                    truncated = content[:max_length]

                    last_newline = truncated.rfind('\n\n')
                    if last_newline > int(max_length * 0.8):
                        truncated = truncated[:last_newline]
                    elif truncated.rfind('\n') > int(max_length * 0.9):
                        truncated = truncated[:truncated.rfind('\n')]

                    context_parts.append(f"\nContent:\n{truncated}\n... (truncated, {len(content) - len(truncated)} chars omitted)")

            context_parts.append("\n" + "=" * 60 + "\n")

        return "\n".join(context_parts)

    def build_email_context(self, emails: List[Dict]) -> str:
        email_parts = ["## Related Email Discussions\n"]

        for i, email in enumerate(emails[:3], 1):
            metadata = email.get('metadata', {})

            email_parts.append(f"### Email {i}")
            email_parts.append(f"Subject: {metadata.get('subject', 'No subject')}")
            email_parts.append(f"From: {metadata.get('from', 'Unknown')}")
            email_parts.append(f"Date: {metadata.get('date', 'Unknown')}")

            if metadata.get('correlated_issues'):
                try:
                    email_parts.append(f"Related Issues: {', '.join(metadata['correlated_issues'][:3])}")
                except Exception:
                    pass
            if metadata.get('correlated_prs'):
                try:
                    email_parts.append(f"Related PRs: {', '.join(metadata['correlated_prs'][:3])}")
                except Exception:
                    pass

            # Try multiple fields for content
            content = metadata.get('full_content') or metadata.get('content') or ''
            if content:
                if len(content) > 800:
                    content = content[:800] + "\n... (truncated)"
                email_parts.append(f"\nContent:\n{content}")

            email_parts.append("\n" + "-" * 60 + "\n")

        return "\n".join(email_parts)

    def build_metrics_context(self) -> str:
        if not self.repo_metrics:
            return ""

        repositories = self.repo_metrics.get('repositories', {})
        if not repositories:
            return ""

        # Use current repo if available, otherwise use first repo in dict
        repo_owner = getattr(self, 'repo_owner', None)
        repo_name = getattr(self, 'repo_name', None)
        repo_key = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else None
        
        # Try to get current repo data first
        if repo_key and repo_key in repositories:
            repo_data = repositories[repo_key]
            display_name = repo_key
        else:
            # Fallback to first repo (for backward compatibility)
            repo_key = list(repositories.keys())[0]
            repo_data = repositories[repo_key]
            display_name = repo_key

        context_parts: List[str] = ["## REPOSITORY METRICS DATA\n"]
        context_parts.append(f"Repository: {display_name}\n")

        metrics = repo_data.get('metrics', {})
        if metrics:
            context_parts.append("### Code Statistics:")
            context_parts.append(f"- Total Files: {metrics.get('total_files', 0)}")
            context_parts.append(f"- Total Lines: {metrics.get('total_lines', 0)}")
            context_parts.append(f"- Code Lines: {metrics.get('total_code_lines', 0)}")
            context_parts.append(f"- Comment Lines: {metrics.get('total_comment_lines', 0)}")
            context_parts.append(f"- Blank Lines: {metrics.get('total_blank_lines', 0)}")
            context_parts.append(f"- Code-to-Comment Ratio: {metrics.get('code_to_comment_ratio', 0):.2f}\n")

        func_class = repo_data.get('functions_and_classes', {})
        if func_class:
            context_parts.append("### Functions & Classes:")
            context_parts.append(f"- Total Functions: {func_class.get('total_functions', 0)}")
            context_parts.append(f"- Total Classes: {func_class.get('total_classes', 0)}")
            context_parts.append(f"- Average Function Length: {func_class.get('average_function_length', 0):.2f} lines")

            funcs_by_lang = func_class.get('functions_by_language', {})
            classes_by_lang = func_class.get('classes_by_language', {})

            if funcs_by_lang or classes_by_lang:
                context_parts.append("\nBy Language:")
                all_langs = set(list(funcs_by_lang.keys()) + list(classes_by_lang.keys()))
                for lang in sorted(all_langs):
                    funcs = funcs_by_lang.get(lang, 0)
                    classes = classes_by_lang.get(lang, 0)
                    context_parts.append(f"  - {lang.capitalize()}: {funcs} functions, {classes} classes")
            context_parts.append("")

        languages = repo_data.get('languages', {})
        if languages:
            all_langs = languages.get('all', {})
            primary = languages.get('primary', '')

            context_parts.append("### Programming Languages:")
            if primary:
                context_parts.append(f"- Primary: {primary.capitalize()}")

            if all_langs:
                context_parts.append("- All Languages:")
                sorted_langs = sorted(all_langs.items(), key=lambda x: x[1], reverse=True)
                for lang, count in sorted_langs:
                    context_parts.append(f"  - {lang.capitalize()}: {count} files")
            context_parts.append("")

        frameworks = repo_data.get('frameworks', {})
        if frameworks:
            detected = frameworks.get('detected', [])
            usage = frameworks.get('usage', {})

            if detected:
                context_parts.append("### Frameworks & Libraries:")
                for fw in detected:
                    use_count = usage.get(fw, 0)
                    context_parts.append(f"- {fw.capitalize()}: {use_count} occurrences")
                context_parts.append("")

        tools = repo_data.get('tools', {})
        if tools:
            detected = tools.get('detected', [])
            categories = tools.get('categories', {})

            if detected:
                context_parts.append("### Development Tools:")
                for tool in detected:
                    context_parts.append(f"- {tool}")

                if categories:
                    for category, tool_list in categories.items():
                        cat_name = category.replace('_', ' ').title()
                        context_parts.append(f"  {cat_name}: {', '.join(tool_list)}")
                context_parts.append("")

        structure = repo_data.get('structure', {})
        if structure:
            dir_count = structure.get('directory_count', 0)
            max_depth = structure.get('max_depth', 0)
            root_files = structure.get('root_files', [])
            directories = structure.get('directories', [])
            src_paths = structure.get('src_paths', [])
            test_paths = structure.get('test_paths', [])
            config_paths = structure.get('config_paths', [])

            context_parts.append("### Repository Structure:")
            context_parts.append(f"- Total Directories: {dir_count}")
            context_parts.append(f"- Maximum Depth: {max_depth} levels")

            if root_files:
                context_parts.append(f"\nRoot Configuration Files ({len(root_files)}): {', '.join(root_files)}")

            if directories:
                context_parts.append(f"\nAll Directories ({len(directories)}):")
                for directory in directories[:30]:
                    context_parts.append(f"  - {directory}/")

            if src_paths:
                context_parts.append(f"\nSource Files ({len(src_paths)} total):")
                context_parts.append("Examples:")
                for path in src_paths[:10]:
                    context_parts.append(f"  - {path}")

            if test_paths:
                context_parts.append(f"\nTest Files ({len(test_paths)} total):")
                context_parts.append("Examples:")
                for path in test_paths[:5]:
                    context_parts.append(f"  - {path}")

            if config_paths:
                context_parts.append(f"\nConfiguration Files ({len(config_paths)} total):")
                context_parts.append("Examples:")
                for path in config_paths[:5]:
                    context_parts.append(f"  - {path}")

        return "\n".join(context_parts)

    def find_chronological_entity(
        self,
        entity_type: str,
        order: str,
        query_embedding: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        Find first/last issue/PR (DEPRECATED - only works with single-index).
        For multi-index, use entity extraction from query instead.
        """
        
        
        # Support both legacy single-index and new multi-index
        db = getattr(self, "db", None)

        if db is None:
            # Multi-index mode → chronological queries not supported
            return None

        repo_filters = self._get_repo_filters()
        results = self.db.search(query_embedding, top_k=100, filters=repo_filters)

        matching_entities = []
        for result in results:
            metadata = result.get('metadata', {})
            chunk_type = metadata.get('type', '')

            if entity_type == 'issue' and chunk_type == 'issue':
                issue_num = metadata.get('issue_number')
                if issue_num:
                    matching_entities.append({
                        'number': issue_num,
                        'result': result
                    })
            elif entity_type == 'pr' and chunk_type == 'pr':
                pr_num = metadata.get('pr_number')
                if pr_num:
                    matching_entities.append({
                        'number': pr_num,
                        'result': result
                    })

        if not matching_entities:
            return None

        matching_entities.sort(key=lambda x: x['number'])

        if order == 'first':
            target = matching_entities[0]
        else:
            target = matching_entities[-1]

        target_number = target['number']

        if entity_type == 'issue':
            filters = {'issue_number': target_number}
            if repo_filters:
                filters.update(repo_filters)
            specific_results = self.db.search_by_metadata(
                query_embedding,
                filters=filters,
                top_k=5
            )
        else:
            filters = {'pr_number': target_number}
            if repo_filters:
                filters.update(repo_filters)
            specific_results = self.db.search_by_metadata(
                query_embedding,
                filters=filters,
                top_k=5
            )

        if specific_results:
            return {
                'type': entity_type,
                'number': target_number,
                'results': specific_results
            }

        return None

    def generate_no_context_response(self, query: str, query_type: str) -> str:
        response = "I couldn't find relevant information in the indexed codebase to answer your question.\n\n"

        response += "### Possible Reasons:\n"
        response += "- The information may not be indexed yet\n"
        response += "- Try rephrasing with different keywords\n\n"

        response += "### What I Can Help With:\n"
        response += "- Repository metrics: 'Show me repo metrics', 'Lines of code?'\n"
        response += "- Tech stack: 'What technologies are used?'\n"
        response += "- Structure: 'Repository structure?', 'Diagram of repo structure?'\n"
        response += "- Architecture: 'Architecture of notifications service?'\n"
        response += "- Specific issues/PRs: 'Issue #123', 'First issue', 'Last PR'\n"
        response += "- Code locations: 'Where is authentication?'\n"

        if self.repo_info.get('total_chunks', 0) > 0:
            response += f"\n### Available Data:\n"
            response += f"- Indexed chunks: {self.repo_info['total_chunks']}\n"
            if self.gmail_db:
                try:
                    response += f"- Indexed emails: {self.gmail_db.index.ntotal}\n"
                except Exception:
                    response += "- Indexed emails: (unknown)\n"
            if self.repo_metrics:
                response += f"- Repository metrics: Available\n"

        return response

    def load_repo_info(self) -> Dict[str, Any]:
        """
        Load repository information from database or multi-index store.
        Extracts repository name from path, metadata, or config files.
        """
        stats = {'total_vectors': 0}
        repo_name = None
        
        # Try to get stats and repo name from multi-index store first
        if self.multi_index_store:
            try:
                stats = self.multi_index_store.get_statistics()
                
                # Try to get repo name from metadata in any index
                for index_type in ['code', 'documentation', 'pr', 'email']:
                    index_db = self.multi_index_store.indices.get(index_type)
                    if index_db and hasattr(index_db, 'metadata') and index_db.metadata:
                        try:
                            # Check first few metadata entries for repo name
                            for meta in index_db.metadata[:10]:
                                if isinstance(meta, dict):
                                    # Look for repo_name, repository, repo, or file_path that might contain repo name
                                    potential_name = (meta.get('repo_name') or 
                                                     meta.get('repository') or 
                                                     meta.get('repo') or
                                                     meta.get('source'))
                                    
                                    # Also check file_path for repo-like patterns
                                    if not potential_name:
                                        file_path = meta.get('file_path') or meta.get('file') or meta.get('source')
                                        if file_path:
                                            # Extract repo name from file path (e.g., CCExtractor_taskwarrior-flutter_data/...)
                                            import re
                                            match = re.search(r'([A-Z][A-Za-z0-9_-]+(?:[_-][A-Za-z0-9_-]+)*)', str(file_path))
                                            if match:
                                                potential_name = match.group(1)
                                    
                                    if potential_name and potential_name.lower() not in ['data', 'vectordb', 'multi_index', 'vector_db', 'backend', 'core']:
                                        repo_name = potential_name
                                        break
                            if repo_name:
                                break
                        except Exception as e:
                            self.logger.debug(f"Error accessing metadata from {index_type}: {e}")
                            continue
                
                # If not found in metadata, try to extract from path
                if not repo_name:
                    path_str = str(self.vector_db_path)
                    # Look for patterns like CCExtractor_taskwarrior-flutter_data in path
                    import re
                    # Match repository-like names (alphanumeric with underscores/hyphens)
                    matches = re.findall(r'([A-Z][A-Za-z0-9_-]+(?:[_-][A-Za-z0-9_-]+)*)', path_str)
                    for match in matches:
                        # Skip generic directory names
                        if match.lower() not in ['data', 'vectordb', 'multi_index', 'vector_db', 'backend', 'core']:
                            repo_name = match
                            break
                
            except Exception as e:
                self.logger.warning(f"Failed to get multi-index stats: {e}")
        
        
        
        # Clean up the repo name
        if repo_name:
            # Remove common prefixes/suffixes
            repo_name = repo_name.replace('_unknown_chunks', '').replace('_chunks', '')
            repo_name = repo_name.replace('_embeddings', '').replace('_git', '')
            repo_name = repo_name.replace('.faiss', '').replace('_db', '')
            
            # Skip if it's still a generic name
            if repo_name.lower() in ['data', 'vectordb', 'multi_index', 'vector_db', 'backend', 'core', 'no-github-db']:
                repo_name = None
        
        # Final fallback
        if not repo_name or repo_name == 'no-github-db':
            repo_name = 'this repository'
        else:
            # Format the name nicely (replace underscores/hyphens with spaces, capitalize)
            repo_name = repo_name.replace('_', ' ').replace('-', ' ')
            # Capitalize first letter of each word, but preserve acronyms
            words = repo_name.split()
            formatted_words = []
            for word in words:
                # If it's all caps (acronym), keep it
                if word.isupper() and len(word) > 1:
                    formatted_words.append(word)
                else:
                    formatted_words.append(word.capitalize())
            repo_name = ' '.join(formatted_words)
        
        return {
            'name': repo_name,
            'total_chunks': stats.get('total_vectors', 0)
        }

    def load_repository_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Load repository metrics/tech stack for the CURRENT repo.
        Uses ONLY repo-specific files from the standard location.
        No hardcoded paths, no fallbacks, no environment overrides.
        
        Location: DataProcessing/{owner}/{repo}/techstack.json
        Repo info comes from chatbot attributes or runtime_state.json
        
        Returns None if repo-specific file not found.
        """
        # Get current repo info
        repo_owner = getattr(self, 'repo_owner', None)
        repo_name = getattr(self, 'repo_name', None)
        
        # Try to load from runtime_state.json if repo info not available
        if not repo_owner or not repo_name:
            try:
                possible_state_files = [
                    Path(__file__).resolve().parents[3] / "data" / "Admin" / "state" / "runtime_state.json",
                    Path("../../data/Admin/state/runtime_state.json"),
                    Path("data/Admin/state/runtime_state.json"),
                    Path("backend/data/Admin/state/runtime_state.json"),
                ]
                
                for state_file in possible_state_files:
                    if state_file.exists():
                        with open(state_file, 'r', encoding='utf-8') as f:
                            state = json.load(f)
                            curr_repo = state.get("curr_repo", {})
                            repo_owner = curr_repo.get("owner") or repo_owner
                            repo_name = curr_repo.get("name") or repo_name
                            if repo_owner and repo_name:
                                break
            except Exception as e:
                if self.verbose:
                    print(f"Could not load repo from runtime_state.json: {e}")
        
        # PRIORITY 1: Repo-specific techstack.json file
        if repo_owner and repo_name:
            repo_specific_paths = [
                Path(__file__).resolve().parents[3] / "data" / "DataProcessing" / repo_owner / repo_name / "techstack.json",
                Path("../../data/DataProcessing") / repo_owner / repo_name / "techstack.json",
                Path("data/DataProcessing") / repo_owner / repo_name / "techstack.json",
                Path("backend/data/DataProcessing") / repo_owner / repo_name / "techstack.json",
            ]
            
            for path in repo_specific_paths:
                if path.exists():
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            metrics = json.load(f)
                            # Wrap in expected format
                            result = {
                                'repositories': {f"{repo_owner}/{repo_name}": metrics},
                                'summary': metrics  # Use repo-specific metrics as summary
                            }
                            if self.verbose:
                                print(f"✅ Loaded repo-specific metrics from: {path}")
                            return result
                    except Exception as e:
                        if self.verbose:
                            print(f"Error loading repo-specific metrics from {path}: {e}")
                        continue
        
        # No fallbacks - only use repo-specific files from the standard location
        if self.verbose:
            repo_display = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else "unknown"
            print(f"❌ No repository metrics file found for repo: {repo_display}")
            print(f"   Expected location: data/DataProcessing/{repo_owner}/{repo_name}/techstack.json")
            print(f"   Run data processing to generate this file for the current repo.")

        return None

    def retrieve_with_multi_query(
        self,
        queries: List[str],
        query_type: str,
        entity: Optional[Dict[str, Any]] = None,
        keywords: List[str] = [],
        query_text: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks using multiple query variations and merge results
        """
        all_results: Dict[Any, Dict[str, Any]] = {}

        for i, q in enumerate(queries, 1):
            self.logger.info(f"MULTI-QUERY RETRIEVAL {i}/{len(queries)} | Searching with: {q[:50]}...")

            query_embedding = self.get_query_embedding(q)
            results = self.retrieve_github_first(
                query_embedding, query_type, entity, keywords, query_text=q
            )

            for result in results:
                chunk_id = result.get('metadata', {}).get('chunk_id', id(result))

                if chunk_id in all_results:
                    all_results[chunk_id]['score'] = max(all_results[chunk_id]['score'], result.get('score', 0))
                    all_results[chunk_id]['query_matches'] += 1
                else:
                    result['query_matches'] = 1
                    all_results[chunk_id] = result

        merged_results = list(all_results.values())

        for result in merged_results:
            result['score'] = result.get('score', 0) * (1.0 + 0.1 * result.get('query_matches', 1))

        merged_results = sorted(merged_results, key=lambda x: x.get('score', 0), reverse=True)

        self.logger.info(f"MULTI-QUERY MERGE | Total unique chunks: {len(merged_results)}")

        return merged_results[:self.top_k * 2]
