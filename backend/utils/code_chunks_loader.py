"""
Code Chunks Loader - Loads and searches code_chunks.json files from DataProcessing directory.

This utility provides fast access to code chunks stored in JSON files,
serving as a fallback when vector index doesn't have results or for
files that haven't been indexed yet.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict
from utils.path_normalizer import normalize_path, extract_filename, extract_directory
from utils.repo_normalizer import repo_matches

logger = logging.getLogger(__name__)


class CodeChunksLoader:
    """
    Loads and searches code chunks from code_chunks.json files.
    
    Provides fast file-based lookup for code chunks that may not be
    in the vector index yet, or as a fallback when vector search fails.
    """
    
    def __init__(self):
        """Initialize the loader with empty cache."""
        self._chunks_cache: Dict[str, List[Dict]] = {}  # repo_key -> chunks list
        self._file_path_index: Dict[str, List[Dict]] = defaultdict(list)  # normalized_path -> chunks
        self._filename_index: Dict[str, List[Dict]] = defaultdict(list) 
        self._loaded_repos: Set[str] = set()
    
    def _get_repo_key(self, repo_owner: Optional[str], repo_name: Optional[str]) -> str:
        """Generate a unique key for a repository."""
        owner = (repo_owner or '').strip().lower()
        name = (repo_name or '').strip().lower()
        return f"{owner}/{name}" if owner else name
    
    def _find_code_chunks_file(self, repo_owner: Optional[str], repo_name: Optional[str]) -> Optional[Path]:
        """
        Find code_chunks.json file for a given repository.
        
        Args:
            repo_owner: Repository owner (optional)
            repo_name: Repository name
            
        Returns:
            Path to code_chunks.json file, or None if not found
        """
        if not repo_name:
            return None
        
        # Try to find backend directory
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent
        
        # Look in data/DataProcessing/{repo_owner}/{repo_name}/chunks/code_chunks.json
        # or data/DataProcessing/{repo_name}/chunks/code_chunks.json
        data_processing_dir = backend_dir / "data" / "DataProcessing"
        
        if not data_processing_dir.exists():
            return None
        
        # Try with owner first
        if repo_owner:
            repo_dir = data_processing_dir / repo_owner / repo_name
            chunks_file = repo_dir / "chunks" / "code_chunks.json"
            if chunks_file.exists():
                return chunks_file
        
        # Try without owner
        repo_dir = data_processing_dir / repo_name
        chunks_file = repo_dir / "chunks" / "code_chunks.json"
        if chunks_file.exists():
            return chunks_file
        
        # Try to find any repo directory that matches
        for owner_dir in data_processing_dir.iterdir():
            if owner_dir.is_dir():
                repo_dir = owner_dir / repo_name
                if repo_dir.exists():
                    chunks_file = repo_dir / "chunks" / "code_chunks.json"
                    if chunks_file.exists():
                        return chunks_file
        
        return None
    
    def load_repo_chunks(
        self, 
        repo_owner: Optional[str], 
        repo_name: Optional[str],
        chunks_file: Optional[Path] = None
    ) -> bool:
        """
        Load code chunks for a repository.
        
        Args:
            repo_owner: Repository owner (optional)
            repo_name: Repository name
            chunks_file: Optional path to code_chunks.json file
            
        Returns:
            True if chunks were loaded successfully, False otherwise
        """
        repo_key = self._get_repo_key(repo_owner, repo_name)
        
        # Already loaded
        if repo_key in self._loaded_repos:
            return True
        
        # Find chunks file if not provided
        if not chunks_file:
            chunks_file = self._find_code_chunks_file(repo_owner, repo_name)
        
        if not chunks_file or not chunks_file.exists():
            logger.debug(f"Code chunks file not found for {repo_key}")
            return False
        
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            if not isinstance(chunks, list):
                logger.warning(f"Code chunks file {chunks_file} is not a list")
                return False
            
            # Cache chunks
            self._chunks_cache[repo_key] = chunks
            
            # Build indexes
            for chunk in chunks:
                # Get file path from various possible locations
                file_path = (
                    chunk.get('file_path') or 
                    chunk.get('entities', {}).get('path') or
                    chunk.get('content', {}).get('file_path') or
                    ''
                )
                
                # Also try to get filename directly from chunk
                filename = chunk.get('filename', '')
                
                if not file_path and not filename:
                    logger.debug(f"CODE_CHUNKS_LOADER | Skipping chunk {chunk.get('chunk_id')} - no file_path or filename")
                    continue
                
                # Normalize path
                normalized_path = normalize_path(file_path, '') if file_path else ''
                
                # If we have filename but no path, try to construct a path
                # if not normalized_path and filename:
                #     # Use filename as path (for filename-only queries)
                #     normalized_path = filename
                
                if not normalized_path:
                    continue
                
                # Index by normalized path
                self._file_path_index[normalized_path].append(chunk)
                
                # Index by filename - use chunk filename if available, otherwise extract from path
                if filename:
                    fname = filename.lower()
                else:
                    fname = extract_filename(normalized_path).lower()

                if fname:
                    # index full filename
                    self._filename_index[fname].append(chunk)

                    # index filename WITHOUT extension (critical)
                    if "." in fname:
                        name_without_ext = fname.rsplit(".", 1)[0]
                        self._filename_index[name_without_ext].append(chunk)

                            
            self._loaded_repos.add(repo_key)
            logger.info(f"Loaded {len(chunks)} code chunks for {repo_key} from {chunks_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading code chunks from {chunks_file}: {e}")
            return False
    
    def get_chunks_by_file_path(
        self, 
        file_path: str,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        exact_match_only: bool = False
    ) -> List[Dict]:
        """
        Get all chunks for a specific file path.
        
        Args:
            file_path: File path to search for
            repo_owner: Repository owner (optional, for loading if needed)
            repo_name: Repository name (for loading if needed)
            exact_match_only: If True, only return exact path matches (no partial matches)
            
        Returns:
            List of chunks matching the file path
        """
        # Ensure repo is loaded
        repo_key = self._get_repo_key(repo_owner, repo_name)
        if repo_key not in self._loaded_repos and repo_name:
            self.load_repo_chunks(repo_owner, repo_name)

        # If input looks like a filename (no slashes), redirect to filename lookup
        if "/" not in file_path and "\\" not in file_path:
            return self.get_chunks_by_filename(
                file_path,
                repo_owner=repo_owner,
                repo_name=repo_name
            )

        
        # Normalize the search path
        normalized_path = normalize_path(file_path, '')
        if not normalized_path:
            logger.debug(f"CODE_CHUNKS_LOADER | Empty normalized path for '{file_path}'")
            return []
        
        # Get chunks from index
        chunks = self._file_path_index.get(normalized_path, [])

        if not chunks:
            filename = extract_filename(normalized_path)
            if filename:
                return self.get_chunks_by_filename(
                    filename,
                    repo_owner=repo_owner,
                    repo_name=repo_name
                )
        
        if exact_match_only:
            # Only return exact matches
            exact_chunks = []
            for chunk in chunks:
                chunk_path = chunk.get('file_path', '')
                chunk_normalized = normalize_path(chunk_path, '')
                if chunk_normalized == normalized_path:
                    exact_chunks.append(chunk)
            chunks = exact_chunks
            logger.debug(f"CODE_CHUNKS_LOADER | Exact match only: found {len(chunks)} chunks for '{normalized_path}'")
        
        # Filter by repo if specified
        if repo_name:
            filtered_chunks = []
            for chunk in chunks:
                chunk_repo = chunk.get('repo_name', '').strip().lower()
                chunk_owner = chunk.get('repo_owner', '').strip().lower()
                
                if repo_matches(chunk_repo, chunk_owner, repo_name, repo_owner):
                    filtered_chunks.append(chunk)
                else:
                    logger.debug(f"CODE_CHUNKS_LOADER | Repo filter: chunk repo '{chunk_repo}/{chunk_owner}' doesn't match '{repo_name}/{repo_owner}'")
            
            logger.info(f"CODE_CHUNKS_LOADER | Found {len(filtered_chunks)} chunks for file '{normalized_path}' (repo filtered)")
            return filtered_chunks
        
        logger.info(f"CODE_CHUNKS_LOADER | Found {len(chunks)} chunks for file '{normalized_path}'")
        return chunks
    
    def get_chunks_by_filename(
        self,
        filename: str,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all chunks for a specific filename (searches by filename, not full path).
        
        Args:
            filename: Filename to search for (e.g., "taskc_details_controller.dart")
            repo_owner: Repository owner (optional, for loading if needed)
            repo_name: Repository name (for loading if needed)
            
        Returns:
            List of chunks matching the filename
        """
        # Ensure repo is loaded
        repo_key = self._get_repo_key(repo_owner, repo_name)
        if repo_key not in self._loaded_repos and repo_name:
            self.load_repo_chunks(repo_owner, repo_name)
        
        # Normalize filename (lowercase, trim)
        filename_lower = filename.lower().strip()
        if not filename_lower:
            logger.debug(f"CODE_CHUNKS_LOADER | Empty filename for '{filename}'")
            return []
        
        logger.info(
            "CODE_CHUNKS_LOADER | Filename lookup started: '%s' (repo=%s/%s)",
            filename_lower,
            repo_owner,
            repo_name,
        )

        # Get all chunks for these paths
        # Extension fallback (taskc_details_controller → taskc_details_controller.dart)
        # Get all chunks for this filename
        all_chunks = list(self._filename_index.get(filename_lower, []))

        # Extension fallback (taskc_details_controller → taskc_details_controller.dart)
        if not all_chunks and "." not in filename_lower:
            dart_name = f"{filename_lower}.dart"
            all_chunks = list(self._filename_index.get(dart_name, []))

        # Deduplicate chunks (same chunk may appear via multiple filename keys)
        seen_chunk_ids = set()
        deduped_chunks = []

        for chunk in all_chunks:
            cid = chunk.get("chunk_id")
            if cid:
                if cid not in seen_chunk_ids:
                    seen_chunk_ids.add(cid)
                    deduped_chunks.append(chunk)
            else:
                # fallback: keep chunk without id
                deduped_chunks.append(chunk)

        all_chunks = deduped_chunks




        logger.info(
            "CODE_CHUNKS_LOADER | Filename '%s' matched %d chunks",
            filename_lower,
            len(all_chunks),
        )
        
        # -------------------------------------------------
        # AMBIGUOUS FILENAME DETECTION
        # -------------------------------------------------
        unique_paths = {
            normalize_path(chunk.get("file_path", ""), "")
            for chunk in all_chunks
            if chunk.get("file_path")
        }

        if len(unique_paths) > 1:
            paths = sorted(unique_paths)

            logger.warning(
                "AMBIGUOUS_FILENAME | '%s' found in multiple paths: %s",
                filename_lower,
                paths,
            )

            # Annotate chunks
            for chunk in all_chunks:
                chunk["_ambiguous_filename"] = True
                chunk["_all_matching_paths"] = paths

            # 🔴 CRITICAL: STOP NORMAL FLOW
            return all_chunks


        
        # Filter by repo if specified
        if repo_name:
            filtered_chunks = []
            for chunk in all_chunks:
                chunk_repo = chunk.get('repo_name', '').strip().lower()
                chunk_owner = chunk.get('repo_owner', '').strip().lower()
                
                if repo_matches(chunk_repo, chunk_owner, repo_name, repo_owner):
                    filtered_chunks.append(chunk)
                else:
                    logger.debug(
                        f"CODE_CHUNKS_LOADER | Repo filter: chunk repo '{chunk_repo}/{chunk_owner}' "
                        f"doesn't match '{repo_name}/{repo_owner}'"
                    )
            
            logger.info(
                f"CODE_CHUNKS_LOADER | Found {len(filtered_chunks)} chunks for filename "
                f"'{filename_lower}' (repo filtered from {len(all_chunks)})"
            )
            return filtered_chunks
        
        return all_chunks
    
    def search_files(
        self, 
        query: str,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
        limit: int = 20
    ) -> List[str]:
        """
        Search for file paths matching a query (filename or partial path).
        
        Args:
            query: Search query (filename or partial path)
            repo_owner: Repository owner (optional)
            repo_name: Repository name (optional)
            limit: Maximum number of results
            
        Returns:
            List of matching file paths
        """
        # Ensure repo is loaded
        repo_key = self._get_repo_key(repo_owner, repo_name)
        if repo_key not in self._loaded_repos and repo_name:
            self.load_repo_chunks(repo_owner, repo_name)
        
        query_lower = query.lower().strip()
        matches = set()
        
        # 1. Exact filename match
        if query_lower in self._filename_index:
            for chunk in self._filename_index[query_lower]:
                path = chunk.get("file_path")
                if path:
                    matches.add(normalize_path(path, ''))

        
        # 2. Partial filename match
        for filename, chunks in self._filename_index.items():
            if query_lower in filename or filename.startswith(query_lower):
                for chunk in chunks:
                    path = chunk.get("file_path")
                    if path:
                        matches.add(normalize_path(path, ''))

        
        # 3. Partial path match
        normalized_query = normalize_path(query, '')
        for path in self._file_path_index.keys():
            path_lower = path.lower()
            if query_lower in path_lower or (normalized_query and normalized_query in path_lower):
                matches.add(path)
        
        # Filter by repo if specified
        if repo_name:
            filtered_matches = []
            for path in matches:
                chunks = self._file_path_index.get(path, [])
                for chunk in chunks:
                    chunk_repo = chunk.get('repo_name', '').strip().lower()
                    chunk_owner = chunk.get('repo_owner', '').strip().lower()
                    
                    if repo_matches(chunk_repo, chunk_owner, repo_name, repo_owner):
                        filtered_matches.append(path)
                        break
            
            matches = set(filtered_matches)
        
        # Sort by relevance (exact matches first, then by length)
        sorted_matches = sorted(matches, key=lambda p: (
            0 if p.lower() == query_lower else (1 if query_lower in p.lower() else 2),
            len(p)
        ))
        
        return sorted_matches[:limit]
    
    def get_all_file_paths(
        self,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None
    ) -> List[str]:
        """
        Get all file paths for a repository.
        
        Args:
            repo_owner: Repository owner (optional)
            repo_name: Repository name (optional)
            
        Returns:
            List of all file paths
        """
        # Ensure repo is loaded
        repo_key = self._get_repo_key(repo_owner, repo_name)
        if repo_key not in self._loaded_repos and repo_name:
            self.load_repo_chunks(repo_owner, repo_name)
        
        all_paths = set(self._file_path_index.keys())
        
        # Filter by repo if specified
        if repo_name:
            filtered_paths = []
            for path in all_paths:
                chunks = self._file_path_index.get(path, [])
                for chunk in chunks:
                    chunk_repo = chunk.get('repo_name', '').strip().lower()
                    chunk_owner = chunk.get('repo_owner', '').strip().lower()
                    
                    if repo_matches(chunk_repo, chunk_owner, repo_name, repo_owner):
                        filtered_paths.append(path)
                        break
            
            return filtered_paths
        
        return list(all_paths)
    
    def clear_cache(self, repo_owner: Optional[str] = None, repo_name: Optional[str] = None):
        """Clear cache for a specific repo or all repos."""
        if repo_name:
            repo_key = self._get_repo_key(repo_owner, repo_name)
            if repo_key in self._chunks_cache:
                del self._chunks_cache[repo_key]
            if repo_key in self._loaded_repos:
                self._loaded_repos.remove(repo_key)
            
            # Remove from indexes
            paths_to_remove = []
            for path, chunks in self._file_path_index.items():
                if any(chunk.get('repo_name', '').strip().lower() == repo_name.lower() 
                       for chunk in chunks):
                    paths_to_remove.append(path)
            
            for path in paths_to_remove:
                if path in self._file_path_index:
                    del self._file_path_index[path]
        else:
            # Clear all
            self._chunks_cache.clear()
            self._file_path_index.clear()
            self._filename_index.clear()
            self._loaded_repos.clear()

