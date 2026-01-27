import json
import hashlib
import re
from typing import Dict, Any, Set, List, Tuple, Optional
from collections import defaultdict

from ..analysis.code_analyzer import CodeAnalyzer
from ..graph.graph_extractor import GraphExtractor

from .git_chunker import chunk_git_data as _chunk_git_data_func
from .gmail_chunker import chunk_gmail_data as _chunk_gmail_data_func
from .raw_fallback import create_raw_data_reference as _create_raw_data_reference_func


class DataChunker:
    """
    Base chunker holding shared state, entity extraction,
    code analysis, and delegating to source-specific chunkers.
    """

    def __init__(self, repo_name: str, repo_owner: str):
        self.repo_name = repo_name
        self.repo_owner = repo_owner

        # Core shared state
        self.chunk_registry = {}            # chunk_id -> chunk
        self.entity_map = defaultdict(set)  # entity -> chunk_ids
        self.git_keywords = set()

        # Analysis engines
        self.code_analyzer = CodeAnalyzer()
        self.graph_extractor = GraphExtractor(repo_name)

    # ------------------------------------------------------------------
    # ID generation
    # ------------------------------------------------------------------

    def generate_chunk_id(
        self, data: Dict[str, Any], chunk_type: str, index: int
    ) -> str:
        """Generate deterministic, collision-resistant chunk IDs"""
        try:
            payload = json.dumps(data, sort_keys=True, default=str)
        except Exception:
            payload = str(data)

        content_hash = hashlib.md5(payload.encode("utf-8")).hexdigest()[:8]
        return f"{chunk_type}_{index}_{content_hash}"

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    def extract_git_entities(self, data: Dict[str, Any]) -> Dict[str, Set[str]]:
        """
        Extract structured entities for precise cross-referencing.
        """
        entities = {
            "authors": set(),
            "issue_numbers": set(),
            "pr_numbers": set(),
            "commit_shas": set(),
            "file_paths": set(),
            "branches": set(),
            "labels": set(),
            "emails": set(),
            "keywords": set(),
        }

        try:
            # ---------------- Issues ----------------
            for issue in data.get("issues", []):
                if not isinstance(issue, dict):
                    continue

                if "number" in issue:
                    num = str(issue["number"])
                    entities["issue_numbers"].update({num, f"#{num}"})

                user = issue.get("user")
                if isinstance(user, dict) and user.get("login"):
                    entities["authors"].add(user["login"].lower())

                body = issue.get("body", "")
                if isinstance(body, str):
                    entities["authors"].update(
                        m.lower() for m in re.findall(r"@([\w-]+)", body)
                    )
                    entities["issue_numbers"].update(
                        f"#{r}" for r in re.findall(r"#(\d+)", body)
                    )

                for label in issue.get("labels", []):
                    if isinstance(label, dict) and label.get("name"):
                        entities["labels"].add(label["name"].lower())

                title = issue.get("title", "")
                if isinstance(title, str):
                    entities["keywords"].update(
                        re.findall(r"\b[a-zA-Z]{3,}\b", title.lower())
                    )

            # ---------------- PRs ----------------
            for pr in data.get("prs", []):
                if not isinstance(pr, dict):
                    continue

                if "number" in pr:
                    num = str(pr["number"])
                    entities["pr_numbers"].update({num, f"#{num}"})

                user = pr.get("user")
                if isinstance(user, dict) and user.get("login"):
                    entities["authors"].add(user["login"].lower())

                from backend.utils.path_normalizer import normalize_path

                for f in pr.get("files", []):
                    if isinstance(f, dict) and f.get("filename"):
                        path = normalize_path(f["filename"], "")
                        if path:
                            parts = path.split("/")
                            for i in range(1, len(parts) + 1):
                                entities["file_paths"].add("/".join(parts[:i]))

                body = pr.get("body", "")
                if isinstance(body, str):
                    entities["authors"].update(
                        m.lower() for m in re.findall(r"@([\w-]+)", body)
                    )
                    entities["pr_numbers"].update(
                        f"#{r}" for r in re.findall(r"#(\d+)", body)
                    )

                head = pr.get("head")
                if isinstance(head, dict) and head.get("ref"):
                    entities["branches"].add(head["ref"].lower())

            # ---------------- Commits ----------------
            for commit in data.get("commits", []):
                if not isinstance(commit, dict):
                    continue

                sha = commit.get("sha")
                if sha:
                    entities["commit_shas"].update({sha, sha[:7]})

                commit_data = commit.get("commit", {})
                if isinstance(commit_data, dict):
                    author = commit_data.get("author", {})
                    if isinstance(author, dict):
                        if author.get("name"):
                            entities["authors"].add(author["name"].lower())
                        if author.get("email"):
                            entities["emails"].add(author["email"].lower())

                    msg = commit_data.get("message", "")
                    if isinstance(msg, str):
                        entities["issue_numbers"].update(
                            f"#{r}" for r in re.findall(r"#(\d+)", msg)
                        )
                        entities["keywords"].update(
                            re.findall(r"\b[a-zA-Z]{3,}\b", msg.lower())
                        )

                for f in commit.get("files", []):
                    if isinstance(f, dict) and f.get("filename"):
                        entities["file_paths"].add(f["filename"])

            # ---------------- Code files ----------------
            for cf in data.get("code_files", []):
                if isinstance(cf, dict) and cf.get("path"):
                    entities["file_paths"].add(cf["path"])

            # Stopword cleanup
            stop_words = {
                "the","a","an","and","or","but","in","on","at","to","for","of",
                "with","by","from","up","about","into","through","during",
                "is","are","was","were","be","been"
            }

            entities["keywords"] = {
                k for k in entities["keywords"]
                if len(k) > 2 and k not in stop_words
            }

        except Exception as e:
            print(f"⚠️  Entity extraction warning: {e}")

        return entities

    # ------------------------------------------------------------------
    # Code analysis
    # ------------------------------------------------------------------

    def analyze_repository_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run full repository code analysis"""
        print("      🔍 Analyzing repository code...")

        self.code_analyzer.reset()
        all_file_paths = []

        for cf in data.get("code_files", []):
            if not isinstance(cf, dict):
                continue

            path = cf.get("path")
            content = cf.get("content", "")
            size = cf.get("size", 0)

            if path is not None:
                all_file_paths.append(path)
                cf["analysis"] = self.code_analyzer.analyze_file(
                    path, content, size
                )

        for pr in data.get("prs", []):
            for f in pr.get("files", []):
                if isinstance(f, dict) and f.get("filename"):
                    all_file_paths.append(f["filename"])

        for commit in data.get("commits", []):
            for f in commit.get("files", []):
                if isinstance(f, dict) and f.get("filename"):
                    all_file_paths.append(f["filename"])

        if all_file_paths:
            self.code_analyzer.analyze_structure(all_file_paths)
            self.code_analyzer.detect_tools(all_file_paths)

        tech_stack = self.code_analyzer.get_tech_stack_summary()

        print(f"         ✓ Files: {self.code_analyzer.metrics['total_files']}")
        print(f"         ✓ Code lines: {self.code_analyzer.metrics['total_code_lines']}")
        print(f"         ✓ Functions: {self.code_analyzer.function_metrics['total_functions']}")
        print(f"         ✓ Classes: {self.code_analyzer.function_metrics['total_classes']}")

        return tech_stack

    # ------------------------------------------------------------------
    # Chunking methods (delegating to source-specific chunkers)
    # ------------------------------------------------------------------

    def chunk_git_data(
        self, data: Dict[str, Any], repo_name: str = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Set[str]], Dict[str, Any]]:
        """
        Chunk Git data with enhanced metadata, entity extraction, bidirectional linking, and code analysis.
        Note: repo_name parameter is accepted for compatibility but uses self.repo_name internally.
        """
        # Use the imported function, binding self
        return _chunk_git_data_func(self, data)

    def chunk_gmail_data(
        self,
        data: Dict[str, Any],
        repo_name: str,
        git_entities: Dict[str, Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk Gmail data with GitHub correlation analysis.
        Note: repo_owner is taken from self.repo_owner.
        """
        # Use the imported function, binding self
        return _chunk_gmail_data_func(
            self, data, repo_name, self.repo_owner, git_entities or {}
        )

    def create_raw_data_reference(
        self,
        data: Dict[str, Any],
        source: str,
        repo_name: str,
        repo_owner: str = None,
    ) -> Dict[str, Any]:
        """
        Create comprehensive raw data reference for edge case fallback.
        Note: repo_owner defaults to self.repo_owner if not provided.
        """
        # Use the imported function, binding self
        return _create_raw_data_reference_func(
            self, data, source, repo_name, repo_owner or self.repo_owner
        )
