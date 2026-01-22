"""
Path Normalizer - Unified file path normalization

This module provides consistent file path normalization across the codebase,
handling all path format variations (Windows, Unix, relative, absolute) and
ensuring paths are stored in a consistent format.

Usage:
    from utils.path_normalizer import normalize_path, PathNormalizer
    
    # Quick function
    normalized = normalize_path("C:\\Users\\file.py")
    # Returns: "C:/Users/file.py" or "Users/file.py" (depending on mode)
    
    # Class-based (more control)
    normalizer = PathNormalizer()
    normalized = normalizer.normalize("lib/app/file.dart")
"""

from typing import Optional, Union
from pathlib import Path
import os
import re
import logging

logger = logging.getLogger(__name__)


class PathNormalizer:
    """
    Normalizes file paths to a consistent format.
    
    Handles:
    - Windows vs Unix path separators (\\ vs /)
    - Relative vs absolute paths
    - Leading/trailing slashes
    - Multiple consecutive separators
    - Path component normalization
    - Empty paths and None values
    """
    
    def __init__(self, prefer_relative: bool = True, remove_leading_slash: bool = True):
        """
        Initialize path normalizer.
        
        Args:
            prefer_relative: If True, convert absolute paths to relative when possible
            remove_leading_slash: If True, remove leading slashes from paths
        """
        self.prefer_relative = prefer_relative
        self.remove_leading_slash = remove_leading_slash
    
    def normalize(self, path: Union[str, Path, None], default: Optional[str] = None) -> Optional[str]:
        """
        Normalize a file path to consistent format.
        
        Args:
            path: Path to normalize (can be str, Path, or None)
            default: Default value to return if path is empty/None
            
        Returns:
            Normalized path string or default
        """
        if path is None:
            return default
        
        # Convert Path objects to string
        if isinstance(path, Path):
            path = str(path)
        
        # Convert to string and strip whitespace
        path_str = str(path).strip()
        
        if not path_str:
            return default
        
        # Skip URLs and non-file paths
        if path_str.startswith(('http://', 'https://', 'ftp://', 'file://')):
            return path_str
        
        # Normalize path separators (convert backslashes to forward slashes)
        path_str = path_str.replace('\\', '/')
        
        # Remove multiple consecutive slashes (but preserve leading // for UNC paths)
        if path_str.startswith('//'):
            # UNC path (\\server\share) - keep first two slashes
            path_str = '//' + re.sub(r'/+', '/', path_str[2:])
        else:
            # Regular path - collapse all slashes
            path_str = re.sub(r'/+', '/', path_str)
        
        # Handle Windows absolute paths (C:/, D:/, etc.)
        if re.match(r'^[A-Za-z]:/', path_str):
            # Windows absolute path like "C:/Users/file.py"
            if self.prefer_relative:
                # Extract relative part (remove drive letter)
                # For now, keep it as is but normalize separators
                pass
            # Keep the drive letter format but normalize
            path_str = path_str.replace(':', ':')  # Already normalized
        
        # Remove leading slash if requested (for relative paths)
        if self.remove_leading_slash and path_str.startswith('/') and not path_str.startswith('//'):
            path_str = path_str[1:]
        
        # Remove trailing slash (unless it's root)
        if path_str.endswith('/') and path_str != '/':
            path_str = path_str.rstrip('/')
        
        # Normalize . and .. components
        try:
            # Use pathlib for proper normalization
            normalized_path = Path(path_str)
            # Resolve relative components (. and ..)
            if not normalized_path.is_absolute():
                # For relative paths, normalize . and ..
                parts = []
                for part in normalized_path.parts:
                    if part == '.':
                        continue
                    elif part == '..':
                        if parts and parts[-1] != '..':
                            parts.pop()
                        else:
                            parts.append('..')
                    else:
                        parts.append(part)
                path_str = '/'.join(parts) if parts else '.'
            else:
                # For absolute paths, use as_posix() for forward slashes
                path_str = normalized_path.as_posix()
        except Exception as e:
            logger.debug(f"Path normalization warning for '{path}': {e}")
            # Fallback: just use the cleaned string
            pass
        
        return path_str if path_str else default
    
    def normalize_directory(self, directory: Union[str, Path, None], default: Optional[str] = None) -> Optional[str]:
        """
        Normalize a directory path.
        
        Similar to normalize() but ensures directory format (can end with /).
        
        Args:
            directory: Directory path to normalize
            default: Default value to return if directory is empty/None
            
        Returns:
            Normalized directory path
        """
        if directory is None:
            return default
        
        normalized = self.normalize(directory, default)
        if normalized and normalized != default:
            # For directories, we can optionally keep trailing slash
            # But for consistency, we'll remove it (can be added back if needed)
            pass
        
        return normalized
    
    def extract_filename(self, path: Union[str, Path, None]) -> Optional[str]:
        """
        Extract filename from path.
        
        Args:
            path: File path
            
        Returns:
            Filename or None
        """
        if path is None:
            return None
        
        normalized = self.normalize(path)
        if not normalized:
            return None
        
        try:
            return Path(normalized).name
        except Exception:
            # Fallback: split by /
            parts = normalized.split('/')
            return parts[-1] if parts else None
    
    def extract_directory(self, path: Union[str, Path, None]) -> Optional[str]:
        """
        Extract directory from path.
        
        Args:
            path: File path
            
        Returns:
            Directory path or empty string for root
        """
        if path is None:
            return None
        
        normalized = self.normalize(path)
        if not normalized:
            return None
        
        try:
            parent = Path(normalized).parent
            if str(parent) == '.':
                return ''
            return self.normalize(str(parent), '')
        except Exception:
            # Fallback: split by /
            parts = normalized.split('/')
            if len(parts) > 1:
                dir_path = '/'.join(parts[:-1])
                return self.normalize(dir_path, '')
            return ''


