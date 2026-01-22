"""
Fuzzy file matching utilities for handling typos and variations in file queries.
"""
from typing import List, Tuple
import re
from difflib import SequenceMatcher


def fuzzy_match_filename(query: str, filename: str, threshold: float = 0.7) -> Tuple[bool, float]:
    """
    Perform fuzzy matching between query and filename.
    
    Args:
        query: Query string (e.g., "filter" or "filtar")
        filename: Actual filename (e.g., "filters.dart")
        threshold: Similarity threshold (0.0 to 1.0)
        
    Returns:
        Tuple of (is_match, similarity_score)
    """
    query_lower = query.lower().strip()
    filename_lower = filename.lower().strip()
    
    # Remove extension for comparison
    query_base = query_lower.rsplit('.', 1)[0] if '.' in query_lower else query_lower
    filename_base = filename_lower.rsplit('.', 1)[0] if '.' in filename_lower else filename_lower
    
    # Exact match
    if query_base == filename_base:
        return True, 1.0
    
    # Contains match
    if query_base in filename_base or filename_base in query_base:
        return True, 0.9
    
    # Fuzzy match using SequenceMatcher
    similarity = SequenceMatcher(None, query_base, filename_base).ratio()
    
    if similarity >= threshold:
        return True, similarity
    
    return False, similarity


def find_similar_filenames(query: str, filenames: List[str], limit: int = 5) -> List[Tuple[str, float]]:
    """
    Find similar filenames to the query.
    
    Args:
        query: Query string
        filenames: List of candidate filenames
        limit: Maximum number of results
        
    Returns:
        List of (filename, similarity_score) tuples, sorted by similarity
    """
    matches = []
    
    for filename in filenames:
        is_match, similarity = fuzzy_match_filename(query, filename, threshold=0.6)
        if is_match:
            matches.append((filename, similarity))
    
    # Sort by similarity (descending)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches[:limit]


def extract_file_query_components(query: str) -> dict:
    """
    Extract multiple file queries from a single query.
    
    Examples:
        "show me filters.dart and users.dart" -> ["filters.dart", "users.dart"]
        "filters.dart, users.dart, auth.dart" -> ["filters.dart", "users.dart", "auth.dart"]
        
    Args:
        query: User query string
        
    Returns:
        Dict with:
        - file_queries: List of individual file queries
        - is_multiple: bool indicating if multiple files requested
    """
    # Patterns for multiple file queries
    patterns = [
        r'([\w\-_./\\]+\.(?:py|js|ts|dart|java|go|rs|cpp|c|h|hpp|md|txt|json|yaml|yml|xml|html|css|scss|less|vue|jsx|tsx|kt|swift|rb|php))',
    ]
    
    file_queries = []
    
    # Find all file patterns
    for pattern in patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        file_queries.extend(matches)
    
    # Also check for comma/and separated files
    if ' and ' in query.lower() or ', ' in query:
        # Split by "and" or comma
        parts = re.split(r'\s+and\s+|,\s*', query, flags=re.IGNORECASE)
        for part in parts:
            part = part.strip()
            # Check if part looks like a file
            if re.search(r'\.(py|js|ts|dart|java|go|rs|cpp|c|h|hpp|md|txt|json|yaml|yml)', part, re.IGNORECASE):
                if part not in file_queries:
                    file_queries.append(part)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_queries = []
    for q in file_queries:
        q_lower = q.lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique_queries.append(q)
    
    return {
        'file_queries': unique_queries,
        'is_multiple': len(unique_queries) > 1
    }

