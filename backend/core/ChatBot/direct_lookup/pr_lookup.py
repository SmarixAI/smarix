"""
Direct PR lookup by exact PR number match.
Enables fast retrieval of specific PRs without vector search.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path


class PRDirectLookup:
    """Direct lookup for PR chunks by PR number."""
    
    def __init__(self, pr_chunks_path: str = None):
        """
        Initialize PR direct lookup.
        
        Args:
            pr_chunks_path: Path to pr_chunks.json file. If None, tries to locate it automatically.
        """
        self.logger = logging.getLogger(__name__)
        self.pr_chunks_path = pr_chunks_path
        self.pr_map = {}  # Map of PR number -> PR chunk data
        self.loaded = False
        
        # Try to load from provided path or auto-locate
        if self.pr_chunks_path:
            self._load_from_path(self.pr_chunks_path)
        else:
            self._auto_locate_and_load()
    
    def _auto_locate_and_load(self):
        """Automatically locate pr_chunks.json in standard locations."""
        possible_paths = [
            # Standard location in CCExtractor taskwarrior-flutter repo
            Path(__file__).parent.parent.parent.parent / "data" / "DataProcessing" / 
            "CCExtractor" / "taskwarrior-flutter" / "chunks" / "pr_chunks.json",
            # Alternative relative paths
            Path.cwd() / "data" / "DataProcessing" / "CCExtractor" / 
            "taskwarrior-flutter" / "chunks" / "pr_chunks.json",
        ]
        
        for path in possible_paths:
            if path.exists():
                self._load_from_path(str(path))
                return
        
        self.logger.warning("Could not auto-locate pr_chunks.json, PR direct lookup disabled")
    
    def _load_from_path(self, path: str):
        """Load and index PR chunks from JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            # Index all PR chunks by PR number
            for chunk in chunks:
                if chunk.get('type') == 'pr':
                    pr_number = chunk.get('entities', {}).get('pr_number')
                    if pr_number is not None:
                        self.pr_map[int(pr_number)] = chunk
            
            self.loaded = True
            self.pr_chunks_path = path
            self.logger.info(f"✅ Loaded {len(self.pr_map)} PR chunks for direct lookup from {path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load PR chunks from {path}: {e}")
            self.loaded = False
    
    def lookup_by_number(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Look up a PR by its exact number.
        
        Args:
            pr_number: The PR number to look up
            
        Returns:
            PR chunk data if found, None otherwise
        """
        if not self.loaded:
            return None
        
        return self.pr_map.get(int(pr_number))
    
    def lookup_by_number_str(self, pr_number_str: str) -> Optional[Dict[str, Any]]:
        """
        Look up a PR by number given as string.
        Handles formats like "565", "#565", "PR#565", etc.
        
        Args:
            pr_number_str: PR number as string (can include # prefix)
            
        Returns:
            PR chunk data if found, None otherwise
        """
        if not self.loaded:
            return None
        
        try:
            # Extract just the number part
            clean_number = ''.join(filter(str.isdigit, pr_number_str))
            if clean_number:
                pr_number = int(clean_number)
                return self.lookup_by_number(pr_number)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def extract_pr_number_from_query(self, query: str) -> Optional[int]:
        """
        Extract PR number from query text.
        Looks for patterns like "PR 565", "PR#565", "#565", "pull request 565", etc.
        
        Args:
            query: The query text
            
        Returns:
            PR number if found, None otherwise
        """
        import re
        
        # Patterns to match: "PR 565", "PR#565", "#565", "pull request 565", etc.
        patterns = [
            r'(?:PR|pull\s+request)\s*#?(\d+)',  # "PR 565" or "PR#565" or "pull request 565"
            r'#(\d+)',  # "#565"
            r'PR(\d+)',  # "PR565"
        ]
        
        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                try:
                    pr_number = int(match.group(1))
                    self.logger.debug(f"PR_LOOKUP | Extracted PR #{pr_number} from query using pattern: {pattern}")
                    return pr_number
                except (ValueError, IndexError):
                    pass
        
        self.logger.debug(f"PR_LOOKUP | No PR number pattern matched in query")
        return None
    
    def check_and_retrieve(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Check if query contains a PR number reference and retrieve it if found.
        This is the main entry point for integration with the chatbot.
        
        Args:
            query: The user query
            
        Returns:
            PR chunk data if a PR was found and loaded, None otherwise
        """
        if not self.loaded:
            self.logger.debug("PR_LOOKUP | check_and_retrieve: PR lookup not loaded, returning None")
            return None
        
        pr_number = self.extract_pr_number_from_query(query)
        
        if pr_number is not None:
            self.logger.debug(f"PR_LOOKUP | check_and_retrieve: Extracted PR #{pr_number} from query: '{query[:80]}'")
            pr_data = self.lookup_by_number(pr_number)
            if pr_data:
                self.logger.info(f"✅ PR_LOOKUP | check_and_retrieve: Found PR #{pr_number} in database")
                return pr_data
            else:
                self.logger.info(f"⚠️ PR_LOOKUP | check_and_retrieve: PR #{pr_number} not found in database")
        else:
            self.logger.debug(f"PR_LOOKUP | check_and_retrieve: No PR number extracted from query: '{query[:80]}'")
        
        return None
    
    def get_available_pr_numbers(self) -> List[int]:
        """Get list of all available PR numbers for validation."""
        if not self.loaded:
            return []
        return sorted(self.pr_map.keys())
    
    def is_loaded(self) -> bool:
        """Check if PR chunks are loaded."""
        return self.loaded


# Global singleton instance
_pr_lookup_instance: Optional[PRDirectLookup] = None


def get_pr_lookup(pr_chunks_path: str = None) -> PRDirectLookup:
    """
    Get the global PR lookup instance (singleton pattern).
    
    Args:
        pr_chunks_path: Optional path to PR chunks JSON. Only used on first call.
        
    Returns:
        PRDirectLookup instance
    """
    global _pr_lookup_instance
    
    if _pr_lookup_instance is None:
        _pr_lookup_instance = PRDirectLookup(pr_chunks_path)
    
    return _pr_lookup_instance
