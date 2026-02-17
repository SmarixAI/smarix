"""
Private Repository Processor - ASYNC VERSION
Processes private repositories using GitHub App authentication
Identical output format to AsyncRepositoryProcessor
"""

import json
import time
import asyncio
from typing import Dict, Any, List
from collections import defaultdict
from pathlib import Path

from core.DataCollection.DataCollectionFromGithub.github_app_client import AsyncGitHubAppClient
from core.DataCollection.DataCollectionFromGithub.file_processor import FileProcessor
from core.DataCollection.DataCollectionFromGithub.event_normalizer import EventNormalizer

# Import collectors
from core.DataCollection.DataCollectionFromGithub.data_collectors.readme_collector import ReadmeCollector
from core.DataCollection.DataCollectionFromGithub.data_collectors.config_collector import ConfigCollector
from core.DataCollection.DataCollectionFromGithub.data_collectors.code_structure_collector import CodeStructureCollector
from core.DataCollection.DataCollectionFromGithub.data_collectors.workflow_collector import WorkflowCollector
from core.DataCollection.DataCollectionFromGithub.data_collectors.knowledge_collector import KnowledgeCollector

from config.DataCollection.settings import Config
from utils.DataCollection.file_utils import FileUtils
from tqdm import tqdm

from utils.s3 import s3_manager