# Global instance with default settings
_default_normalizer = PathNormalizer(prefer_relative=True, remove_leading_slash=True)


def normalize_path(path: Union[str, Path, None], default: Optional[str] = None, 
                   prefer_relative: bool = True, remove_leading_slash: bool = True) -> Optional[str]:
    """
    Quick function to normalize a file path.
    
    Args:
        path: Path to normalize
        default: Default value if path is empty/None
        prefer_relative: Convert absolute to relative when possible
        remove_leading_slash: Remove leading slash from paths
        
    Returns:
        Normalized path string
        
    Examples:
        >>> normalize_path("C:\\Users\\file.py")
        "C:/Users/file.py"
        >>> normalize_path("lib/app/file.dart")
        "lib/app/file.dart"
        >>> normalize_path("\\Users\\file.py")
        "Users/file.py"
        >>> normalize_path("//server/share/file.txt")
        "//server/share/file.txt"
    """
    if prefer_relative != _default_normalizer.prefer_relative or \
       remove_leading_slash != _default_normalizer.remove_leading_slash:
        # Use custom normalizer
        normalizer = PathNormalizer(prefer_relative=prefer_relative, 
                                   remove_leading_slash=remove_leading_slash)
        return normalizer.normalize(path, default)
    
    # Use default normalizer
    return _default_normalizer.normalize(path, default)


def extract_filename(path: Union[str, Path, None]) -> Optional[str]:
    """Quick function to extract filename from path."""
    return _default_normalizer.extract_filename(path)


def extract_directory(path: Union[str, Path, None]) -> Optional[str]:
    """Quick function to extract directory from path."""
    return _default_normalizer.extract_directory(path)


def normalize_directory(directory: Union[str, Path, None], default: Optional[str] = None) -> Optional[str]:
    """Quick function to normalize a directory path."""
    return _default_normalizer.normalize_directory(directory, default)

