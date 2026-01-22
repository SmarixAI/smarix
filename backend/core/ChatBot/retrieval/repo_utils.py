"""
Repository filtering and utility functions for retrieval.
"""
from typing import List, Dict, Any, Optional
from utils.metadata_normalizer import MetadataNormalizer
from utils.repo_normalizer import normalize_repo_name, normalize_repo_owner, repo_matches, extract_repo_parts
from utils.path_normalizer import normalize_path, extract_filename, extract_directory


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
    
    def _get_file_suggestions(self, query_text: str, limit: int = 5) -> List[str]:
        """
        Get file suggestions when exact match not found.
        Uses fuzzy matching to suggest similar files.
        
        Args:
            query_text: Query text
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested file paths
        """
        if not hasattr(self, 'multi_index_store') or not self.multi_index_store:
            return []
        
        suggestions = []
        
        # Get all available files from file path index
        for index_type in ['code', 'all']:
            index_db = self.multi_index_store.indices.get(index_type)
            if not index_db or not hasattr(index_db, 'file_path_index'):
                continue
            
            file_path_index = index_db.file_path_index
            if not file_path_index:
                continue
            
            # Get all filenames
            all_filenames = list(file_path_index._filename_to_paths.keys())
            
            # Extract filename from query
            from utils.path_normalizer import extract_filename
            query_filename = extract_filename(query_text) or query_text.split()[-1] if query_text.split() else ''
            
            if query_filename:
                from utils.fuzzy_file_matcher import find_similar_filenames
                similar = find_similar_filenames(query_filename, all_filenames, limit=limit)
                
                # Get full paths for similar filenames
                for filename, score in similar:
                    if filename in file_path_index._filename_to_paths:
                        paths = file_path_index._filename_to_paths[filename]
                        suggestions.extend(list(paths)[:2])  # Max 2 paths per filename
                
                if len(suggestions) >= limit:
                    break
        
        return suggestions[:limit]
    
    def _detect_file_query_intent(self, query_text: str, keywords: List[str]) -> Dict[str, Any]:
        """
        Detect if query is about a file and extract file-related information.
        
        Returns:
            Dict with:
            - is_file_query: bool
            - file_paths: List[str] - extracted file paths
            - filename_hints: List[str] - potential filenames
            - directory_hints: List[str] - potential directories
        """
        import re
        from utils.path_normalizer import normalize_path, extract_filename, extract_directory
        
        result = {
            'is_file_query': False,
            'file_paths': [],
            'filename_hints': [],
            'directory_hints': []
        }
        
        query_lower = query_text.lower()
        
        # Check for explicit file path patterns
        path_patterns = [
            r'[\w\-_./\\]+\.(?:py|js|ts|dart|java|go|rs|cpp|c|h|hpp|md|txt|json|yaml|yml|xml|html|css|scss|less|vue|jsx|tsx|kt|swift|rb|php|r|m|mm|pl|sh|bash|zsh|fish|ps1|bat|cmd)',
            r'[\w\-_./\\]+/[\w\-_./\\]+',
        ]
        
        for pattern in path_patterns:
            matches = re.findall(pattern, query_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = ''.join(match)
                normalized = normalize_path(match.strip(), '')
                if normalized:
                    result['file_paths'].append(normalized)
                    result['is_file_query'] = True
                    
                    # Extract filename and directory hints
                    filename = extract_filename(normalized)
                    directory = extract_directory(normalized)
                    if filename:
                        result['filename_hints'].append(filename.lower())
                    if directory:
                        result['directory_hints'].append(directory.lower())
        
        # Check keywords for file-like patterns
        for keyword in keywords:
            if '/' in keyword or '\\' in keyword or '.' in keyword:
                normalized = normalize_path(keyword, '')
                if normalized and normalized not in result['file_paths']:
                    result['file_paths'].append(normalized)
                    result['is_file_query'] = True
                    
                    filename = extract_filename(normalized)
                    directory = extract_directory(normalized)
                    if filename:
                        result['filename_hints'].append(filename.lower())
                    if directory:
                        result['directory_hints'].append(directory.lower())
        
        # Check for filename-only queries (e.g., "filters.dart")
        filename_only_pattern = r'([\w\-_]+\.[\w]+)'
        filename_matches = re.findall(filename_only_pattern, query_text, re.IGNORECASE)
        for match in filename_matches:
            if match.lower() not in result['filename_hints']:
                result['filename_hints'].append(match.lower())
                result['is_file_query'] = True
        
        # Check for multiple file queries (e.g., "filters.dart and users.dart")
        from utils.fuzzy_file_matcher import extract_file_query_components
        multi_file_info = extract_file_query_components(query_text)
        if multi_file_info['is_multiple']:
            for file_query in multi_file_info['file_queries']:
                normalized = normalize_path(file_query, '')
                if normalized and normalized not in result['file_paths']:
                    result['file_paths'].append(normalized)
                    result['is_file_query'] = True
                    
                    filename = extract_filename(normalized)
                    directory = extract_directory(normalized)
                    if filename:
                        result['filename_hints'].append(filename.lower())
                    if directory:
                        result['directory_hints'].append(directory.lower())
        
        # Check for directory queries (e.g., "show me all files in lib/app/models")
        directory_query_patterns = [
            r'(?:all files?|files?) (?:in|from|under)\s+([\w\-_./\\]+)',
            r'(?:list|show|get)\s+(?:all\s+)?files?\s+(?:in|from|under)\s+([\w\-_./\\]+)',
        ]
        for pattern in directory_query_patterns:
            matches = re.findall(pattern, query_text, re.IGNORECASE)
            for match in matches:
                normalized = normalize_path(match.strip(), '')
                if normalized and normalized not in result['directory_hints']:
                    result['directory_hints'].append(normalized.lower())
                    result['is_file_query'] = True
        
        # Remove duplicates
        result['file_paths'] = list(set(result['file_paths']))
        result['filename_hints'] = list(set(result['filename_hints']))
        result['directory_hints'] = list(set(result['directory_hints']))
        
        return result
    
    def _retrieve_by_file_path(self, query_text: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        HYBRID FILE RETRIEVAL: Multi-strategy approach to ensure files are never missed.
        
        Strategy:
        1. File Path Index Lookup (fast, exact/partial matches)
        2. Keyword-based filename matching
        3. Vector search with path-based boosts (fallback)
        
        Args:
            query_text: Query text that may contain file paths
            keywords: Extracted keywords that may include file paths
            
        Returns:
            List of chunk dictionaries with all matching file chunks
        """
        # Step 1: Detect file query intent
        file_intent = self._detect_file_query_intent(query_text, keywords)
        
        if not file_intent['is_file_query']:
            # Not a file query, return empty
            return []
        
        file_paths = file_intent['file_paths']
        filename_hints = file_intent['filename_hints']
        directory_hints = file_intent['directory_hints']
        
        all_results = []
        seen_chunk_ids = set()
        
        if not hasattr(self, 'multi_index_store') or not self.multi_index_store:
            return []
        
        # Step 2: File Path Index Lookup (highest priority)
        for index_type in ['code', 'all']:
            index_db = self.multi_index_store.indices.get(index_type)
            if not index_db or not hasattr(index_db, 'get_by_file_paths'):
                continue
            
            # Try exact file paths first
            if file_paths:
                chunks = index_db.get_by_file_paths(file_paths)
                for chunk in chunks:
                    if not self._chunk_matches_repo(chunk):
                        continue
                    
                    chunk_id = chunk.get('chunk_id')
                    if chunk_id and chunk_id not in seen_chunk_ids:
                        seen_chunk_ids.add(chunk_id)
                        from utils.metadata_normalizer import MetadataNormalizer
                        meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                        chunk_type = meta_norm.get_chunk_type('')
                        
                        # Filter out PR/issue chunks
                        if chunk_type in ['pr', 'issue', 'email']:
                            continue
                        
                        all_results.append({
                            'chunk_id': chunk_id,
                            'metadata': chunk.get('metadata', {}),
                            'content': chunk.get('content', ''),
                            'score': 15.0 if index_type == 'code' else 12.0,  # Very high for exact match
                            'source': f'file_index_{index_type}',
                            'match_type': 'exact_path'
                        })
            
            # Try filename-based search in file path index
            if filename_hints and hasattr(index_db, 'search_file_paths'):
                for filename_hint in filename_hints:
                    found_paths = index_db.search_file_paths(filename_hint, limit=20)
                    if found_paths:
                        chunks = index_db.get_by_file_paths(found_paths)
                        for chunk in chunks:
                            if not self._chunk_matches_repo(chunk):
                                continue
                            
                            chunk_id = chunk.get('chunk_id')
                            if chunk_id and chunk_id not in seen_chunk_ids:
                                seen_chunk_ids.add(chunk_id)
                                from utils.metadata_normalizer import MetadataNormalizer
                                meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                                chunk_type = meta_norm.get_chunk_type('')
                                
                                if chunk_type in ['pr', 'issue', 'email']:
                                    continue
                                
                                # Check if filename matches
                                file_path = meta_norm.get_file_path('')
                                if file_path and filename_hint in file_path.lower():
                                    all_results.append({
                                        'chunk_id': chunk_id,
                                        'metadata': chunk.get('metadata', {}),
                                        'content': chunk.get('content', ''),
                                        'score': 10.0 if index_type == 'code' else 8.0,  # High for filename match
                                        'source': f'file_index_{index_type}',
                                        'match_type': 'filename_match'
                                    })
        
        # Step 3: Try directory-based search if directory hints exist
        if directory_hints and hasattr(self, 'multi_index_store') and self.multi_index_store:
            for index_type in ['code', 'all']:
                index_db = self.multi_index_store.indices.get(index_type)
                if not index_db or not hasattr(index_db, 'file_path_index'):
                    continue
                
                file_path_index = index_db.file_path_index
                if not file_path_index:
                    continue
                
                for dir_hint in directory_hints:
                    # Get files in directory
                    if hasattr(file_path_index, 'get_files_in_directory'):
                        dir_files = file_path_index.get_files_in_directory(dir_hint)
                        if dir_files:
                            chunks = index_db.get_by_file_paths(dir_files)
                            for chunk in chunks:
                                if not self._chunk_matches_repo(chunk):
                                    continue
                                
                                chunk_id = chunk.get('chunk_id')
                                if chunk_id and chunk_id not in seen_chunk_ids:
                                    seen_chunk_ids.add(chunk_id)
                                    from utils.metadata_normalizer import MetadataNormalizer
                                    meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                                    chunk_type = meta_norm.get_chunk_type('')
                                    
                                    if chunk_type in ['pr', 'issue', 'email']:
                                        continue
                                    
                                    all_results.append({
                                        'chunk_id': chunk_id,
                                        'metadata': chunk.get('metadata', {}),
                                        'content': chunk.get('content', ''),
                                        'score': 9.0 if index_type == 'code' else 7.0,
                                        'source': f'file_index_{index_type}',
                                        'match_type': 'directory_match'
                                    })
        
        # Step 4: If we still don't have results, try broader file path index search
        if not all_results and hasattr(self, 'multi_index_store') and self.multi_index_store:
            for index_type in ['code', 'all']:
                index_db = self.multi_index_store.indices.get(index_type)
                if index_db and hasattr(index_db, 'search_file_paths'):
                    # Search with full query text
                    found_paths = index_db.search_file_paths(query_text, limit=15)
                    if found_paths:
                        chunks = index_db.get_by_file_paths(found_paths)
                        for chunk in chunks:
                            if not self._chunk_matches_repo(chunk):
                                continue
                            
                            chunk_id = chunk.get('chunk_id')
                            if chunk_id and chunk_id not in seen_chunk_ids:
                                seen_chunk_ids.add(chunk_id)
                                from utils.metadata_normalizer import MetadataNormalizer
                                meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                                chunk_type = meta_norm.get_chunk_type('')
                                
                                if chunk_type in ['pr', 'issue', 'email']:
                                    continue
                                
                                all_results.append({
                                    'chunk_id': chunk_id,
                                    'metadata': chunk.get('metadata', {}),
                                    'content': chunk.get('content', ''),
                                    'score': 8.0 if index_type == 'code' else 6.0,  # Medium for partial match
                                    'source': f'file_index_{index_type}',
                                    'match_type': 'partial_path'
                                })
        
        if not file_paths:
            return []
        
        # Retrieve chunks for found file paths
        # Prioritize 'code' index first, then 'all' index
        results = []
        
        # First, try 'code' index (most relevant for file paths)
        if hasattr(self, 'multi_index_store') and self.multi_index_store:
            code_index_db = self.multi_index_store.indices.get('code')
            if code_index_db and hasattr(code_index_db, 'get_by_file_paths'):
                chunks = code_index_db.get_by_file_paths(file_paths)
                
                # Add score and format results - PRIORITIZE CODE CHUNKS
                for chunk in chunks:
                    # Check repo filter
                    if not self._chunk_matches_repo(chunk):
                        continue
                    
                    # Use metadata normalizer to check chunk type
                    from utils.metadata_normalizer import MetadataNormalizer
                    meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                    chunk_type = meta_norm.get_chunk_type('')
                    
                    # FILTER OUT PR/ISSUE chunks - we want actual code files
                    if chunk_type in ['pr', 'issue', 'email']:
                        continue
                    
                    # Format result with high score for direct file path match
                    result = {
                        'chunk_id': chunk.get('chunk_id'),
                        'metadata': chunk.get('metadata', {}),
                        'content': chunk.get('content', ''),
                        'score': 10.0,  # Very high score for direct file path match from code index
                        'source': 'code'
                    }
                    results.append(result)
        
        # If we didn't find enough results, try 'all' index but still filter PR/issue chunks
        # For file-specific queries, we want ALL chunks from the file, so don't limit
        if hasattr(self, 'multi_index_store') and self.multi_index_store:
            all_index_db = self.multi_index_store.indices.get('all')
            if all_index_db and hasattr(all_index_db, 'get_by_file_paths'):
                chunks = all_index_db.get_by_file_paths(file_paths)
                
                for chunk in chunks:
                    # Check repo filter
                    if not self._chunk_matches_repo(chunk):
                        continue
                    
                    # Use metadata normalizer to check chunk type
                    from utils.metadata_normalizer import MetadataNormalizer
                    meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                    chunk_type = meta_norm.get_chunk_type('')
                    
                    # FILTER OUT PR/ISSUE chunks - we want actual code files
                    if chunk_type in ['pr', 'issue', 'email']:
                        continue
                    
                    chunk_id = chunk.get('chunk_id')
                    # Skip if already in results
                    if any(r.get('chunk_id') == chunk_id for r in results):
                        continue
                    
                    # Format result with lower score than code index
                    result = {
                        'chunk_id': chunk_id,
                        'metadata': chunk.get('metadata', {}),
                        'content': chunk.get('content', ''),
                        'score': 8.0,  # High but lower than code index
                        'source': 'all'
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
        
        # Sort by chunk type priority, then by score
        # Priority: file_overview > code > function > class > method > others
        def sort_key(r):
            meta_norm = MetadataNormalizer(r.get('metadata', {}), r)
            chunk_type = meta_norm.get_chunk_type('')
            score = r.get('score', 0)
            
            # Type priority: overview first, then code chunks
            type_priority_map = {
                'file_overview': 0,
                'code': 1,
                'function': 2,
                'class': 3,
                'method': 4,
            }
            type_priority = type_priority_map.get(chunk_type, 10)
            
            return (type_priority, -score)
        
        unique_results.sort(key=sort_key)
        
        # Step 5: If still no results, try fuzzy matching for typos
        if not unique_results and filename_hints and hasattr(self, 'multi_index_store') and self.multi_index_store:
            from utils.fuzzy_file_matcher import find_similar_filenames
            
            for index_type in ['code', 'all']:
                index_db = self.multi_index_store.indices.get(index_type)
                if not index_db or not hasattr(index_db, 'file_path_index'):
                    continue
                
                file_path_index = index_db.file_path_index
                if not file_path_index:
                    continue
                
                all_filenames = list(file_path_index._filename_to_paths.keys())
                
                for filename_hint in filename_hints:
                    # Try fuzzy matching
                    similar = find_similar_filenames(filename_hint, all_filenames, limit=5)
                    
                    for similar_filename, similarity_score in similar:
                        if similar_filename in file_path_index._filename_to_paths:
                            similar_paths = file_path_index._filename_to_paths[similar_filename]
                            chunks = index_db.get_by_file_paths(list(similar_paths))
                            
                            for chunk in chunks:
                                if not self._chunk_matches_repo(chunk):
                                    continue
                                
                                chunk_id = chunk.get('chunk_id')
                                if chunk_id and chunk_id not in seen_chunk_ids:
                                    seen_chunk_ids.add(chunk_id)
                                    from utils.metadata_normalizer import MetadataNormalizer
                                    meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                                    chunk_type = meta_norm.get_chunk_type('')
                                    
                                    if chunk_type in ['pr', 'issue', 'email']:
                                        continue
                                    
                                    # Score based on similarity
                                    base_score = 7.0 if index_type == 'code' else 5.0
                                    score = base_score + (similarity_score * 2.0)  # Boost by similarity
                                    
                                    unique_results.append({
                                        'chunk_id': chunk_id,
                                        'metadata': chunk.get('metadata', {}),
                                        'content': chunk.get('content', ''),
                                        'score': score,
                                        'source': f'file_index_{index_type}',
                                        'match_type': 'fuzzy_match',
                                        'similarity': similarity_score
                                    })
        
        # Log results for debugging
        if unique_results:
            self.logger.info(f"FILE_PATH_RETRIEVAL | Found {len(unique_results)} chunks from file index")
            match_types = {}
            for r in unique_results:
                match_type = r.get('match_type', 'unknown')
                match_types[match_type] = match_types.get(match_type, 0) + 1
            self.logger.info(f"FILE_PATH_RETRIEVAL | Match types: {match_types}")
        else:
            # Log that no results were found and provide suggestions
            suggestions = self._get_file_suggestions(query_text, limit=3)
            if suggestions:
                self.logger.warning(f"FILE_PATH_RETRIEVAL | No exact matches found. Suggestions: {suggestions[:3]}")
        
        # For file-specific queries, return ALL chunks (no limit)
        # This ensures we get the complete file content
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

