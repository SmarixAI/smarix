"""
Repository filtering and utility functions for retrieval.
"""
from typing import List, Dict, Any, Optional


class RepoFilterMixin:
    """Mixin for repository-based filtering utilities."""
    
    def _get_repo_filters(self) -> Optional[Dict[str, Any]]:
        """Get repo-based filters for VectorDB search - STRICT filtering by both owner and repo name"""
        repo_owner = getattr(self, 'repo_owner', None)
        repo_name = getattr(self, 'repo_name', None)
        
        if not repo_owner or not repo_name:
            return None
        
        # Return filter that matches BOTH owner and repo name
        return {"repo_name": repo_name, "repo_owner": repo_owner}
    
    def _filter_by_repo(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Post-retrieval filtering to ensure only current repo chunks are returned - STRICT filtering"""
        repo_owner = getattr(self, 'repo_owner', None)
        repo_name = getattr(self, 'repo_name', None)
        
        # If repo info not available, return empty (don't return results from unknown repos)
        if not repo_owner or not repo_name:
            if results:
                self.logger.warning(f"FILTER | No repo info available, filtering out {len(results)} results")
            return []
        
        filtered = []
        for result in results:
            metadata = result.get('metadata', {})
            chunk_repo = metadata.get('repo_name', '').strip()
            chunk_owner = metadata.get('repo_owner', '').strip()
            
            # STRICT matching: BOTH owner AND repo name must match
            # Accept if:
            # 1. Full format matches: "owner/repo" == "owner/repo"
            # 2. Both owner and repo name match separately
            matches = False
            
            # Check full format first
            if chunk_repo == f"{repo_owner}/{repo_name}":
                matches = True
            # Check separate owner and repo name (both must match)
            elif chunk_owner == repo_owner and chunk_repo == repo_name:
                matches = True
            # If repo_name is stored as just the name (without owner), check owner separately
            elif chunk_repo == repo_name and chunk_owner == repo_owner:
                matches = True
            
            if matches:
                filtered.append(result)
        
        if len(filtered) < len(results):
            self.logger.info(f"FILTER | Filtered {len(results)} -> {len(filtered)} results for repo {repo_owner}/{repo_name}")
        
        return filtered