class AsyncPrivateRepositoryProcessor:
    """
    Enhanced async processor for PRIVATE repositories using GitHub App authentication
    
    Key differences from AsyncRepositoryProcessor:
    - Uses AsyncGitHubAppClient (installation tokens) instead of AsyncGitHubClient (personal tokens)
    - Requires installation_id parameter
    - Everything else is IDENTICAL
    """

    def __init__(self):
        self.config = Config()
        self.file_processor = FileProcessor()
        self.normalizer = EventNormalizer()
        self.file_utils = FileUtils()
        self.processed_hashes = set()

        # Initialize collectors (same as public repo processor)
        self.readme_collector = ReadmeCollector()
        self.config_collector = ConfigCollector()
        self.structure_collector = CodeStructureCollector()
        self.workflow_collector = WorkflowCollector()
        self.knowledge_collector = KnowledgeCollector()

    async def test_connection(self, github_client: AsyncGitHubAppClient) -> bool:
        """Test GitHub connection"""
        return await github_client.test_connection()

    async def process_repository(
        self, 
        owner: str, 
        repo: str, 
        installation_id: int,
        team_id: str = None, 
        channel_id: str = None
    ) -> Dict[str, Any]:
        """
        Process PRIVATE repository with async operations - MAIN ENTRY POINT
        
        Args:
            owner: Repository owner
            repo: Repository name
            installation_id: GitHub App installation ID
            team_id: Optional team ID
            channel_id: Optional channel ID
        
        Returns:
            Same data structure as AsyncRepositoryProcessor
        """
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"Processing PRIVATE Repository: {owner}/{repo}")
        print(f"Installation ID: {installation_id}")
        print(f"{'='*60}\n")

        self.processed_hashes.clear()

        # Initialize comprehensive data structure (IDENTICAL to public processor)
        repo_data = {
            "metadata": {},
            "code_files": [],
            "documentation": [],
            "dependencies": [],
            "issues": [],
            "prs": [],
            "commits": [],
            "knowledge_data": [],
            "analyzed_files": [],
            "duplicate_files": [],
            "onboarding": {
                "setup_instructions": [],
                "environment_config": {},
                "quick_start_guide": [],
                "architecture_overview": {},
                "api_documentation": [],
                "deployment_guide": [],
            },
            "offboarding": {
                "code_patterns": {},
                "design_decisions": [],
                "workarounds_and_hacks": [],
                "gotchas_and_warnings": [],
                "domain_knowledge": [],
                "technical_debt": [],
                "expert_knowledge_map": {},
                "complex_areas": [],
                "frequently_modified_files": [],
            },
            "architecture": {
                "entry_points": [],
                "module_structure": {},
                "api_endpoints": [],
                "database_models": [],
                "authentication": {},
                "frameworks": {},
                "component_hierarchy": {},
            },
            "workflows": {
                "ci_cd_pipelines": [],
                "build_steps": [],
                "test_commands": [],
                "deployment_steps": [],
                "code_quality_checks": [],
            },
            "stats": {
                "total_files_found": 0,
                "duplicates_skipped": 0,
                "files_processed": 0,
                "issues_count": 0,
                "prs_count": 0,
                "commits_count": 0,
                "processing_time": 0,
                "language_breakdown": {},
                "file_size_stats": {},
                "onboarding_data_points": 0,
                "offboarding_data_points": 0,
            },
        }

        # Use AsyncGitHubAppClient instead of AsyncGitHubClient
        async with AsyncGitHubAppClient(
            installation_id=installation_id,
            max_concurrent_requests=50
        ) as github_client:

            # Step 1: Repository metadata
            print("📋 Step 1/8: Collecting repository metadata...")
            repo_data["metadata"] = await github_client.get_repository_metadata(owner, repo)
            print(f"   Repository: {repo_data['metadata'].get('name', 'Unknown')}")
            print(f"   Language: {repo_data['metadata'].get('language', 'Mixed')}")
            print(f"   Stars: {repo_data['metadata'].get('stars', 0)}")
            print(f"   Private: {repo_data['metadata'].get('private', False)}")

            # Step 2: Code files and documentation (ASYNC)
            print("\n📁 Step 2/8: Scanning repository files...")
            await self._process_directory_recursive_async(
                owner, repo, "", repo_data, github_client
            )
            self._calculate_final_stats(repo_data)
            print(f"   ✓ Found {len(repo_data['code_files'])} code files")
            print(f"   ✓ Found {len(repo_data['documentation'])} documentation files")
            print(f"   ✓ Found {len(repo_data['dependencies'])} dependency files")

            # Step 3: Analyze code files (sync - local processing)
            print("\n🔍 Step 3/8: Analyzing code structure...")
            repo_data["analyzed_files"] = self.file_processor.analyze_code_files(
                repo_data["code_files"]
            )
            print(f"   ✓ Analyzed {len(repo_data['analyzed_files'])} files")

            # Step 4: Collect GitHub data (ASYNC - MAJOR SPEEDUP HERE)
            print("\n🐙 Step 4/8: Collecting GitHub activity data...")
            await self._collect_github_data_async(owner, repo, repo_data, github_client)

            # Step 5: Extract onboarding information (sync - local)
            print("\n📚 Step 5/8: Extracting onboarding information...")
            self._collect_onboarding_data(repo_data)

            # Step 6: Extract offboarding/knowledge information (sync - local)
            print("\n🧠 Step 6/8: Extracting knowledge and patterns...")
            self._collect_offboarding_data(repo_data)

            # Step 7: Collect workflow and CI/CD information (sync - local)
            print("\n⚙️  Step 7/8: Analyzing workflows and CI/CD...")
            self._collect_workflow_data(repo_data)

            # Step 8: Knowledge signals (ASYNC)
            print("\n💬 Step 8/8: Collecting knowledge signals...")
            unified = await github_client.fetch_unified_activity(
                owner, repo, limit=getattr(self.config, "MAX_COMMITS", 100)
            )
            normalized_events = [
                self.normalizer.normalize_github_event(u) for u in unified
            ]
            repo_data["knowledge_data"].extend(normalized_events)

            # Generate summary statistics
            self._generate_summary_stats(repo_data)

            # Add developer and activity summary
            await self._add_developer_and_activity_summary_async(
                owner, repo, repo_data, github_client
            )

            # Technology stack detection
            all_files = (
                repo_data["code_files"]
                + repo_data["documentation"]
                + repo_data["dependencies"]
            )
            repo_data["technology_stack"] = (
                self.file_utils.detect_technologies_from_files(all_files)
            )

        processing_time = time.time() - start_time
        repo_data["stats"]["processing_time"] = processing_time

        print(f"\n{'='*60}")
        print(f"✅ Processing Complete!")
        print(f"   Total time: {processing_time:.2f}s")
        print(f"   Onboarding data points: {repo_data['stats']['onboarding_data_points']}")
        print(f"   Offboarding data points: {repo_data['stats']['offboarding_data_points']}")
        print(f"{'='*60}\n")

        return repo_data

    async def _process_directory_recursive_async(
        self,
        owner: str,
        repo: str,
        path: str,
        repo_data: Dict,
        github_client: AsyncGitHubAppClient,
        depth: int = 0,
    ) -> None:
        """Recursively process directory contents with ASYNC file downloads"""
        if depth > self.config.MAX_RECURSION_DEPTH:
            return

        contents = await github_client.get_repository_contents(owner, repo, path)

        # Separate files and directories
        files = [item for item in contents if item["type"] == "file"]
        dirs = [
            item
            for item in contents
            if item["type"] == "dir"
            and not self.file_processor.should_skip_directory(item["name"])
        ]

        # ✅ Pass owner and repo to file processor
        if files:
            print(f"   Processing {len(files)} files in {path or 'root'}...")
            file_tasks = [
                self._process_single_file_async(
                    owner,           # ✅ Pass owner
                    repo,            # ✅ Pass repo
                    file_item,
                    repo_data,
                    github_client
                )
                for file_item in files
            ]
            await asyncio.gather(*file_tasks)

        # Process subdirectories recursively
        for dir_item in dirs:
            await self._process_directory_recursive_async(
                owner, repo, dir_item["path"], repo_data, github_client, depth + 1
            )


    async def _process_single_file_async(
        self,
        owner: str,      # ✅ Add owner parameter
        repo: str,       # ✅ Add repo parameter
        file_item: Dict,
        repo_data: Dict,
        github_client: AsyncGitHubAppClient
    ) -> None:
        """Process a single file asynchronously"""
        file_path = file_item["path"]
        repo_data["stats"]["total_files_found"] += 1

        if self.file_processor.should_skip_file(file_item):
            return

        # ✅ Use API endpoint with owner/repo/path instead of download_url
        file_content = await github_client.get_file_content(owner, repo, file_path)
        if not file_content:
            return

        file_data = self.file_processor.process_file_content(file_item, file_content)

        # Categorize and store
        category = self.file_processor.categorize_file(file_item)
        repo_data["stats"]["files_processed"] += 1
        file_ext = file_data.get("extension", "unknown")
        repo_data["stats"]["language_breakdown"][file_ext] = (
            repo_data["stats"]["language_breakdown"].get(file_ext, 0) + 1
        )

        if category == "code":
            repo_data["code_files"].append(file_data)
        elif category == "documentation":
            repo_data["documentation"].append(file_data)
        elif category == "dependencies":
            repo_data["dependencies"].append(file_data)

    async def _collect_github_data_async(
        self, owner: str, repo: str, repo_data: Dict, github_client: AsyncGitHubAppClient
    ) -> None:
        """
        Collect issues, PRs, and commits CONCURRENTLY using normalization
        """
        
        # Fetch enriched data concurrently
        print("   Fetching issues, PRs, and commits concurrently...")
        
        issues_task = github_client.fetch_issues_batch(
            owner, repo, limit=getattr(self.config, "MAX_ISSUES", None)
        )
        prs_task = github_client.fetch_prs_batch(
            owner, repo, limit=getattr(self.config, "MAX_PRS", None)
        )
        commits_task = github_client.fetch_commits_batch(
            owner, repo, limit=getattr(self.config, "MAX_COMMITS", None)
        )
        
        # Wait for all three to complete
        issues_raw, prs_raw, commits_raw = await asyncio.gather(
            issues_task, prs_task, commits_task
        )
        
        # Normalize issues
        print(f"   Normalizing {len(issues_raw)} enriched issues...")
        issues_map = {}
        for issue in issues_raw:
            normalized_issue = self.normalizer._normalize_issue(issue)
            issues_map[issue.get("number")] = normalized_issue["metadata"]
        print(f"   ✓ Collected {len(issues_map)} issues with comments")
        
        # Normalize PRs
        print(f"   Normalizing {len(prs_raw)} enriched PRs...")
        prs_map = {}
        for pr in prs_raw:
            normalized_pr = self.normalizer._normalize_pr(pr)
            prs_map[pr.get("number")] = normalized_pr["metadata"]
        print(f"   ✓ Collected {len(prs_map)} PRs with files & reviews")
        
        # Bidirectional linking
        for pr_num, pr_data in prs_map.items():
            for issue_num in pr_data.get("linked_issues", []):
                if issue_num in issues_map:
                    if pr_num not in issues_map[issue_num].get("linked_prs", []):
                        issues_map[issue_num]["linked_prs"].append(pr_num)
        
        # Resolution status
        for issue_num, issue_data in issues_map.items():
            if issue_data.get("is_truly_resolved"):
                issue_data["resolution_status"] = "resolved_by_merged_pr"
        
        # Store normalized data in repo_data
        repo_data["issues"] = list(issues_map.values())
        repo_data["prs"] = list(prs_map.values())
        repo_data["stats"]["issues_count"] = len(issues_map)
        repo_data["stats"]["prs_count"] = len(prs_map)
        
        # Process commits
        repo_data["commits"] = [
            {
                "sha": c.get("sha"),
                "message": c.get("message", "").strip(),
                "author": c.get("author", {}),
                "date": c.get("date"),
            }
            for c in commits_raw
        ]
        repo_data["stats"]["commits_count"] = len(commits_raw)
        print(f"   ✓ Collected {len(commits_raw)} commits")

    async def _add_developer_and_activity_summary_async(
        self, owner: str, repo: str, repo_data: Dict, github_client: AsyncGitHubAppClient
    ) -> None:
        """Add developer summary with async data fetching"""
        developer_summary = defaultdict(lambda: {"commits": 0, "prs": 0, "issues": 0})
        file_ownership = defaultdict(lambda: defaultdict(int))
        todos_detected = []

        # Process commits
        for commit in repo_data["commits"]:
            author = commit.get("author", {}).get("name", "unknown")
            developer_summary[author]["commits"] += 1

        # Process PRs
        for pr in repo_data["prs"]:
            author = pr.get("user", {}).get("login", "unknown")
            developer_summary[author]["prs"] += 1

            # File ownership from PR changed files
            for file_item in pr.get("changed_files", []):
                filename = (
                    file_item.get("filename")
                    if isinstance(file_item, dict)
                    else file_item
                )
                if filename:
                    file_ownership[filename][author] += 1

        # Process issues
        for issue in repo_data["issues"]:
            user = issue.get("user", {}).get("login", "unknown")
            developer_summary[user]["issues"] += 1

        # Detect TODOs
        for file in repo_data["code_files"]:
            anns = self.file_processor.detect_annotations(file["content"])
            if anns:
                todos_detected.append({"file": file["path"], "annotations": anns})

        # Fetch branches and contributors concurrently
        branches_task = github_client.get_branches(owner, repo)
        contributors_task = github_client.get_contributors_activity(owner, repo)

        branches, contributors = await asyncio.gather(branches_task, contributors_task)

        # Build response
        repo_data["developer_summary"] = {
            "contributors": [
                {
                    "author": c.get("author", {}).get("login"),
                    "commits": c.get("total", 0),
                }
                for c in contributors
            ],
            "ownership_map": {f: max(a, key=a.get) for f, a in file_ownership.items()},
            "activity_summary": dict(developer_summary),
        }

        repo_data["incomplete_work"] = {
            "open_prs": [p["number"] for p in repo_data["prs"] if p["state"] == "open"],
            "open_issues": [
                i["number"] for i in repo_data["issues"] if i["state"] == "open"
            ],
            "todos": todos_detected,
            "stale_branches": [{"branch": b["name"]} for b in branches],
        }

    # ============================================
    # ALL METHODS BELOW ARE IDENTICAL TO AsyncRepositoryProcessor
    # (Just copy-paste from repository_processor.py)
    # ============================================

    def _collect_onboarding_data(self, repo_data: Dict[str, Any]) -> None:
        """Collect all onboarding-related information"""
        readme_data = self.readme_collector.collect_readme_data(
            repo_data["documentation"]
        )
        repo_data["onboarding"]["setup_instructions"] = readme_data[
            "setup_instructions"
        ]
        repo_data["onboarding"]["quick_start_guide"] = readme_data["quick_start_guide"]
        repo_data["onboarding"]["architecture_overview"] = readme_data[
            "architecture_overview"
        ]
        repo_data["onboarding"]["api_documentation"] = readme_data["api_documentation"]
        repo_data["onboarding"]["deployment_guide"] = readme_data["deployment_info"]

        config_data = self.config_collector.collect_config_data(
            repo_data["dependencies"], repo_data["code_files"]
        )
        repo_data["onboarding"]["environment_config"] = config_data["environment_setup"]

        structure_data = self.structure_collector.collect_structure_data(
            repo_data["code_files"], repo_data["analyzed_files"]
        )
        repo_data["architecture"].update(structure_data)

        count = (
            len(readme_data["setup_instructions"])
            + len(readme_data["quick_start_guide"])
            + len(readme_data["api_documentation"])
            + len(config_data["scripts"])
            + len(structure_data["entry_points"])
        )
        repo_data["stats"]["onboarding_data_points"] = count

    def _collect_offboarding_data(self, repo_data: Dict[str, Any]) -> None:
        """Collect all offboarding/knowledge retention information"""
        knowledge_data = self.knowledge_collector.collect_knowledge_data(
            repo_data["code_files"],
            repo_data["commits"],
            repo_data["issues"],
            repo_data["prs"],
        )
        repo_data["offboarding"].update(knowledge_data)

        count = (
            len(knowledge_data["workarounds_and_hacks"])
            + len(knowledge_data["gotchas_and_warnings"])
            + len(knowledge_data["design_decisions"])
            + len(knowledge_data["domain_knowledge"])
            + len(knowledge_data["complex_areas"])
        )
        repo_data["stats"]["offboarding_data_points"] = count

    def _collect_workflow_data(self, repo_data: Dict[str, Any]) -> None:
        """Collect CI/CD and workflow information"""
        workflow_data = self.workflow_collector.collect_workflow_data(
            repo_data["code_files"], repo_data
        )
        repo_data["workflows"].update(workflow_data)

    def _generate_summary_stats(self, repo_data: Dict[str, Any]) -> None:
        """Generate summary statistics"""
        tag_counts = defaultdict(int)
        for e in repo_data["knowledge_data"]:
            for t in e.get("tags", []):
                tag_counts[t] += 1
        repo_data["knowledge_summary"] = dict(tag_counts)
        repo_data["knowledge_stats"] = {
            "onboarding_signals": tag_counts.get("onboarding", 0),
            "offboarding_signals": tag_counts.get("offboarding", 0),
            "knowledge_signals": tag_counts.get("knowledge", 0),
        }

    def save_repository_data(
        self, repo_data: Dict[str, Any], owner: str, repo: str
    ) -> str:
        """Save repository data to S3 (no local file)"""
        s3_key = f"DataCollectionFromGit/{owner}/{repo}/{repo}.json"

        s3_manager.upload_json(repo_data, s3_key, public_read=False)

        return s3_key

    def _find_original_file_path(self, duplicate_file: Dict, repo_data: Dict) -> str:
        """Find original file path"""
        duplicate_hash = self.file_utils.get_file_hash(duplicate_file["content"])
        all_files = (
            repo_data["code_files"]
            + repo_data["documentation"]
            + repo_data["dependencies"]
        )
        for file_data in all_files:
            if self.file_utils.get_file_hash(file_data["content"]) == duplicate_hash:
                return file_data["path"]
        return "unknown"

    def _calculate_final_stats(self, repo_data: Dict) -> None:
        """Calculate final statistics"""
        all_files = (
            repo_data["code_files"]
            + repo_data["documentation"]
            + repo_data["dependencies"]
        )
        stats = repo_data["stats"]
        if all_files:
            total_size = sum(file_data.get("size", 0) for file_data in all_files)
            avg_size = total_size / len(all_files) if all_files else 0
            stats["file_size_stats"] = {
                "total_size_bytes": total_size,
                "total_size_kb": round(total_size / 1024, 2),
                "total_size_mb": round(total_size / (1024 * 1024), 3),
                "avg_file_size_bytes": round(avg_size, 2),
                "avg_file_size_kb": round(avg_size / 1024, 2),
                "file_count": len(all_files),
            }

    def print_summary(
        self, repo_data: Dict[str, Any], owner: str, repo: str, output_file: str
    ) -> None:
        """Print comprehensive summary"""
        print(f"\n{'='*70}")
        print(f"PRIVATE REPOSITORY SUMMARY: {owner}/{repo}")
        print(f"{'='*70}")
        print(f"\n📊 BASIC STATISTICS:")
        print(f"   Code Files: {len(repo_data['code_files'])}")
        print(f"   Issues: {repo_data['stats']['issues_count']}")
        print(f"   Pull Requests: {repo_data['stats']['prs_count']}")
        print(f"   Commits: {repo_data['stats']['commits_count']}")
        print(f"\n💾 OUTPUT:")
        print(f"   Saved to: {output_file}")
        print(f"   Processing time: {repo_data['stats']['processing_time']:.2f}s")
        print(f"\n{'='*70}\n")
