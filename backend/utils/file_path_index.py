"""
File Path Index - Fast lookup index for file paths

This module provides a fast lookup index that maps file paths to chunk IDs,
enabling efficient retrieval of chunks by file path without full vector search.

Usage:
    from utils.file_path_index import FilePathIndex
    
    index = FilePathIndex()
    index.add_chunk("lib/app/file.dart", "chunk_123")
    index.add_chunk("lib/app/file.dart", "chunk_124")
    
    # Get all chunks for a file
    chunk_ids = index.get_chunks_by_path("lib/app/file.dart")
    
    # Search by partial path
    matches = index.search_paths("app/file")
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
import logging
from utils.path_normalizer import normalize_path, extract_filename

logger = logging.getLogger(__name__)


class FilePathIndex:
    """
    Fast lookup index for file paths to chunk IDs.
    
    Features:
    - O(1) lookup by exact file path
    - Fast partial path matching
    - Directory-based grouping
    - Normalized path handling
    - Persistence support
    """
    
    def __init__(self):
        """Initialize an empty file path index."""
        # Primary index: file_path -> set of chunk_ids
        self._path_to_chunks: Dict[str, Set[str]] = defaultdict(set)
        
        # Reverse index: chunk_id -> file_path (for updates/deletes)
        self._chunk_to_path: Dict[str, str] = {}
        
        # Directory index: directory -> set of file paths
        self._dir_to_files: Dict[str, Set[str]] = defaultdict(set)
        
        # Filename index: filename -> set of file paths (for filename-only searches)
        self._filename_to_paths: Dict[str, Set[str]] = defaultdict(set)
        
        # Statistics
        self._total_chunks = 0
        self._total_files = 0
    
    def add_chunk(self, file_path: str, chunk_id: str, metadata: Optional[Dict] = None) -> None:
        """
        Add a chunk to the index.
        
        Args:
            file_path: File path (will be normalized)
            chunk_id: Unique chunk identifier
            metadata: Optional metadata dict (for filename/directory extraction)
        """
        if not file_path or not chunk_id:
            return
        
        # Normalize file path
        normalized_path = normalize_path(file_path, '')
        if not normalized_path:
            return
        
        # Remove old mapping if chunk_id already exists
        if chunk_id in self._chunk_to_path:
            old_path = self._chunk_to_path[chunk_id]
            if old_path != normalized_path:
                self._remove_chunk_from_path(old_path, chunk_id)
        
        # Add to primary index
        if chunk_id not in self._path_to_chunks[normalized_path]:
            self._path_to_chunks[normalized_path].add(chunk_id)
            self._total_chunks += 1
        
        # Update reverse index
        self._chunk_to_path[chunk_id] = normalized_path
        
        # Update directory index
        directory = self._extract_directory(normalized_path, metadata)
        if directory:
            self._dir_to_files[directory].add(normalized_path)
        
        # Update filename index
        filename = self._extract_filename(normalized_path, metadata)
        if filename:
            self._filename_to_paths[filename].add(normalized_path)
        
        # Update file count
        self._total_files = len(self._path_to_chunks)
    
    def remove_chunk(self, chunk_id: str) -> None:
        """Remove a chunk from the index."""
        if chunk_id not in self._chunk_to_path:
            return
        
        file_path = self._chunk_to_path[chunk_id]
        self._remove_chunk_from_path(file_path, chunk_id)
        del self._chunk_to_path[chunk_id]
    
    def _remove_chunk_from_path(self, file_path: str, chunk_id: str) -> None:
        """Remove chunk from a specific path."""
        if file_path in self._path_to_chunks:
            self._path_to_chunks[file_path].discard(chunk_id)
            if not self._path_to_chunks[file_path]:
                del self._path_to_chunks[file_path]
                self._total_files = len(self._path_to_chunks)
            self._total_chunks -= 1
    
    def get_chunks_by_path(self, file_path: str) -> List[str]:
        """
        Get all chunk IDs for a specific file path.
        
        Args:
            file_path: File path (will be normalized)
            
        Returns:
            List of chunk IDs
        """
        normalized_path = normalize_path(file_path, '')
        if not normalized_path:
            return []
        
        return list(self._path_to_chunks.get(normalized_path, set()))
    
    def get_chunks_by_paths(self, file_paths: List[str]) -> List[str]:
        """
        Get all chunk IDs for multiple file paths.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of unique chunk IDs
        """
        chunk_ids = set()
        for file_path in file_paths:
            normalized_path = normalize_path(file_path, '')
            if normalized_path in self._path_to_chunks:
                chunk_ids.update(self._path_to_chunks[normalized_path])
        return list(chunk_ids)
    
    def search_paths(self, query: str, limit: Optional[int] = None) -> List[str]:
        """
        Search for file paths matching a query (partial match).
        
        Args:
            query: Search query (can be partial path, filename, or directory)
            limit: Maximum number of paths to return
            
        Returns:
            List of matching file paths
        """
        if not query:
            return []
        
        query_lower = query.lower().strip()
        normalized_query = normalize_path(query, '')
        
        # Extract filename from query if it looks like a path
        query_filename = extract_filename(normalized_query) if normalized_query else None
        if query_filename:
            query_filename_lower = query_filename.lower()
        else:
            # If query doesn't have path separators, treat entire query as potential filename
            query_filename_lower = query_lower
        
        matches = set()
        
        # 1. Exact path match (highest priority)
        if normalized_query in self._path_to_chunks:
            matches.add(normalized_query)
        
        # 2. Filename exact match (high priority)
        if query_filename_lower in self._filename_to_paths:
            matches.update(self._filename_to_paths[query_filename_lower])
        
        # 3. Filename partial match (e.g., "filter" matches "filters.dart")
        for filename, paths in self._filename_to_paths.items():
            if query_filename_lower in filename or filename.startswith(query_filename_lower):
                matches.update(paths)
        
        # 4. Partial path match (contains query)
        for path in self._path_to_chunks.keys():
            path_lower = path.lower()
            if query_lower in path_lower:
                matches.add(path)
        
        # 5. Directory match
        if normalized_query in self._dir_to_files:
            matches.update(self._dir_to_files[normalized_query])
        
        # Sort by relevance:
        # - Exact matches first
        # - Filename matches before path matches
        # - Shorter paths first
        def sort_key(p):
            p_lower = p.lower()
            is_exact = (p == normalized_query)
            is_filename_match = query_filename_lower and (
                extract_filename(p).lower() == query_filename_lower or
                extract_filename(p).lower().startswith(query_filename_lower)
            )
            return (
                0 if is_exact else (1 if is_filename_match else 2),  # Exact > filename > path
                len(p)  # Shorter paths first
            )
        
        sorted_matches = sorted(matches, key=sort_key)
        
        if limit:
            return sorted_matches[:limit]
        return sorted_matches
    
    def get_files_in_directory(self, directory: str) -> List[str]:
        """
        Get all file paths in a directory.
        
        Args:
            directory: Directory path (will be normalized)
            
        Returns:
            List of file paths
        """
        normalized_dir = normalize_path(directory, '')
        if not normalized_dir:
            return []
        
        return list(self._dir_to_files.get(normalized_dir, set()))
    
    def get_paths_by_filename(self, filename: str) -> List[str]:
        """
        Get all file paths with a specific filename.
        
        Args:
            filename: Filename (e.g., "file.dart")
            
        Returns:
            List of file paths
        """
        if not filename:
            return []
        
        # Normalize filename (extract just the name part)
        from utils.path_normalizer import extract_filename
        normalized_filename = extract_filename(filename) or filename.lower()
        
        return list(self._filename_to_paths.get(normalized_filename, set()))
    
    def get_all_paths(self) -> List[str]:
        """Get all file paths in the index."""
        return list(self._path_to_chunks.keys())
    
    def get_statistics(self) -> Dict[str, any]:
        """Get index statistics."""
        return {
            'total_files': self._total_files,
            'total_chunks': self._total_chunks,
            'total_directories': len(self._dir_to_files),
            'total_filenames': len(self._filename_to_paths)
        }
    
    def clear(self) -> None:
        """Clear the entire index."""
        self._path_to_chunks.clear()
        self._chunk_to_path.clear()
        self._dir_to_files.clear()
        self._filename_to_paths.clear()
        self._total_chunks = 0
        self._total_files = 0
    
    def _extract_directory(self, file_path: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """Extract directory from file path or metadata."""
        from utils.path_normalizer import extract_directory
        
        # Try metadata first
        if metadata:
            directory = metadata.get('directory')
            if directory:
                return normalize_path(directory, '')
        
        # Extract from path
        return extract_directory(file_path) or ''
    
    def _extract_filename(self, file_path: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """Extract filename from file path or metadata."""
        from utils.path_normalizer import extract_filename
        
        # Try metadata first
        if metadata:
            filename = metadata.get('filename')
            if filename:
                return filename.lower()
        
        # Extract from path
        return extract_filename(file_path) or None
    
    def to_dict(self) -> Dict:
        """Serialize index to dictionary for persistence."""
        return {
            'path_to_chunks': {k: list(v) for k, v in self._path_to_chunks.items()},
            'chunk_to_path': self._chunk_to_path.copy(),
            'statistics': self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FilePathIndex':
        """Deserialize index from dictionary."""
        index = cls()
        
        # Restore path_to_chunks
        for path, chunk_ids in data.get('path_to_chunks', {}).items():
            index._path_to_chunks[path] = set(chunk_ids)
            for chunk_id in chunk_ids:
                index._chunk_to_path[chunk_id] = path
        
        # Rebuild directory and filename indexes
        for path in index._path_to_chunks.keys():
            directory = index._extract_directory(path)
            if directory:
                index._dir_to_files[directory].add(path)
            
            filename = index._extract_filename(path)
            if filename:
                index._filename_to_paths[filename].add(path)
        
        # Restore statistics
        stats = data.get('statistics', {})
        index._total_chunks = stats.get('total_chunks', len(index._chunk_to_path))
        index._total_files = stats.get('total_files', len(index._path_to_chunks))
        
        return index

