"""
Repository information loading utilities.
"""
from typing import Dict, Any, Optional
from pathlib import Path
import json
import re
from utils.metadata_normalizer import MetadataNormalizer


class RepositoryInfoMixin:
    """Mixin for loading repository information and metrics."""
    
    def load_repo_info(self) -> Dict[str, Any]:
        """
        Load repository information from database or multi-index store.
        Extracts repository name from path, metadata, or config files.
        """
        stats = {'total_vectors': 0}
        repo_name = None
        
        # Try to get stats and repo name from multi-index store first
        if self.multi_index_store:
            try:
                stats = self.multi_index_store.get_statistics()
                
                # Try to get repo name from metadata in any index
                for index_type in ['code', 'documentation', 'pr', 'email']:
                    index_db = self.multi_index_store.indices.get(index_type)
                    if index_db and hasattr(index_db, 'metadata') and index_db.metadata:
                        try:
                            # Check first few metadata entries for repo name
                            for meta in index_db.metadata[:10]:
                                if isinstance(meta, dict):
                                    # Use metadata normalizer for unified access
                                    meta_norm = MetadataNormalizer(meta)
                                    potential_name = meta_norm.get_repo_name()
                                    
                                    # Also check file_path for repo-like patterns
                                    if not potential_name:
                                        file_path = meta_norm.get_file_path()
                                        if file_path:
                                            # Extract repo name from file path (e.g., CCExtractor_taskwarrior-flutter_data/...)
                                            match = re.search(r'([A-Z][A-Za-z0-9_-]+(?:[_-][A-Za-z0-9_-]+)*)', str(file_path))
                                            if match:
                                                potential_name = match.group(1)
                                    
                                    if potential_name and potential_name.lower() not in ['data', 'vectordb', 'multi_index', 'vector_db', 'backend', 'core']:
                                        repo_name = potential_name
                                        break
                            if repo_name:
                                break
                        except Exception as e:
                            self.logger.debug(f"Error accessing metadata from {index_type}: {e}")
                            continue
                
                # If not found in metadata, try to extract from path
                if not repo_name:
                    path_str = str(self.vector_db_path)
                    # Look for patterns like CCExtractor_taskwarrior-flutter_data in path
                    # Match repository-like names (alphanumeric with underscores/hyphens)
                    matches = re.findall(r'([A-Z][A-Za-z0-9_-]+(?:[_-][A-Za-z0-9_-]+)*)', path_str)
                    for match in matches:
                        # Skip generic directory names
                        if match.lower() not in ['data', 'vectordb', 'multi_index', 'vector_db', 'backend', 'core']:
                            repo_name = match
                            break
                
            except Exception as e:
                self.logger.warning(f"Failed to get multi-index stats: {e}")
        
        
        # Clean up the repo name
        if repo_name:
            # Remove common prefixes/suffixes
            repo_name = repo_name.replace('_unknown_chunks', '').replace('_chunks', '')
            repo_name = repo_name.replace('_embeddings', '').replace('_git', '')
            repo_name = repo_name.replace('.faiss', '').replace('_db', '')
            
            # Skip if it's still a generic name
            if repo_name.lower() in ['data', 'vectordb', 'multi_index', 'vector_db', 'backend', 'core', 'no-github-db']:
                repo_name = None
        
        # Final fallback
        if not repo_name or repo_name == 'no-github-db':
            repo_name = 'this repository'
        else:
            # Format the name nicely (replace underscores/hyphens with spaces, capitalize)
            repo_name = repo_name.replace('_', ' ').replace('-', ' ')
            # Capitalize first letter of each word, but preserve acronyms
            words = repo_name.split()
            formatted_words = []
            for word in words:
                # If it's all caps (acronym), keep it
                if word.isupper() and len(word) > 1:
                    formatted_words.append(word)
                else:
                    formatted_words.append(word.capitalize())
            repo_name = ' '.join(formatted_words)
        
        return {
            'name': repo_name,
            'total_chunks': stats.get('total_vectors', 0)
        }

    def load_repository_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Load repository metrics/tech stack for the CURRENT repo.
        Uses ONLY repo-specific files from the standard location.
        No hardcoded paths, no fallbacks, no environment overrides.
        
        Location: DataProcessing/{owner}/{repo}/techstack.json
        Repo info comes from chatbot attributes or runtime_state.json
        
        Returns None if repo-specific file not found.
        """
        # Get current repo info
        repo_owner = getattr(self, 'repo_owner', None)
        repo_name = getattr(self, 'repo_name', None)
        
        # Try to load from runtime_state.json if repo info not available
        if not repo_owner or not repo_name:
            try:
                possible_state_files = [
                    Path(__file__).resolve().parents[3] / "data" / "Admin" / "state" / "runtime_state.json",
                    Path("../../data/Admin/state/runtime_state.json"),
                    Path("data/Admin/state/runtime_state.json"),
                    Path("backend/data/Admin/state/runtime_state.json"),
                ]
                
                for state_file in possible_state_files:
                    if state_file.exists():
                        with open(state_file, 'r', encoding='utf-8') as f:
                            state = json.load(f)
                            curr_repo = state.get("curr_repo", {})
                            repo_owner = curr_repo.get("owner") or repo_owner
                            repo_name = curr_repo.get("name") or repo_name
                            if repo_owner and repo_name:
                                break
            except Exception as e:
                if self.verbose:
                    print(f"Could not load repo from runtime_state.json: {e}")
        
        # PRIORITY 1: Repo-specific techstack.json file
        if repo_owner and repo_name:
            repo_specific_paths = [
                Path(__file__).resolve().parents[3] / "data" / "DataProcessing" / repo_owner / repo_name / "techstack.json",
                Path("../../data/DataProcessing") / repo_owner / repo_name / "techstack.json",
                Path("data/DataProcessing") / repo_owner / repo_name / "techstack.json",
                Path("backend/data/DataProcessing") / repo_owner / repo_name / "techstack.json",
            ]
            
            for path in repo_specific_paths:
                if path.exists():
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            metrics = json.load(f)
                            # Wrap in expected format
                            result = {
                                'repositories': {f"{repo_owner}/{repo_name}": metrics},
                                'summary': metrics  # Use repo-specific metrics as summary
                            }
                            if self.verbose:
                                print(f"✅ Loaded repo-specific metrics from: {path}")
                            return result
                    except Exception as e:
                        if self.verbose:
                            print(f"Error loading repo-specific metrics from {path}: {e}")
                        continue
        
        # No fallbacks - only use repo-specific files from the standard location
        if self.verbose:
            repo_display = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else "unknown"
            print(f"❌ No repository metrics file found for repo: {repo_display}")
            print(f"   Expected location: data/DataProcessing/{repo_owner}/{repo_name}/techstack.json")
            print(f"   Run data processing to generate this file for the current repo.")

        return None

