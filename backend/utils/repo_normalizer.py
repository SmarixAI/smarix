"""
Repo Normalizer - Unified repository name/owner normalization

This module provides consistent repository name and owner normalization across
the codebase, handling all format variations (case, whitespace, URLs, formats)
and ensuring repo matching works reliably.

Usage:
    from utils.repo_normalizer import normalize_repo_name, normalize_repo_owner, RepoNormalizer
    
    # Quick functions
    normalized = normalize_repo_name("Owner/Repo")
    # Returns: "repo"
    
    owner = normalize_repo_owner("https://github.com/Owner/Repo")
    # Returns: "owner"
    
    # Class-based (more control)
    normalizer = RepoNormalizer()
    normalized = normalizer.normalize_name("owner-repo")
    owner = normalizer.extract_owner("github.com/owner/repo")
"""

from typing import Optional, Tuple, Union
import re
import logging

logger = logging.getLogger(__name__)


class RepoNormalizer:
    """
    Normalizes repository names and owners to a consistent format.
    
    Handles:
    - Case variations (Owner/Repo -> owner/repo)
    - Whitespace trimming
    - URL formats (github.com/owner/repo, https://github.com/owner/repo.git)
    - Format variations (owner-repo, owner_repo, owner.repo)
    - Extraction from full format (owner/repo -> owner and repo)
    - Special characters and edge cases
    """
    
    def __init__(self, case_sensitive: bool = False):
        """
        Initialize repo normalizer.
        
        Args:
            case_sensitive: If True, preserve case. Default False for flexible matching.
        """
        self.case_sensitive = case_sensitive
    
    def normalize_name(self, repo_name: Union[str, None], default: Optional[str] = None) -> Optional[str]:
        """
        Normalize a repository name to consistent format.
        
        Args:
            repo_name: Repository name to normalize (can be full format "owner/repo" or just "repo")
            default: Default value to return if repo_name is empty/None
            
        Returns:
            Normalized repository name (just the name, without owner) or default
            
        Examples:
            >>> normalizer = RepoNormalizer()
            >>> normalizer.normalize_name("Owner/Repo")
            "repo"
            >>> normalizer.normalize_name("owner-repo")
            "owner-repo"
            >>> normalizer.normalize_name("  MyRepo  ")
            "myrepo"
        """
        if repo_name is None:
            return default
        
        repo_str = str(repo_name).strip()
        
        if not repo_str:
            return default
        
        # Skip URLs - extract repo name from URL first
        if self._is_url(repo_str):
            _, extracted_repo = self._extract_from_url(repo_str)
            if extracted_repo:
                repo_str = extracted_repo
            else:
                return default
        
        # Extract just the repo name if it's in "owner/repo" format
        if '/' in repo_str:
            parts = repo_str.split('/')
            if len(parts) == 2:
                repo_str = parts[1].strip()
            elif len(parts) > 2:
                # URL-like format, take last part
                repo_str = parts[-1].strip()
        
        # Remove .git suffix if present
        if repo_str.endswith('.git'):
            repo_str = repo_str[:-4]
        
        # Normalize case (unless case_sensitive)
        if not self.case_sensitive:
            repo_str = repo_str.lower()
        
        # Remove leading/trailing whitespace
        repo_str = repo_str.strip()
        
        return repo_str if repo_str else default
    
    def normalize_owner(self, repo_owner: Union[str, None], default: Optional[str] = None) -> Optional[str]:
        """
        Normalize a repository owner to consistent format.
        
        Args:
            repo_owner: Repository owner to normalize
            default: Default value to return if repo_owner is empty/None
            
        Returns:
            Normalized owner name or default
            
        Examples:
            >>> normalizer = RepoNormalizer()
            >>> normalizer.normalize_owner("  Owner  ")
            "owner"
            >>> normalizer.normalize_owner("OWNER")
            "owner"
        """
        if repo_owner is None:
            return default
        
        owner_str = str(repo_owner).strip()
        
        if not owner_str:
            return default
        
        # Extract from URL if needed
        if self._is_url(owner_str):
            extracted_owner, _ = self._extract_from_url(owner_str)
            if extracted_owner:
                owner_str = extracted_owner
            else:
                return default
        
        # Normalize case (unless case_sensitive)
        if not self.case_sensitive:
            owner_str = owner_str.lower()
        
        # Remove leading/trailing whitespace
        owner_str = owner_str.strip()
        
        return owner_str if owner_str else default
    
    def extract_from_full_format(self, repo_string: Union[str, None]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract owner and repo name from full format string.
        
        Handles formats like:
        - "owner/repo"
        - "https://github.com/owner/repo"
        - "git@github.com:owner/repo.git"
        - "owner-repo" (treats as repo name only)
        
        Args:
            repo_string: Full repository string in various formats
            
        Returns:
            Tuple of (owner, repo_name) or (None, repo_name) if owner not found
            
        Examples:
            >>> normalizer = RepoNormalizer()
            >>> normalizer.extract_from_full_format("Owner/Repo")
            ("owner", "repo")
            >>> normalizer.extract_from_full_format("https://github.com/owner/repo.git")
            ("owner", "repo")
            >>> normalizer.extract_from_full_format("just-repo")
            (None, "just-repo")
        """
        if not repo_string:
            return (None, None)
        
        repo_str = str(repo_string).strip()
        
        if not repo_str:
            return (None, None)
        
        # Handle URL formats
        if self._is_url(repo_str):
            owner, repo = self._extract_from_url(repo_str)
            return (self.normalize_owner(owner), self.normalize_name(repo))
        
        # Handle "owner/repo" format
        if '/' in repo_str:
            parts = repo_str.split('/')
            if len(parts) >= 2:
                owner_part = parts[-2].strip()
                repo_part = parts[-1].strip()
                # Remove .git suffix
                if repo_part.endswith('.git'):
                    repo_part = repo_part[:-4]
                return (self.normalize_owner(owner_part), self.normalize_name(repo_part))
        
        # If no slash, treat as repo name only
        return (None, self.normalize_name(repo_str))
    
    def normalize_full_repo(self, owner: Optional[str], repo_name: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Normalize both owner and repo name, handling various input formats.
        
        Args:
            owner: Owner string (can be None)
            repo_name: Repo name string (can be in "owner/repo" format)
            
        Returns:
            Tuple of (normalized_owner, normalized_repo_name)
            
        Examples:
            >>> normalizer = RepoNormalizer()
            >>> normalizer.normalize_full_repo("Owner", "Repo")
            ("owner", "repo")
            >>> normalizer.normalize_full_repo(None, "Owner/Repo")
            ("owner", "repo")
        """
        normalized_owner = None
        normalized_repo = None
        
        # If repo_name contains owner/repo format, extract both
        if repo_name and '/' in str(repo_name):
            extracted_owner, extracted_repo = self.extract_from_full_format(repo_name)
            if extracted_owner:
                normalized_owner = extracted_owner
            if extracted_repo:
                normalized_repo = extracted_repo
        
        # Normalize owner if provided separately
        if owner:
            normalized_owner = self.normalize_owner(owner)
        
        # Normalize repo name if not already extracted
        if repo_name and not normalized_repo:
            normalized_repo = self.normalize_name(repo_name)
        
        return (normalized_owner, normalized_repo)
    
    def matches(self, 
                owner1: Optional[str], repo1: Optional[str],
                owner2: Optional[str], repo2: Optional[str]) -> bool:
        """
        Check if two repo identifiers match (flexible matching).
        
        Args:
            owner1, repo1: First repo identifier
            owner2, repo2: Second repo identifier
            
        Returns:
            True if repos match (considering format variations)
            
        Examples:
            >>> normalizer = RepoNormalizer()
            >>> normalizer.matches("Owner", "Repo", "owner", "repo")
            True
            >>> normalizer.matches("Owner", "Repo", None, "Owner/Repo")
            True
        """
        # Normalize both
        norm_owner1, norm_repo1 = self.normalize_full_repo(owner1, repo1)
        norm_owner2, norm_repo2 = self.normalize_full_repo(owner2, repo2)
        
        # Both must have repo names
        if not norm_repo1 or not norm_repo2:
            return False
        
        # Repo names must match
        if norm_repo1 != norm_repo2:
            return False
        
        # If both have owners, they must match
        if norm_owner1 and norm_owner2:
            return norm_owner1 == norm_owner2
        
        # If only one has owner, still match (flexible)
        # This handles cases where owner is missing in one but repo name matches
        return True
    
    def _is_url(self, repo_string: str) -> bool:
        """Check if string looks like a URL."""
        url_patterns = [
            r'^https?://',
            r'^git@',
            r'^ssh://',
            r'\.git$',
            r'github\.com',
            r'gitlab\.com',
            r'bitbucket\.org'
        ]
        return any(re.search(pattern, repo_string, re.IGNORECASE) for pattern in url_patterns)
    
    def _extract_from_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract owner and repo from URL format.
        
        Handles:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        - ssh://git@github.com/owner/repo.git
        """
        if not url:
            return (None, None)
        
        # Remove protocol
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^ssh://', '', url)
        url = re.sub(r'^git@', '', url)
        
        # Remove .git suffix
        url = url.rstrip('/')
        if url.endswith('.git'):
            url = url[:-4]
        
        # Extract domain and path
        # Pattern: domain.com/owner/repo or domain.com:owner/repo
        match = re.search(r'(?:github\.com|gitlab\.com|bitbucket\.org)[:/]([^/]+)/([^/]+)', url, re.IGNORECASE)
        if match:
            owner = match.group(1).strip()
            repo = match.group(2).strip()
            return (owner, repo)
        
        # Try generic pattern: anything/owner/repo
        parts = url.split('/')
        if len(parts) >= 3:
            # Skip domain, take owner and repo
            owner = parts[-2].strip()
            repo = parts[-1].strip()
            return (owner, repo)
        
        return (None, None)


# Global instance with default settings
_default_normalizer = RepoNormalizer(case_sensitive=False)


def normalize_repo_name(repo_name: Union[str, None], default: Optional[str] = None, 
                       case_sensitive: bool = False) -> Optional[str]:
    """
    Quick function to normalize a repository name.
    
    Args:
        repo_name: Repository name to normalize
        default: Default value if repo_name is empty/None
        case_sensitive: If True, preserve case
        
    Returns:
        Normalized repository name
        
    Examples:
        >>> normalize_repo_name("Owner/Repo")
        "repo"
        >>> normalize_repo_name("  MyRepo  ")
        "myrepo"
        >>> normalize_repo_name("https://github.com/owner/repo.git")
        "repo"
    """
    if case_sensitive != _default_normalizer.case_sensitive:
        normalizer = RepoNormalizer(case_sensitive=case_sensitive)
        return normalizer.normalize_name(repo_name, default)
    
    return _default_normalizer.normalize_name(repo_name, default)


def normalize_repo_owner(repo_owner: Union[str, None], default: Optional[str] = None,
                         case_sensitive: bool = False) -> Optional[str]:
    """Quick function to normalize a repository owner."""
    if case_sensitive != _default_normalizer.case_sensitive:
        normalizer = RepoNormalizer(case_sensitive=case_sensitive)
        return normalizer.normalize_owner(repo_owner, default)
    
    return _default_normalizer.normalize_owner(repo_owner, default)


def extract_repo_parts(repo_string: Union[str, None]) -> Tuple[Optional[str], Optional[str]]:
    """Quick function to extract owner and repo from full format."""
    return _default_normalizer.extract_from_full_format(repo_string)


def repo_matches(owner1: Optional[str], repo1: Optional[str],
                 owner2: Optional[str], repo2: Optional[str]) -> bool:
    """Quick function to check if two repos match."""
    return _default_normalizer.matches(owner1, repo1, owner2, repo2)

