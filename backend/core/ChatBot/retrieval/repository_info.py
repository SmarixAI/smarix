"""
Repository information loading utilities - S3 OPTIMIZED
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import re
from utils.metadata_normalizer import MetadataNormalizer
from utils.s3 import s3_manager

# S3 Configuration
S3_BUCKET = "smarix-data"
S3_BASE_PATH = "DataProcessing"


class RepositoryInfoMixin:
    """Mixin for loading repository information and metrics from S3."""

    def load_repo_info(self) -> Dict[str, Any]:
        """
        Load repository information from database or multi-index store.
        Extracts repository name from path, metadata, or config files.
        """
        stats = {"total_vectors": 0}
        repo_name = None

        # Try to get stats and repo name from multi-index store first
        if self.multi_index_store:
            try:
                stats = self.multi_index_store.get_statistics()

                # Try to get repo name from metadata in any index
                for index_type in ["code", "documentation", "pr", "email"]:
                    index_db = self.multi_index_store.indices.get(index_type)
                    if index_db and hasattr(index_db, "metadata") and index_db.metadata:
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
                                            match = re.search(
                                                r"([A-Z][A-Za-z0-9_-]+(?:[_-][A-Za-z0-9_-]+)*)",
                                                str(file_path),
                                            )
                                            if match:
                                                potential_name = match.group(1)

                                    if (
                                        potential_name
                                        and potential_name.lower()
                                        not in [
                                            "data",
                                            "vectordb",
                                            "multi_index",
                                            "vector_db",
                                            "backend",
                                            "core",
                                        ]
                                    ):
                                        repo_name = potential_name
                                        break
                            if repo_name:
                                break
                        except Exception as e:
                            self.logger.debug(
                                f"Error accessing metadata from {index_type}: {e}"
                            )
                            continue

                # If not found in metadata, try to extract from path (handles both S3 and local paths)
                if not repo_name:
                    path_str = str(self.vector_db_path)
                    # Look for patterns like CCExtractor_taskwarrior-flutter_data in path
                    # Match repository-like names (alphanumeric with underscores/hyphens)
                    matches = re.findall(
                        r"([A-Z][A-Za-z0-9_-]+(?:[_-][A-Za-z0-9_-]+)*)", path_str
                    )
                    for match in matches:
                        # Skip generic directory names
                        if match.lower() not in [
                            "data",
                            "vectordb",
                            "multi_index",
                            "vector_db",
                            "backend",
                            "core",
                            "s3",
                            "smarix",
                        ]:
                            repo_name = match
                            break

            except Exception as e:
                self.logger.warning(f"Failed to get multi-index stats: {e}")

        # Clean up the repo name
        if repo_name:
            # Remove common prefixes/suffixes
            repo_name = repo_name.replace("_unknown_chunks", "").replace("_chunks", "")
            repo_name = repo_name.replace("_embeddings", "").replace("_git", "")
            repo_name = repo_name.replace(".faiss", "").replace("_db", "")

            # Skip if it's still a generic name
            if repo_name.lower() in [
                "data",
                "vectordb",
                "multi_index",
                "vector_db",
                "backend",
                "core",
                "no-github-db",
            ]:
                repo_name = None

        # Final fallback
        if not repo_name or repo_name == "no-github-db":
            repo_name = "this repository"
        else:
            # Format the name nicely (replace underscores/hyphens with spaces, capitalize)
            repo_name = repo_name.replace("_", " ").replace("-", " ")
            # Capitalize first letter of each word, but preserve acronyms
            words = repo_name.split()
            formatted_words = []
            for word in words:
                # If it's all caps (acronym), keep it
                if word.isupper() and len(word) > 1:
                    formatted_words.append(word)
                else:
                    formatted_words.append(word.capitalize())
            repo_name = " ".join(formatted_words)

        return {"name": repo_name, "total_chunks": stats.get("total_vectors", 0)}

    def load_repository_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Load repository metrics/tech stack for the CURRENT repo from S3.
        Uses ONLY repo-specific files from S3.
        No hardcoded paths, no fallbacks, no environment overrides.

        Location: s3://bucket/DataProcessing/{owner}/{repo}/techstack.json
        Repo info comes from chatbot attributes or runtime_state.json from S3

        Returns None if repo-specific file not found.
        """
        # Get current repo info
        repo_owner = getattr(self, "repo_owner", None)
        repo_name = getattr(self, "repo_name", None)

        # Try to load from runtime_state.json in S3 if repo info not available
        if not repo_owner or not repo_name:
            try:
                state_s3_key = "Admin/state/runtime_state.json"
                state = s3_manager.download_json(state_s3_key)
                curr_repo = state.get("curr_repo", {})
                repo_owner = curr_repo.get("owner") or repo_owner
                repo_name = curr_repo.get("name") or repo_name

                if self.verbose and repo_owner and repo_name:
                    print(
                        f"📥 Loaded repo info from S3 state: {repo_owner}/{repo_name}"
                    )
            except Exception as e:
                if self.verbose:
                    print(f"⚠️  Could not load repo from runtime_state.json in S3: {e}")

        # Load repo-specific techstack.json from S3
        if repo_owner and repo_name:
            s3_techstack_key = f"{S3_BASE_PATH}/{repo_owner}/{repo_name}/techstack.json"

            try:
                # Check if file exists in S3
                if s3_manager.key_exists(s3_techstack_key):
                    if self.verbose:
                        print(
                            f"📥 Loading repo-specific metrics from S3: s3://{S3_BUCKET}/{s3_techstack_key}"
                        )

                    # Download and parse JSON
                    metrics = s3_manager.download_json(s3_techstack_key)

                    # Wrap in expected format
                    result = {
                        "repositories": {f"{repo_owner}/{repo_name}": metrics},
                        "summary": metrics,  # Use repo-specific metrics as summary
                    }

                    if self.verbose:
                        print(f"✅ Loaded repo-specific metrics from S3")

                    return result
                else:
                    if self.verbose:
                        print(
                            f"⚠️  Techstack file not found in S3: s3://{S3_BUCKET}/{s3_techstack_key}"
                        )

            except Exception as e:
                if self.verbose:
                    print(f"❌ Error loading repo-specific metrics from S3: {e}")

        # No fallbacks - only use repo-specific files from S3
        if self.verbose:
            repo_display = (
                f"{repo_owner}/{repo_name}" if repo_owner and repo_name else "unknown"
            )
            print(f"❌ No repository metrics file found in S3 for repo: {repo_display}")
            print(
                f"   Expected location: s3://{S3_BUCKET}/{S3_BASE_PATH}/{repo_owner}/{repo_name}/techstack.json"
            )
            print(f"   Run data processing to generate this file for the current repo.")

        return None
