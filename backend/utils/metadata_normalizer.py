"""
Metadata Normalizer - Unified metadata structure with fallback lookups

This module provides a standardized way to access metadata fields across
the codebase, handling all variations and legacy field names with automatic
fallback lookups. This ensures backward compatibility while moving toward
a unified metadata schema.

Usage:
    from utils.metadata_normalizer import MetadataNormalizer
    
    normalizer = MetadataNormalizer(metadata_dict)
    file_path = normalizer.get_file_path()
    chunk_type = normalizer.get_chunk_type()
    repo_name = normalizer.get_repo_name()
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import logging
from utils.path_normalizer import normalize_path, extract_filename, extract_directory
from utils.repo_normalizer import normalize_repo_name, normalize_repo_owner, extract_repo_parts

logger = logging.getLogger(__name__)


class MetadataNormalizer:
    """
    Normalizes and provides unified access to metadata fields with comprehensive
    fallback lookups. Handles all legacy field name variations.
    
    This class is designed to be backward compatible - it doesn't modify the
    original metadata, only provides normalized access to it.
    """
    
    def __init__(self, metadata: Union[Dict[str, Any], Any], result_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize with metadata dictionary.
        
        Args:
            metadata: The metadata dictionary (can be nested under 'metadata' key or top-level)
            result_dict: Optional result dictionary (for cases where metadata is in result['metadata'])
        """
        # Handle case where metadata is nested in result dict
        if result_dict is not None:
            base = result_dict.get('metadata', {}) or metadata or {}

            # 🔥 MERGE ENTITIES INTO METADATA
            entities = result_dict.get("entities", {})
            if isinstance(entities, dict):
                base = {**base, **entities}

            # 🔥 OPTIONAL: merge raw_data if present
            raw_data = result_dict.get("raw_data", {})
            if isinstance(raw_data, dict):
                base = {**base, **raw_data}

            self._raw_metadata = base
        else:
            # Handle both direct metadata dict and nested cases
            if isinstance(metadata, dict):
                # If it's a result dict with nested metadata
                if 'metadata' in metadata and isinstance(metadata.get('metadata'), dict):
                    self._raw_metadata = metadata.get('metadata', {})
                # If metadata fields are at top level
                elif any(key in metadata for key in ['file_path', 'chunk_type', 'type', 'repo_name']):
                    self._raw_metadata = metadata
                else:
                    self._raw_metadata = metadata
            else:
                self._raw_metadata = {}
        
        # Also check if metadata is in entities sub-dict
        if not self._raw_metadata and isinstance(metadata, dict):
            if 'entities' in metadata and isinstance(metadata.get('entities'), dict):
                self._raw_metadata = metadata.get('entities', {})
    
    def get_file_path(self, default: Optional[str] = None) -> Optional[str]:
        """
        Get file path with comprehensive fallback lookups.
        
        Field name variations checked (in order):
        - file_path (primary)
        - file
        - path
        - repo_file_path
        - source (if it looks like a path)
        - entities.path
        - entities.file_path
        
        Returns:
            Normalized file path (forward slashes, trimmed) or default
        """
        # Primary field
        file_path = self._raw_metadata.get('file_path')
        if file_path and str(file_path).strip():
            return self._normalize_path(file_path)
        
        # Fallback fields
        for field in ['file', 'path', 'repo_file_path']:
            file_path = self._raw_metadata.get(field)
            if file_path and str(file_path).strip():
                return self._normalize_path(file_path)
        
        # Check 'source' if it looks like a file path
        source = self._raw_metadata.get('source', '')
        if source and ('/' in str(source) or '\\' in str(source)) and not source.startswith('http'):
            return self._normalize_path(source)
        
        # Check nested entities
        entities = self._raw_metadata.get('entities', {})
        if isinstance(entities, dict):
            for field in ['path', 'file_path']:
                file_path = entities.get(field)
                if file_path and str(file_path).strip():
                    return self._normalize_path(file_path)
        
        return default
    
    def get_created_at(self, default: Optional[str] = None) -> Optional[str]:
        temporal = self._raw_metadata.get("temporal", {})
        return (
            temporal.get("created_at")
            or self._raw_metadata.get("created_at")
            or default
        )

    def get_merged_at(self, default: Optional[str] = None) -> Optional[str]:
        temporal = self._raw_metadata.get("temporal", {})
        return (
            temporal.get("merged_at")
            or self._raw_metadata.get("merged_at")
            or default
        )

    def get_closed_at(self, default: Optional[str] = None) -> Optional[str]:
        temporal = self._raw_metadata.get("temporal", {})
        return (
            temporal.get("closed_at")
            or self._raw_metadata.get("closed_at")
            or default
        )

    
    def get_chunk_type(self, default: Optional[str] = None) -> Optional[str]:
        """
        Get chunk type with fallback lookups.
        
        Field name variations checked (in order):
        - chunk_type (primary)
        - type
        - source_type
        - content_type
        
        Returns:
            Chunk type string or default
        """
        # Primary field
        chunk_type = self._raw_metadata.get('chunk_type')
        if chunk_type:
            return str(chunk_type)
        
        # Fallback fields
        for field in ['type', 'source_type', 'content_type']:
            chunk_type = self._raw_metadata.get(field)
            if chunk_type:
                return str(chunk_type)
        
        return default
    
    def get_repo_name(self, default: Optional[str] = None) -> Optional[str]:
        """
        Get repository name with fallback lookups.
        
        Field name variations checked (in order):
        - repo_name (primary)
        - repository
        - repo
        
        Also handles full format "owner/repo" and extracts just the repo name.
        Uses repo normalizer for consistent format handling.
        
        Returns:
            Normalized repository name or default
        """
        # Primary field
        repo_name = self._raw_metadata.get('repo_name')
        if repo_name:
            return normalize_repo_name(repo_name, default)
        
        # Fallback fields
        for field in ['repository', 'repo']:
            repo_name = self._raw_metadata.get(field)
            if repo_name:
                return normalize_repo_name(repo_name, default)
        
        return default
    
    def get_repo_owner(self, default: Optional[str] = None) -> Optional[str]:
        """
        Get repository owner with fallback lookups.
        
        Field name variations checked:
        - repo_owner (primary)
        - owner
        - Extracted from repo_name if it's in "owner/repo" format
        
        Uses repo normalizer for consistent format handling.
        
        Returns:
            Normalized repository owner or default
        """
        # Primary field
        repo_owner = self._raw_metadata.get('repo_owner')
        if repo_owner:
            return normalize_repo_owner(repo_owner, default)
        
        # Try to extract from repo_name if it's in "owner/repo" format
        repo_name_raw = self._raw_metadata.get('repo_name') or self._raw_metadata.get('repository') or self._raw_metadata.get('repo')
        if repo_name_raw:
            extracted_owner, _ = extract_repo_parts(repo_name_raw)
            if extracted_owner:
                return extracted_owner
        
        # Check owner field
        owner = self._raw_metadata.get('owner')
        if owner:
            return normalize_repo_owner(owner, default)
        
        return default
    
    def get_language(self, default: Optional[str] = None) -> Optional[str]:
        """
        Get programming language with fallback lookups.
        
        Field name variations checked:
        - language (primary)
        - entities.language
        
        Returns:
            Language string or default
        """
        language = self._raw_metadata.get('language')
        if language:
            return str(language).strip()
        
        # Check nested entities
        entities = self._raw_metadata.get('entities', {})
        if isinstance(entities, dict):
            language = entities.get('language')
            if language:
                return str(language).strip()
        
        return default
    
    def get_content(self, default: Optional[str] = None) -> Optional[str]:
        """
        Get content with fallback lookups.
        
        Field name variations checked:
        - content (primary)
        - full_content
        - text
        - raw
        
        Returns:
            Content string or default
        """
        # Primary field
        content = self._raw_metadata.get('content')
        if content:
            return str(content) if not isinstance(content, dict) else str(content.get('content', ''))
        
        # Fallback fields
        for field in ['full_content', 'text', 'raw']:
            content = self._raw_metadata.get(field)
            if content:
                return str(content)
        
        # Check nested content.content
        if isinstance(self._raw_metadata.get('content'), dict):
            content = self._raw_metadata['content'].get('content')
            if content:
                return str(content)
        
        return default
    
    def get_filename(self, default: Optional[str] = None) -> Optional[str]:
        """
        Get filename with fallback lookups.
        
        Tries to extract from file_path if filename not directly available.
        
        Returns:
            Filename or default
        """
        # Primary field
        filename = self._raw_metadata.get('filename')
        if filename:
            return str(filename).strip()
        
        # Try to extract from file_path using path normalizer
        file_path = self.get_file_path()
        if file_path:
            extracted = extract_filename(file_path)
            if extracted:
                return extracted
        
        # Check nested entities
        entities = self._raw_metadata.get('entities', {})
        if isinstance(entities, dict):
            filename = entities.get('filename')
            if filename:
                return str(filename).strip()
        
        return default
    
    def get_directory(self, default: Optional[str] = None) -> Optional[str]:
        """
        Get directory path with fallback lookups.
        
        Tries to extract from file_path if directory not directly available.
        
        Returns:
            Directory path or default
        """
        # Primary field
        directory = self._raw_metadata.get('directory')
        if directory:
            # Normalize the directory path
            normalized = normalize_path(directory, '')
            return normalized if normalized else default
        
        # Try to extract from file_path using path normalizer
        file_path = self.get_file_path()
        if file_path:
            extracted = extract_directory(file_path)
            if extracted is not None:
                return extracted if extracted else default
        
        # Check nested entities
        entities = self._raw_metadata.get('entities', {})
        if isinstance(entities, dict):
            directory = entities.get('directory')
            if directory:
                # Normalize the directory path
                normalized = normalize_path(directory, '')
                return normalized if normalized else default
        
        return default
    
    def get_issue_number(self, default: Optional[int] = None) -> Optional[int]:
        """Get issue number with fallback lookups."""
        issue_number = self._raw_metadata.get('issue_number')
        if issue_number is not None:
            try:
                return int(issue_number)
            except (ValueError, TypeError):
                pass
        
        # Check issue_id format "#123"
        issue_id = self._raw_metadata.get('issue_id', '')
        if issue_id and isinstance(issue_id, str) and issue_id.startswith('#'):
            try:
                return int(issue_id[1:])
            except ValueError:
                pass
        
        # Check number field
        number = self._raw_metadata.get('number')
        if number is not None and self.get_chunk_type() == 'issue':
            try:
                return int(number)
            except (ValueError, TypeError):
                pass
        
        return default
    
    def get_pr_number(self, default: Optional[int] = None) -> Optional[int]:
        """Get PR number with fallback lookups."""
        pr_number = self._raw_metadata.get('pr_number')
        if pr_number is not None:
            try:
                return int(pr_number)
            except (ValueError, TypeError):
                pass
        
        # Check pr_id format "#123"
        pr_id = self._raw_metadata.get('pr_id', '')
        if pr_id and isinstance(pr_id, str) and pr_id.startswith('#'):
            try:
                return int(pr_id[1:])
            except ValueError:
                pass
        
        # Check number field
        number = self._raw_metadata.get('number')
        if number is not None and self.get_chunk_type() in ['pr', 'pull_request']:
            try:
                return int(number)
            except (ValueError, TypeError):
                pass
        
        return default
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get any metadata field with fallback to nested structures.
        
        This is a safe getter that also checks nested structures like 'entities'.
        """
        # Direct access
        if key in self._raw_metadata:
            return self._raw_metadata[key]
        
        # Check nested entities
        entities = self._raw_metadata.get('entities', {})
        if isinstance(entities, dict) and key in entities:
            return entities[key]
        
        return default
    
    def normalize(self) -> Dict[str, Any]:
        """
        Return a normalized metadata dictionary with all standard field names.
        
        This creates a new dict with standardized field names while preserving
        all original fields for backward compatibility.
        """
        normalized = {}
        
        # Copy all original fields (backward compatibility)
        normalized.update(self._raw_metadata)
        
        # Add normalized fields (standard names)
        file_path = self.get_file_path()
        if file_path:
            normalized['file_path'] = file_path
        
        chunk_type = self.get_chunk_type()
        if chunk_type:
            normalized['chunk_type'] = chunk_type
            normalized['type'] = chunk_type  # Alias for backward compat
        
        repo_name = self.get_repo_name()
        if repo_name:
            normalized['repo_name'] = repo_name
        
        repo_owner = self.get_repo_owner()
        if repo_owner:
            normalized['repo_owner'] = repo_owner
        
        language = self.get_language()
        if language:
            normalized['language'] = language
        
        filename = self.get_filename()
        if filename:
            normalized['filename'] = filename
        
        directory = self.get_directory()
        if directory:
            normalized['directory'] = directory
        
        issue_number = self.get_issue_number()
        if issue_number is not None:
            normalized['issue_number'] = issue_number
        
        pr_number = self.get_pr_number()
        if pr_number is not None:
            normalized['pr_number'] = pr_number

        # 🔥 ADD THIS BLOCK
        merged_by = self.get('merged_by')
        if merged_by:
            normalized['merged_by'] = merged_by

        # 🔥 Temporal fields (PR / Issue lifecycle)
        created_at = self.get_created_at()
        if created_at:
            normalized["created_at"] = created_at

        merged_at = self.get_merged_at()
        if merged_at:
            normalized["merged_at"] = merged_at

        closed_at = self.get_closed_at()
        if closed_at:
            normalized["closed_at"] = closed_at

        
        return normalized
    
    def _normalize_path(self, path: Any) -> str:
        """Normalize file path using path normalizer."""
        if not path:
            return ''
        # Use centralized path normalizer for consistency
        normalized = normalize_path(path, '')
        return normalized if normalized else ''
    
    def _extract_repo_name(self, repo_value: Any) -> str:
        """Extract repository name from various formats (legacy method, uses repo normalizer)."""
        if not repo_value:
            return ''
        # Use repo normalizer for consistent extraction
        normalized = normalize_repo_name(repo_value, '')
        return normalized if normalized else ''


# Convenience functions for quick access
def get_file_path(metadata: Union[Dict[str, Any], Any], result_dict: Optional[Dict[str, Any]] = None, default: Optional[str] = None) -> Optional[str]:
    """Quick access to file_path."""
    normalizer = MetadataNormalizer(metadata, result_dict)
    return normalizer.get_file_path(default)


def get_chunk_type(metadata: Union[Dict[str, Any], Any], result_dict: Optional[Dict[str, Any]] = None, default: Optional[str] = None) -> Optional[str]:
    """Quick access to chunk_type."""
    normalizer = MetadataNormalizer(metadata, result_dict)
    return normalizer.get_chunk_type(default)


def get_repo_name(metadata: Union[Dict[str, Any], Any], result_dict: Optional[Dict[str, Any]] = None, default: Optional[str] = None) -> Optional[str]:
    """Quick access to repo_name."""
    normalizer = MetadataNormalizer(metadata, result_dict)
    return normalizer.get_repo_name(default)


def normalize_metadata(metadata: Union[Dict[str, Any], Any], result_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Quick access to normalized metadata dict."""
    normalizer = MetadataNormalizer(metadata, result_dict)
    return normalizer.normalize()

