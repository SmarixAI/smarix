"""
Direct issue lookup by exact issue number match.
Enables fast retrieval of specific issues without vector search.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path


class IssueDirectLookup:
    """Direct lookup for issue chunks by issue number."""
    
    def __init__(self, issue_chunks_path: str = None):
        """
        Initialize issue direct lookup.
        
        Args:
            issue_chunks_path: Path to issue_chunks.json file. If None, tries to locate it automatically.
        """
        self.logger = logging.getLogger(__name__)
        self.issue_chunks_path = issue_chunks_path
        self.issue_map = {}  # Map of issue number -> issue chunk data
        self.loaded = False
        
        # Try to load from provided path or auto-locate
        if self.issue_chunks_path:
            self._load_from_path(self.issue_chunks_path)
        else:
            self._auto_locate_and_load()
    
    def _auto_locate_and_load(self):
        """Automatically locate issue_chunks.json in standard locations."""
        possible_paths = [
            # Standard location in CCExtractor taskwarrior-flutter repo
            Path(__file__).parent.parent.parent.parent / "data" / "DataProcessing" / 
            "CCExtractor" / "taskwarrior-flutter" / "chunks" / "issue_chunks.json",
            # Alternative relative paths
            Path.cwd() / "data" / "DataProcessing" / "CCExtractor" / 
            "taskwarrior-flutter" / "chunks" / "issue_chunks.json",
        ]
        
        for path in possible_paths:
            if path.exists():
                self._load_from_path(str(path))
                return
        
        self.logger.warning("Could not auto-locate issue_chunks.json, issue direct lookup disabled")
    
    def _load_from_path(self, path: str):
        """Load and index issue chunks from JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            # Index all issue chunks by issue number
            for chunk in chunks:
                if chunk.get('type') == 'issue':
                    issue_number = chunk.get('entities', {}).get('issue_number')
                    if issue_number is not None:
                        self.issue_map[int(issue_number)] = chunk
            
            self.loaded = True
            self.issue_chunks_path = path
            self.logger.info(f"✅ Loaded {len(self.issue_map)} issue chunks for direct lookup from {path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load issue chunks from {path}: {e}")
            self.loaded = False
    
    def lookup_by_number(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """
        Look up an issue by its exact number.
        
        Args:
            issue_number: The issue number to look up
            
        Returns:
            Issue chunk data if found, None otherwise
        """
        if not self.loaded:
            return None
        
        return self.issue_map.get(int(issue_number))
    
    def lookup_by_number_str(self, issue_number_str: str) -> Optional[Dict[str, Any]]:
        """
        Look up an issue by number given as string.
        Handles formats like "563", "#563", "issue#563", etc.
        
        Args:
            issue_number_str: Issue number as string (can include # prefix)
            
        Returns:
            Issue chunk data if found, None otherwise
        """
        if not self.loaded:
            return None
        
        try:
            # Extract just the number part
            clean_number = ''.join(filter(str.isdigit, issue_number_str))
            if clean_number:
                issue_number = int(clean_number)
                return self.lookup_by_number(issue_number)
        except (ValueError, TypeError):
            pass
        
        return None
    
    def extract_issue_number_from_query(self, query: str) -> Optional[int]:
        """
        Extract issue number from query text.
        Looks for patterns like "issue 563", "issue#563", "#563", "bug 563", etc.
        
        Args:
            query: The query text
            
        Returns:
            Issue number if found, None otherwise
        """
        import re
        
        # Patterns to match: "issue 563", "issue#563", "#563", "bug 563", etc.
        patterns = [
            r'(?:issue|bug|ticket|problem)\s*#?(\d+)',  # "issue 563" or "issue#563"
            r'#(\d+)',  # "#563"
            r'issue(\d+)',  # "issue563"
        ]
        
        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                try:
                    issue_number = int(match.group(1))
                    self.logger.debug(f"ISSUE_LOOKUP | Extracted issue #{issue_number} from query using pattern: {pattern}")
                    return issue_number
                except (ValueError, IndexError):
                    pass
        
        self.logger.debug(f"ISSUE_LOOKUP | No issue number pattern matched in query")
        return None
    
    def check_and_retrieve(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Check if query contains an issue number reference and retrieve it if found.
        This is the main entry point for integration with the chatbot.
        
        Args:
            query: The user query
            
        Returns:
            Issue chunk data if an issue was found and loaded, None otherwise
        """
        if not self.loaded:
            self.logger.debug("ISSUE_LOOKUP | check_and_retrieve: Issue lookup not loaded, returning None")
            return None
        
        issue_number = self.extract_issue_number_from_query(query)
        
        if issue_number is not None:
            self.logger.debug(f"ISSUE_LOOKUP | check_and_retrieve: Extracted issue #{issue_number} from query: '{query[:80]}'")
            issue_data = self.lookup_by_number(issue_number)
            if issue_data:
                self.logger.info(f"✅ ISSUE_LOOKUP | check_and_retrieve: Found issue #{issue_number} in database")
                return issue_data
            else:
                self.logger.info(f"⚠️ ISSUE_LOOKUP | check_and_retrieve: Issue #{issue_number} not found in database")
        else:
            self.logger.debug(f"ISSUE_LOOKUP | check_and_retrieve: No issue number extracted from query: '{query[:80]}'")
        
        return None
    
    def get_available_issue_numbers(self) -> List[int]:
        """Get list of all available issue numbers for validation."""
        if not self.loaded:
            return []
        return sorted(self.issue_map.keys())
    
    def is_loaded(self) -> bool:
        """Check if issue chunks are loaded."""
        return self.loaded


# Global singleton instance
_issue_lookup_instance: Optional[IssueDirectLookup] = None


def get_issue_lookup(issue_chunks_path: str = None) -> IssueDirectLookup:
    """
    Get the global issue lookup instance (singleton pattern).
    
    Args:
        issue_chunks_path: Optional path to issue chunks JSON. Only used on first call.
        
    Returns:
        IssueDirectLookup instance
    """
    global _issue_lookup_instance
    
    if _issue_lookup_instance is None:
        _issue_lookup_instance = IssueDirectLookup(issue_chunks_path)
    
    return _issue_lookup_instance
