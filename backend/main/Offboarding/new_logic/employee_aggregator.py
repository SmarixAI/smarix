# employee_aggregator.py

from collections import defaultdict
from typing import Dict, Any, List
import os
import logging
from change_analyzer import ChangeAnalyzer


# Use global logging configuration (defined in main runner)
logger = logging.getLogger(__name__)


class EmployeeAggregator:

    MAX_DEPTH = 4

    DOC_EXTENSIONS = {".md", ".rst", ".adoc"}
    CONFIG_EXTENSIONS = {".yaml", ".yml", ".json", ".env"}
    TEST_KEYWORDS = ["test", "tests", "spec", "e2e"]
    RUNBOOK_KEYWORDS = ["scripts", "deploy", "release", ".github", "ci"]
    DOC_KEYWORDS = ["handover", "readme", "docs", "runbook", "howto"]

    # -----------------------------------------
    # Extract Path Prefixes
    # -----------------------------------------
    @staticmethod
    def _extract_prefixes(path: str) -> List[str]:
        parts = path.split("/")
        prefixes = []

        for i in range(1, min(len(parts), EmployeeAggregator.MAX_DEPTH) + 1):
            prefixes.append("/".join(parts[:i]))

        logger.info(f"Extracted prefixes for {path}: {prefixes}")
        return prefixes

    # -----------------------------------------
    # Detect Tags
    # -----------------------------------------
    @staticmethod
    def _detect_tags(path: str) -> List[str]:

        tags = []
        lower = path.lower()
        _, ext = os.path.splitext(lower)

        if ext in EmployeeAggregator.DOC_EXTENSIONS:
            tags.append("documentation")

        if ext in EmployeeAggregator.CONFIG_EXTENSIONS or "config" in lower:
            tags.append("config")

        if any(k in lower for k in EmployeeAggregator.TEST_KEYWORDS):
            tags.append("tests")

        if any(k in lower for k in EmployeeAggregator.RUNBOOK_KEYWORDS):
            tags.append("runbook")

        if any(k in lower for k in EmployeeAggregator.DOC_KEYWORDS):
            tags.append("handover")

        if not tags:
            tags.append("code")

        logger.info(f"Detected tags for {path}: {tags}")
        return tags

    # -----------------------------------------
    # Main Extraction
    # -----------------------------------------
    @staticmethod
    def extract(repo_data: Dict[str, Any], employee_name: str) -> Dict[str, Any]:

        logger.info("--------------------------------------------------")
        logger.info(f"Starting extraction for employee: {employee_name}")

        prs = repo_data.get("prs", [])
        commits = repo_data.get("commits", [])

        logger.info(f"Total PRs in repo: {len(prs)}")
        logger.info(f"Total commits in repo: {len(commits)}")

        file_stats = defaultdict(lambda: {
            "prs": 0,
            "commits": 0,
            "additions": 0,
            "deletions": 0,
        })

        matched_prs = 0
        matched_commits = 0

        # -----------------------------------------
        # PR Processing
        # -----------------------------------------
        for pr in prs:

            if pr.get("author") == employee_name:
                matched_prs += 1

                for f in pr.get("changed_files", []):

                    filename = f.get("filename")
                    if not filename:
                        continue

                    # Basic stats
                    file_stats[filename]["prs"] += 1
                    file_stats[filename]["additions"] += f.get("additions", 0)
                    file_stats[filename]["deletions"] += f.get("deletions", 0)

                    # -----------------------------------------
                    # NEW: Structural Change Analysis
                    # -----------------------------------------

                    analysis = ChangeAnalyzer.analyze(f)

                    if "structural_signals" not in file_stats[filename]:
                        file_stats[filename]["structural_signals"] = set()

                    file_stats[filename]["structural_signals"].update(
                        analysis.get("structural_signals", [])
                    )

                    if analysis.get("breaking_change"):
                        file_stats[filename]["breaking_change"] = True

                    file_stats[filename]["change_type"] = analysis.get("change_type")


        logger.info(f"Matched PRs authored by employee: {matched_prs}")

        # -----------------------------------------
        # Commit Processing
        # -----------------------------------------
        for commit in commits:

            if commit.get("author", {}).get("name") == employee_name:
                matched_commits += 1

                for f in commit.get("files", []):
                    filename = f.get("filename")
                    if not filename:
                        continue

                    file_stats[filename]["commits"] += 1

        logger.info(f"Matched commits authored by employee: {matched_commits}")
        logger.info(f"Total unique files touched: {len(file_stats)}")

        # -----------------------------------------
        # Enrich File Metadata
        # -----------------------------------------
        enriched_files = []

        for file_path, stats in file_stats.items():

            prefixes = EmployeeAggregator._extract_prefixes(file_path)
            tags = EmployeeAggregator._detect_tags(file_path)
            _, ext = os.path.splitext(file_path)

            enriched_files.append({
                "file": file_path,
                "prs": stats["prs"],
                "commits": stats["commits"],
                "additions": stats["additions"],
                "deletions": stats["deletions"],
                "prefixes": prefixes,
                "tags": tags,
                "extension": ext,
                "structural_signals": list(stats.get("structural_signals", [])),
                "breaking_change": stats.get("breaking_change", False),
                "change_type": stats.get("change_type", "minor"),

            })

        logger.info(f"Enriched file records created: {len(enriched_files)}")
        logger.info("Employee extraction completed.")
        logger.info("--------------------------------------------------\n")

        return {
            "employee": employee_name,
            "files": enriched_files,
        }
