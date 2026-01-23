"""
Modular retrieval system for RAG chatbot.

This package provides a modular retrieval system split into focused components:
- repo_utils: Repository filtering utilities
- graph_retrieval: Graph-based retrieval from dependency graphs
- query_routing: Query routing to appropriate indexes
- multi_index_retrieval: Multi-index retrieval strategy
- reranking: Cross-encoder reranking and diversity selection
- context_builder: Context building from retrieval results
- gmail_correlation: Gmail correlation with GitHub results
- repository_info: Repository information and metrics loading
"""
import re
from typing import List, Dict, Any, Optional
import numpy as np

from .repo_utils import RepoFilterMixin
from .graph_retrieval import GraphRetrievalMixin
from .query_routing import QueryRoutingMixin
from .multi_index_retrieval import MultiIndexRetrievalMixin
from .reranking import RerankingMixin
from .context_builder import ContextBuilderMixin
from .gmail_correlation import GmailCorrelationMixin
from .repository_info import RepositoryInfoMixin
from ..query_type import QueryType


class RetrievalMixin(
    RepoFilterMixin,
    GraphRetrievalMixin,
    QueryRoutingMixin,
    MultiIndexRetrievalMixin,
    RerankingMixin,
    ContextBuilderMixin,
    GmailCorrelationMixin,
    RepositoryInfoMixin
):
    """Main retrieval mixin that composes all retrieval components."""
    
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

        # -------------------------------------------------------
        # CODE_LOCATION: Try code_chunks_loader first (exact filename + path), then vector search if not found
        # This must happen BEFORE multi-index routing to avoid unnecessary processing
        if query_type == QueryType.CODE_LOCATION and query_text:
            self.logger.info(f"CODE_LOCATION | Processing code location query: {query_text}")
            
            # Detect file query intent
            file_intent = self._detect_file_query_intent(query_text, keywords)
            file_paths = file_intent.get('file_paths', [])
            filename_hints = file_intent.get('filename_hints', [])
            
            # Try code_chunks_loader first with exact filename + path
            code_loader = self._get_code_chunks_loader()
            if code_loader:
                repo_owner = getattr(self, 'repo_owner', None)
                repo_name = getattr(self, 'repo_name', None)
                
                results = []
                seen_chunk_ids = set()
                
                # Try exact file paths first
                if file_paths:
                    self.logger.info(f"CODE_LOCATION | Searching code_chunks_loader for {len(file_paths)} file paths: {file_paths}")
                    for file_path in file_paths:
                        # Try by full path with exact match first
                        chunks = code_loader.get_chunks_by_file_path(
                            file_path,
                            repo_owner,
                            repo_name,
                            exact_match_only=True  # Exact match only for code location queries
                        )
                        
                        # If no exact match, try without exact_match_only (partial match)
                        if not chunks:
                            self.logger.info(
                                f"CODE_LOCATION | No exact match for path '{file_path}', trying partial match"
                            )
                            chunks = code_loader.get_chunks_by_file_path(
                                file_path,
                                repo_owner,
                                repo_name,
                                exact_match_only=False  # Allow partial matches
                            )
                        
                        # If still no results, try by filename (in case user only provided filename)
                        if not chunks and filename_hints:
                            from utils.path_normalizer import extract_filename
                            filename = extract_filename(file_path)
                            if filename:
                                self.logger.info(
                                    f"CODE_LOCATION | No results for path '{file_path}', "
                                    f"trying filename search: '{filename}'"
                                )
                                chunks = code_loader.get_chunks_by_filename(
                                    filename,
                                    repo_owner,
                                    repo_name
                                )
                        
                        self.logger.info(
                            f"CODE_LOCATION | File path '{file_path}': found {len(chunks)} chunks from code_chunks_loader"
                        )
                        
                        # Convert chunks to expected format
                        for chunk in chunks:
                            chunk_id = chunk.get('chunk_id')
                            if chunk_id and chunk_id not in seen_chunk_ids:
                                seen_chunk_ids.add(chunk_id)
                                
                                # Extract content from code_chunks.json format
                                content = chunk.get('content', {})
                                if isinstance(content, dict):
                                    content_text = content.get('content', '')
                                    if not content_text:
                                        raw_data = chunk.get('raw_data', {})
                                        if isinstance(raw_data, dict):
                                            content_text = raw_data.get('content', '')
                                    if not content_text:
                                        content_text = str(content)
                                else:
                                    content_text = str(content) if content else ''
                                
                                # Build metadata in expected format - get file_path from chunk directly or from metadata
                                chunk_metadata = chunk.get('metadata', {})
                                if not chunk_metadata:
                                    from utils.metadata_normalizer import MetadataNormalizer
                                    meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                                    chunk_type = meta_norm.get_chunk_type('')
                                    
                                    # Get file_path from chunk directly first, then from metadata
                                    file_path = chunk.get('file_path', '') or meta_norm.get_file_path('')
                                    
                                    chunk_metadata = {
                                        'file_path': file_path,
                                        'filename': chunk.get('filename', '') or meta_norm.get_filename(''),
                                        'directory': chunk.get('directory', '') or meta_norm.get_directory(''),
                                        'chunk_type': chunk_type,
                                        'repo_name': chunk.get('repo_name', '') or meta_norm.get_repo_name(''),
                                        'repo_owner': chunk.get('repo_owner', '') or meta_norm.get_repo_owner(''),
                                        'language': chunk.get('language', '') or meta_norm.get_language(''),
                                    }
                                else:
                                    # If metadata exists, ensure file_path is set
                                    if 'file_path' not in chunk_metadata or not chunk_metadata.get('file_path'):
                                        chunk_metadata['file_path'] = chunk.get('file_path', '')
                                
                                result_dict = {
                                    'chunk_id': chunk_id,
                                    'metadata': chunk_metadata,
                                    'content': content_text,
                                    'score': 10.0,  # High score for exact file matches
                                    'source': 'code_chunks_loader',
                                    'match_type': 'exact_file_match'
                                }
                                
                                # Preserve ambiguity flags if present (CRITICAL for ambiguity detection)
                                if chunk.get('_ambiguous_filename'):
                                    result_dict['_ambiguous_filename'] = True
                                    result_dict['_all_matching_paths'] = chunk.get('_all_matching_paths', [])
                                    self.logger.info(
                                        f"CODE_LOCATION | Preserving ambiguity flags for chunk {chunk_id}: "
                                        f"filename={chunk.get('filename', 'unknown')}, "
                                        f"paths={chunk.get('_all_matching_paths', [])}"
                                    )
                                
                                results.append(result_dict)
                
                # Try filename hints if no results from file paths
                if not results and filename_hints:
                    self.logger.info(
                        f"CODE_LOCATION | No results from exact paths, trying filename hints: {filename_hints}"
                    )
                    for filename_hint in filename_hints:
                        chunks = code_loader.get_chunks_by_filename(
                            filename_hint,
                            repo_owner,
                            repo_name
                        )
                        
                        self.logger.info(
                            f"CODE_LOCATION | Filename hint '{filename_hint}': found {len(chunks)} chunks"
                        )
                        
                        for chunk in chunks:
                            chunk_id = chunk.get('chunk_id')
                            if chunk_id and chunk_id not in seen_chunk_ids:
                                seen_chunk_ids.add(chunk_id)
                                
                                # Extract content
                                content = chunk.get('content', {})
                                if isinstance(content, dict):
                                    content_text = content.get('content', '')
                                    if not content_text:
                                        raw_data = chunk.get('raw_data', {})
                                        if isinstance(raw_data, dict):
                                            content_text = raw_data.get('content', '')
                                    if not content_text:
                                        content_text = str(content)
                                else:
                                    content_text = str(content) if content else ''
                                
                                # Build metadata - get file_path from chunk directly or from metadata
                                chunk_metadata = chunk.get('metadata', {})
                                if not chunk_metadata:
                                    from utils.metadata_normalizer import MetadataNormalizer
                                    meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                                    chunk_type = meta_norm.get_chunk_type('')
                                    
                                    # Get file_path from chunk directly first, then from metadata, then from entities/content
                                    from utils.path_normalizer import extract_filename
                                    file_path = (
                                        chunk.get('file_path', '') or 
                                        meta_norm.get_file_path('') or
                                        chunk.get('entities', {}).get('path', '') or
                                        chunk.get('content', {}).get('file_path', '')
                                    )
                                    
                                    chunk_metadata = {
                                        'file_path': file_path,
                                        'filename': chunk.get('filename', '') or meta_norm.get_filename('') or (extract_filename(file_path) if file_path else ''),
                                        'directory': chunk.get('directory', '') or meta_norm.get_directory(''),
                                        'chunk_type': chunk_type,
                                        'repo_name': chunk.get('repo_name', '') or meta_norm.get_repo_name(''),
                                        'repo_owner': chunk.get('repo_owner', '') or meta_norm.get_repo_owner(''),
                                        'language': chunk.get('language', '') or meta_norm.get_language(''),
                                    }
                                else:
                                    # If metadata exists, ensure file_path is set from chunk if missing
                                    if 'file_path' not in chunk_metadata or not chunk_metadata.get('file_path'):
                                        chunk_metadata['file_path'] = (
                                            chunk.get('file_path', '') or
                                            chunk.get('entities', {}).get('path', '') or
                                            chunk.get('content', {}).get('file_path', '')
                                        )
                                
                                result_dict = {
                                    'chunk_id': chunk_id,
                                    'metadata': chunk_metadata,
                                    'content': content_text,
                                    'score': 9.0,  # Slightly lower than exact path match
                                    'source': 'code_chunks_loader',
                                    'match_type': 'exact_filename_match'
                                }
                                
                                # Also set file_path directly on result_dict for easier access
                                if chunk_metadata.get('file_path'):
                                    result_dict['file_path'] = chunk_metadata['file_path']
                                
                                # Preserve ambiguity flags if present (CRITICAL for ambiguity detection)
                                if chunk.get('_ambiguous_filename'):
                                    result_dict['_ambiguous_filename'] = True
                                    result_dict['_all_matching_paths'] = chunk.get('_all_matching_paths', [])
                                    self.logger.warning(
                                        f"CODE_LOCATION | AMBIGUITY DETECTED - Preserving ambiguity flags for chunk {chunk_id}: "
                                        f"filename={chunk.get('filename', chunk_metadata.get('filename', 'unknown'))}, "
                                        f"file_path={chunk_metadata.get('file_path', 'unknown')}, "
                                        f"paths={chunk.get('_all_matching_paths', [])}"
                                    )
                                
                                results.append(result_dict)
                
                # If found results from code_chunks_loader, return immediately (no vector search, no routing, no reranking)
                if results:
                    # 🚨 CHECK FOR AMBIGUITY, but first check if user provided a full path
                    if any(r.get("_ambiguous_filename") for r in results):
                        # Get filename and paths from first result
                        first_result = results[0]
                        filename = first_result.get("metadata", {}).get("filename", "")
                        if not filename:
                            # Try to extract from file_path
                            file_path = first_result.get("metadata", {}).get("file_path", "") or first_result.get("file_path", "")
                            if file_path:
                                from utils.path_normalizer import extract_filename
                                filename = extract_filename(file_path)
                        
                        paths = first_result.get("_all_matching_paths", [])
                        
                        if not filename and paths:
                            # Extract filename from first path
                            from utils.path_normalizer import extract_filename
                            filename = extract_filename(paths[0]) if paths else "unknown"
                        
                        # 🚨 CRITICAL: Check if user provided a full path in the query
                        # If they did, filter results to only that path and return normally (not ambiguous)
                        if query_text:
                            from utils.path_normalizer import normalize_path
                            
                            # Normalize query to handle different formats
                            query_normalized = normalize_path(query_text, '').lower().replace('\\', '/').strip('/')
                            
                            # Check if query contains any of the ambiguous paths
                            matching_path = None
                            for path in paths:
                                path_normalized = normalize_path(path, '').lower().replace('\\', '/').strip('/')
                                
                                # More robust matching:
                                # 1. Exact match (after normalization)
                                # 2. Query ends with path
                                # 3. Path ends with query (partial path provided)
                                # 4. Either contains the other (substring match)
                                if (path_normalized == query_normalized or
                                    query_normalized.endswith('/' + path_normalized) or
                                    query_normalized.endswith(path_normalized) or
                                    path_normalized.endswith('/' + query_normalized) or
                                    path_normalized.endswith(query_normalized) or
                                    path_normalized in query_normalized or
                                    query_normalized in path_normalized):
                                    matching_path = path
                                    self.logger.info(
                                        f"CODE_LOCATION | User specified full path in query: '{query_text}' matches '{path}' "
                                        f"(normalized: '{query_normalized}' == '{path_normalized}'), "
                                        f"filtering results to this path only"
                                    )
                                    break
                            
                            # If user specified a path, filter results to only that path
                            if matching_path:
                                matching_path_normalized = normalize_path(matching_path, '').lower().replace('\\', '/').strip('/')
                                filtered_results = []
                                for result in results:
                                    result_path = result.get("metadata", {}).get("file_path", "") or result.get("file_path", "")
                                    if result_path:
                                        result_path_normalized = normalize_path(result_path, '').lower().replace('\\', '/').strip('/')
                                        
                                        # Match if paths are the same after normalization
                                        if (result_path_normalized == matching_path_normalized or
                                            result_path_normalized.endswith('/' + matching_path_normalized) or
                                            result_path_normalized.endswith(matching_path_normalized) or
                                            matching_path_normalized.endswith('/' + result_path_normalized) or
                                            matching_path_normalized.endswith(result_path_normalized)):
                                            # Remove ambiguity flags since we're filtering to one path
                                            result.pop("_ambiguous_filename", None)
                                            result.pop("_all_matching_paths", None)
                                            filtered_results.append(result)
                                
                                if filtered_results:
                                    self.logger.info(
                                        f"CODE_LOCATION | Filtered {len(filtered_results)} chunks for specified path '{matching_path}' "
                                        f"(from {len(results)} ambiguous chunks)"
                                    )
                                    return filtered_results[:self.top_k * 2]
                                else:
                                    self.logger.warning(
                                        f"CODE_LOCATION | User specified path '{matching_path}' but no matching chunks found. "
                                        f"This might indicate a path mismatch."
                                    )
                        
                        # No matching path found in query, return ambiguity
                        self.logger.warning(
                            f"CODE_LOCATION | Ambiguous filename detected — stopping retrieval before context building. "
                            f"Filename: '{filename}', {len(paths)} paths found. User query: '{query_text}'"
                        )
                        return [{
                            "__ambiguous__": True,
                            "filename": filename or "unknown",
                            "paths": paths
                        }]

                    return results[:self.top_k * 2]

            
            # If code_chunks_loader didn't find results, do simple vector search
            # Skip multi-index routing and complex file index merging
            self.logger.info(
                f"CODE_LOCATION | No results from code_chunks_loader, doing simple vector search"
            )
            
            # Simple vector search - search 'code' index directly in multi-index mode, or regular db in single-index mode
            retrieve_k = top_k or self.top_k * 4
            repo_filters = self._get_repo_filters()
            
            if self.multi_index_store:
                # Multi-index mode: search 'code' index directly (no routing, no reranking)
                code_index = self.multi_index_store.indices.get('code')
                if code_index:
                    vector_results = code_index.search(query_embedding, top_k=retrieve_k)
                    vector_results = self._filter_by_repo(vector_results)
                    self.logger.info(f"CODE_LOCATION | Found {len(vector_results)} results from 'code' index")
                    return vector_results[:self.top_k * 2]
                else:
                    self.logger.warning("CODE_LOCATION | 'code' index not found in multi-index store")
                    return []
            else:
                # Single-index mode: simple vector search
                vector_results = self.db.search(query_embedding, top_k=retrieve_k, filters=repo_filters)
                vector_results = self._filter_by_repo(vector_results)
                self.logger.info(f"CODE_LOCATION | Found {len(vector_results)} results from vector search")
                return vector_results[:self.top_k * 2]

        if query_type in ["impact_analysis", "traceability"] and self.multi_index_store:
            print(f"Executing Graph-Enhanced Retrieval ({query_type})...")
            
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

        # Normal retrieve logic
        # NOTE: CODE_LOCATION is handled above - if it reaches here, code_chunks_loader didn't find results
        # so we do a simple vector search without complex file index merging
        if query_type == QueryType.FLOW_ARCHITECTURE:
            retrieve_k = top_k or self.top_k * 6
        elif query_type == QueryType.HOW_TO:
            retrieve_k = top_k or self.top_k * 4
        elif query_type == QueryType.CODE_LOCATION:
            # CODE_LOCATION: Simple vector search fallback (code_chunks_loader already checked above)
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
        vector_results = self.db.search(query_embedding, top_k=retrieve_k, filters=repo_filters)
        
        # CRITICAL: Post-filter to ensure only current repo (safeguard)
        vector_results = self._filter_by_repo(vector_results)
        
        # For CODE_LOCATION queries: Simple vector search only (code_chunks_loader already checked above)
        # Skip complex file index merging - just return vector results
        if query_type == QueryType.CODE_LOCATION:
            self.logger.info(f"CODE_LOCATION | Returning {len(vector_results)} vector search results (code_chunks_loader had no matches)")
            results = vector_results
        # For HOW_TO queries: Merge file index results with vector search (if needed)
        elif query_type == QueryType.HOW_TO and query_text:
            file_path_results = self._retrieve_by_file_path(query_text, keywords)
            
            if file_path_results:
                # Merge file index results with vector search results
                # File index results have higher priority
                merged_results = {}
                seen_chunk_ids = set()
                
                # Add file index results first (highest priority)
                for result in file_path_results:
                    chunk_id = result.get('chunk_id')
                    if chunk_id:
                        merged_results[chunk_id] = result
                        seen_chunk_ids.add(chunk_id)
                
                # Add vector search results with path-based boost
                # BUT: For file queries, only add vector results if they match the exact file
                file_intent = self._detect_file_query_intent(query_text, keywords)
                filename_hints = file_intent.get('filename_hints', [])
                directory_hints = file_intent.get('directory_hints', [])
                requested_file_paths = file_intent.get('file_paths', [])
                
                self.logger.info(
                    f"FILE_RETRIEVAL | Merging vector results: "
                    f"file_paths={requested_file_paths}, filename_hints={filename_hints}, "
                    f"vector_results_count={len(vector_results)}"
                )
                
                for result in vector_results:
                    from utils.metadata_normalizer import MetadataNormalizer
                    meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
                    result_file_path = meta_norm.get_file_path('')
                    result_filename = meta_norm.get_filename('')
                    chunk_type = meta_norm.get_chunk_type('')
                    
                    # For file queries, STRICTLY filter vector results to only exact matches
                    matches_file_query = False
                    
                    # Check if this result matches any requested file path
                    if requested_file_paths:
                        for requested_path in requested_file_paths:
                            if result_file_path and (
                                result_file_path.lower() == requested_path.lower() or
                                result_file_path.lower().endswith(requested_path.lower())
                            ):
                                matches_file_query = True
                                self.logger.info(
                                    f"FILE_RETRIEVAL | Vector result matches file path: "
                                    f"'{result_file_path}' matches '{requested_path}'"
                                )
                                break
                    
                    # Check if this result matches any requested filename
                    if not matches_file_query and filename_hints:
                        for filename_hint in filename_hints:
                            if result_filename and result_filename.lower() == filename_hint.lower():
                                matches_file_query = True
                                self.logger.info(
                                    f"FILE_RETRIEVAL | Vector result matches filename: "
                                    f"'{result_filename}' matches '{filename_hint}'"
                                )
                                break
                    
                    # Only add vector results that match the file query
                    # For CODE_LOCATION queries, we want STRICT matching - only exact file matches
                    if not matches_file_query:
                        # Filter out non-matching files from vector search
                        self.logger.debug(
                            f"FILE_RETRIEVAL | Filtering out vector result: "
                            f"file='{result_file_path}', filename='{result_filename}', "
                            f"type='{chunk_type}', score={result.get('score', 0)}, "
                            f"doesn't match requested files {requested_file_paths} or filename hints {filename_hints}"
                        )
                        continue
                    
                    chunk_id = result.get('chunk_id')
                    if not chunk_id:
                        chunk_id = id(result)
                    
                    if chunk_id in seen_chunk_ids:
                        # Already have this from file index, skip
                        self.logger.debug(
                            f"FILE_RETRIEVAL | Skipping duplicate chunk_id: {chunk_id}"
                        )
                        continue
                    
                    # Apply path-based boost if file path matches
                    file_path_lower = result_file_path.lower() if result_file_path else ''
                    original_score = result.get('score', 0)
                    
                    if file_path_lower:
                        # Boost for exact filename matches
                        for filename_hint in filename_hints:
                            if result_filename and result_filename.lower() == filename_hint.lower():
                                result['score'] = original_score + 5.0  # Very strong boost for exact match
                                self.logger.info(
                                    f"FILE_RETRIEVAL | Exact filename match boost: "
                                    f"'{result_filename}' == '{filename_hint}', "
                                    f"score: {original_score} -> {result['score']}"
                                )
                                break
                        
                        # Boost for directory matches
                        for dir_hint in directory_hints:
                            if dir_hint in file_path_lower:
                                result['score'] = result.get('score', original_score) + 1.5
                                break
                    
                    self.logger.info(
                        f"FILE_RETRIEVAL | Adding vector result: "
                        f"file='{result_file_path}', filename='{result_filename}', "
                        f"score={result.get('score', 0)}, chunk_id={chunk_id}"
                    )
                    merged_results[chunk_id] = result
                
                # Convert back to list and sort by score
                results = list(merged_results.values())
                results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
                
                self.logger.info(f"HYBRID_FILE_RETRIEVAL | Merged {len(file_path_results)} file index + {len(vector_results)} vector results = {len(results)} total")
            else:
                # No file index results, use vector search with path-based boosts
                results = vector_results
                
                # Apply path-based boosts to vector results
                file_intent = self._detect_file_query_intent(query_text, keywords)
                filename_hints = file_intent.get('filename_hints', [])
                directory_hints = file_intent.get('directory_hints', [])
                
                for result in results:
                    from utils.metadata_normalizer import MetadataNormalizer
                    meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
                    file_path = meta_norm.get_file_path('')
                    
                    if file_path:
                        file_path_lower = file_path.lower()
                        original_score = result.get('score', 0)
                        
                        for filename_hint in filename_hints:
                            if filename_hint in file_path_lower:
                                result['score'] = original_score + 3.0
                                break
                        
                        for dir_hint in directory_hints:
                            if dir_hint in file_path_lower:
                                result['score'] = result.get('score', original_score) + 1.5
                                break
                
                results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)
        else:
            # Non-CODE_LOCATION queries: use vector search as before
            results = vector_results
        
        # Hybrid metadata boost (unchanged)
        if self.use_hybrid_retrieval:
            results = self.boost_by_metadata(results, keywords, query_type)
            results = sorted(results, key=lambda x: x.get('score', 0), reverse=True)

        return results[:self.top_k * 2]

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

        from utils.metadata_normalizer import MetadataNormalizer
        matching_entities = []
        for result in results:
            # Use metadata normalizer for unified access
            meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
            chunk_type = meta_norm.get_chunk_type('')

            if entity_type == 'issue' and chunk_type == 'issue':
                issue_num = meta_norm.get_issue_number()
                if issue_num is not None:
                    matching_entities.append({
                        'number': issue_num,
                        'result': result
                    })
            elif entity_type == 'pr' and chunk_type == 'pr':
                pr_num = meta_norm.get_pr_number()
                if pr_num is not None:
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
        """Generate a helpful response when no context is found."""
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

