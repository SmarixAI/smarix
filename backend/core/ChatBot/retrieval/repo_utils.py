"""
Repository filtering and utility functions for retrieval.
"""
from typing import List, Dict, Any, Optional
from utils.metadata_normalizer import MetadataNormalizer
from utils.repo_normalizer import normalize_repo_name, normalize_repo_owner, repo_matches, extract_repo_parts


class RepoFilterMixin:
    """Mixin for repository-based filtering utilities."""
    
    def _get_repo_filters(self) -> Optional[Dict[str, Any]]:
        """
        Get repo-based filters for VectorDB search - FLEXIBLE filtering with normalization.
        
        Normalizes repo info before creating filters to handle format variations.
        """
        repo_owner_raw = getattr(self, 'repo_owner', None)
        repo_name_raw = getattr(self, 'repo_name', None)
        
        if not repo_name_raw:
            return None
        
        # Normalize repo info for consistent filtering
        # Handle case where repo_name might be in "owner/repo" format
        normalized_owner, normalized_repo = extract_repo_parts(repo_name_raw)
        
        # If owner not extracted from repo_name, use separate repo_owner
        if not normalized_owner and repo_owner_raw:
            normalized_owner = normalize_repo_owner(repo_owner_raw)
        
        # Normalize repo name if not already extracted
        if not normalized_repo:
            normalized_repo = normalize_repo_name(repo_name_raw)
        
        if not normalized_repo:
            return None
        
        # Return filter with normalized values
        # Note: VectorDB filter will do exact match, but we also do post-filtering
        # with flexible matching in _filter_by_repo
        filters = {"repo_name": normalized_repo}
        if normalized_owner:
            filters["repo_owner"] = normalized_owner
        
        return filters
    
    def _filter_by_repo(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Post-retrieval filtering to ensure only current repo chunks are returned.
        
        Uses FLEXIBLE matching to handle format variations:
        - Case-insensitive matching
        - Whitespace handling
        - URL format extraction
        - Missing owner handling (if repo name matches)
        - Various format variations (owner/repo, owner-repo, etc.)
        """
        repo_owner_raw = getattr(self, 'repo_owner', None)
        repo_name_raw = getattr(self, 'repo_name', None)
        
        # If repo name not available, return empty (don't return results from unknown repos)
        if not repo_name_raw:
            if results:
                self.logger.warning(f"FILTER | No repo info available, filtering out {len(results)} results")
            return []
        
        # Normalize current repo info
        # Handle case where repo_name might be in "owner/repo" format
        normalized_current_owner, normalized_current_repo = extract_repo_parts(repo_name_raw)
        
        # If owner not extracted from repo_name, use separate repo_owner
        if not normalized_current_owner and repo_owner_raw:
            normalized_current_owner = normalize_repo_owner(repo_owner_raw)
        
        # Normalize repo name if not already extracted
        if not normalized_current_repo:
            normalized_current_repo = normalize_repo_name(repo_name_raw)
        
        if not normalized_current_repo:
            if results:
                self.logger.warning(f"FILTER | Could not normalize repo name, filtering out {len(results)} results")
            return []
        
        filtered = []
        for result in results:
            # Use metadata normalizer for unified repo access
            meta_norm = MetadataNormalizer(result.get('metadata', {}), result)
            chunk_repo_raw = meta_norm.get_repo_name('')
            chunk_owner_raw = meta_norm.get_repo_owner('')
            
            # Normalize chunk repo info
            normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(chunk_repo_raw)
            
            # If owner not extracted from repo_name, use separate repo_owner
            if not normalized_chunk_owner and chunk_owner_raw:
                normalized_chunk_owner = normalize_repo_owner(chunk_owner_raw)
            
            # Normalize repo name if not already extracted
            if not normalized_chunk_repo:
                normalized_chunk_repo = normalize_repo_name(chunk_repo_raw)
            
            # Use flexible matching
            matches = repo_matches(
                normalized_current_owner, normalized_current_repo,
                normalized_chunk_owner, normalized_chunk_repo
            )
            
            if matches:
                filtered.append(result)
        
        if len(filtered) < len(results):
            current_repo_display = f"{normalized_current_owner}/{normalized_current_repo}" if normalized_current_owner else normalized_current_repo
            self.logger.info(f"FILTER | Filtered {len(results)} -> {len(filtered)} results for repo {current_repo_display}")
        
        return filtered
    
    def _retrieve_by_file_path(self, query_text: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve chunks using file path index for fast file-based lookups.
        
        This is used for CODE_LOCATION queries when file paths are detected.
        
        Args:
            query_text: Query text that may contain file paths
            keywords: Extracted keywords that may include file paths
            
        Returns:
            List of chunk dictionaries, or empty list if no file paths found
        """
        import re
        
        # Try to extract file paths from query
        file_paths = []
        
        # Check keywords for file paths (common patterns)
        for keyword in keywords:
            # Look for path-like patterns (contain / or \)
            if '/' in keyword or '\\' in keyword:
                from utils.path_normalizer import normalize_path
                normalized = normalize_path(keyword, '')
                if normalized:
                    file_paths.append(normalized)
        
        # Check query text for file paths
        # Pattern: look for paths with extensions or common path separators
        path_patterns = [
            r'[\w\-_/\\]+\.(py|js|ts|dart|java|go|rs|cpp|c|h|hpp|md|txt|json|yaml|yml)',
            r'[\w\-_/\\]+/[\w\-_/\\]+',  # directory/file pattern
        ]
        
        for pattern in path_patterns:
            matches = re.findall(pattern, query_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = ''.join(match)
                from utils.path_normalizer import normalize_path
                normalized = normalize_path(match, '')
                if normalized and normalized not in file_paths:
                    file_paths.append(normalized)
        
        if not file_paths:
            # Try searching file path index with query text
            if hasattr(self, 'multi_index_store') and self.multi_index_store:
                # Search across all indices
                all_paths = []
                for index_type in ['code', 'all']:
                    index_db = self.multi_index_store.indices.get(index_type)
                    if index_db and hasattr(index_db, 'search_file_paths'):
                        found_paths = index_db.search_file_paths(query_text, limit=10)
                        all_paths.extend(found_paths)
                
                if all_paths:
                    file_paths = list(set(all_paths))[:5]  # Limit to top 5 matches
        
        if not file_paths:
            return []
        
        # Retrieve chunks for found file paths
        results = []
        
        for index_type in ['code', 'all']:
            if not hasattr(self, 'multi_index_store') or not self.multi_index_store:
                continue
                
            index_db = self.multi_index_store.indices.get(index_type)
            if index_db and hasattr(index_db, 'get_by_file_paths'):
                chunks = index_db.get_by_file_paths(file_paths)
                
                # Add score and format results
                for chunk in chunks:
                    # Check repo filter
                    if not self._chunk_matches_repo(chunk):
                        continue
                    
                    # Format result
                    result = {
                        'chunk_id': chunk.get('chunk_id'),
                        'metadata': chunk.get('metadata', {}),
                        'content': chunk.get('content', ''),
                        'score': 1.0,  # High score for direct file path match
                        'source': index_type
                    }
                    results.append(result)
        
        # Remove duplicates by chunk_id
        seen = set()
        unique_results = []
        for result in results:
            chunk_id = result.get('chunk_id')
            if chunk_id and chunk_id not in seen:
                seen.add(chunk_id)
                unique_results.append(result)
        
        return unique_results
    
    def _chunk_matches_repo(self, chunk: Dict[str, Any]) -> bool:
        """Check if chunk matches current repo (helper for file path retrieval)."""
        repo_owner_raw = getattr(self, 'repo_owner', None)
        repo_name_raw = getattr(self, 'repo_name', None)
        
        if not repo_name_raw:
            return False
        
        from utils.metadata_normalizer import MetadataNormalizer
        from utils.repo_normalizer import repo_matches, normalize_repo_name, normalize_repo_owner, extract_repo_parts
        
        meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
        chunk_repo = meta_norm.get_repo_name('')
        chunk_owner = meta_norm.get_repo_owner('')
        
        # Normalize current repo
        normalized_current_owner, normalized_current_repo = extract_repo_parts(repo_name_raw)
        if not normalized_current_owner and repo_owner_raw:
            normalized_current_owner = normalize_repo_owner(repo_owner_raw)
        if not normalized_current_repo:
            normalized_current_repo = normalize_repo_name(repo_name_raw)
        
        # Normalize chunk repo
        normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(chunk_repo)
        if not normalized_chunk_owner and chunk_owner:
            normalized_chunk_owner = normalize_repo_owner(chunk_owner)
        if not normalized_chunk_repo:
            normalized_chunk_repo = normalize_repo_name(chunk_repo)
        
        return repo_matches(
            normalized_current_owner, normalized_current_repo,
            normalized_chunk_owner, normalized_chunk_repo
        )

