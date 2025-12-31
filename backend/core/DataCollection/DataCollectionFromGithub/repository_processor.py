"""
Enhanced Repository Processor
Integrates all data collectors for comprehensive raw data collection
"""

import json
import time
from typing import Dict, Any
from collections import defaultdict

from core.DataCollection.DataCollectionFromGithub.github_client import GitHubClient
from core.DataCollection.DataCollectionFromGithub.file_processor import FileProcessor
from core.DataCollection.DataCollectionFromGithub.event_normalizer import EventNormalizer

# Import new collectors
from core.DataCollection.DataCollectionFromGithub.data_collectors.readme_collector import ReadmeCollector
from core.DataCollection.DataCollectionFromGithub.data_collectors.config_collector import ConfigCollector
from core.DataCollection.DataCollectionFromGithub.data_collectors.code_structure_collector import CodeStructureCollector
from core.DataCollection.DataCollectionFromGithub.data_collectors.workflow_collector import WorkflowCollector
from core.DataCollection.DataCollectionFromGithub.data_collectors.knowledge_collector import KnowledgeCollector

from config.DataCollection.settings import Config
from utils.DataCollection.rate_limiter import RateLimiter
from utils.DataCollection.file_utils import FileUtils
from tqdm import tqdm


class RepositoryProcessor:
    """Enhanced processor with comprehensive data collection for onboarding/offboarding"""

    def __init__(self):
        self.config = Config()
        self.github_client = GitHubClient()
        self.file_processor = FileProcessor()
        # self.teams_client = TeamsClient()
        self.normalizer = EventNormalizer()
        self.rate_limiter = RateLimiter()
        self.file_utils = FileUtils()
        self.processed_hashes = set()

        # Initialize new collectors
        self.readme_collector = ReadmeCollector()
        self.config_collector = ConfigCollector()
        self.structure_collector = CodeStructureCollector()
        self.workflow_collector = WorkflowCollector()
        self.knowledge_collector = KnowledgeCollector()

    def test_connection(self) -> bool:
        if not self.config.GITHUB_TOKEN:
            print("Warning: No GitHub token found. Rate limits will be lower.")
        return self.github_client.test_connection()

    def process_repository(self, owner: str, repo: str, team_id: str = None, channel_id: str = None) -> Dict[str, Any]:
        start_time = time.time()
        print(f"\n{'='*60}")
        print(f"Processing Repository: {owner}/{repo}")
        print(f"{'='*60}\n")

        self.processed_hashes.clear()

        # Initialize comprehensive data structure
        repo_data = {
            # Original sections
            'metadata': {},
            'code_files': [],
            'documentation': [],
            'dependencies': [],
            'issues': [],
            'prs': [],
            'commits': [],
            'knowledge_data': [],
            'analyzed_files': [],
            'duplicate_files': [],

            # NEW: Enhanced onboarding sections
            'onboarding': {
                'setup_instructions': [],
                'environment_config': {},
                'quick_start_guide': [],
                'architecture_overview': {},
                'api_documentation': [],
                'deployment_guide': []
            },

            # NEW: Enhanced offboarding sections
            'offboarding': {
                'code_patterns': {},
                'design_decisions': [],
                'workarounds_and_hacks': [],
                'gotchas_and_warnings': [],
                'domain_knowledge': [],
                'technical_debt': [],
                'expert_knowledge_map': {},
                'complex_areas': [],
                'frequently_modified_files': []
            },

            # NEW: Code structure and architecture
            'architecture': {
                'entry_points': [],
                'module_structure': {},
                'api_endpoints': [],
                'database_models': [],
                'authentication': {},
                'frameworks': {},
                'component_hierarchy': {}
            },

            # NEW: CI/CD and workflows
            'workflows': {
                'ci_cd_pipelines': [],
                'build_steps': [],
                'test_commands': [],
                'deployment_steps': [],
                'code_quality_checks': []
            },

            # Statistics
            'stats': {
                'total_files_found': 0,
                'duplicates_skipped': 0,
                'files_processed': 0,
                'issues_count': 0,
                'prs_count': 0,
                'commits_count': 0,
                'processing_time': 0,
                'language_breakdown': {},
                'file_size_stats': {},
                'onboarding_data_points': 0,
                'offboarding_data_points': 0
            }
        }

        # Step 1: Repository metadata
        print("📋 Step 1/8: Collecting repository metadata...")
        repo_data['metadata'] = self.github_client.get_repository_metadata(owner, repo)
        print(f"   Repository: {repo_data['metadata'].get('name', 'Unknown')}")
        print(f"   Language: {repo_data['metadata'].get('language', 'Mixed')}")
        print(f"   Stars: {repo_data['metadata'].get('stars', 0)}")

        # Step 2: Code files and documentation
        print("\n📁 Step 2/8: Scanning repository files...")
        self._process_directory_recursive(owner, repo, "", repo_data)
        self._calculate_final_stats(repo_data)
        print(f"   ✓ Found {len(repo_data['code_files'])} code files")
        print(f"   ✓ Found {len(repo_data['documentation'])} documentation files")
        print(f"   ✓ Found {len(repo_data['dependencies'])} dependency files")

        # Step 3: Analyze code files
        print("\n🔍 Step 3/8: Analyzing code structure...")
        repo_data['analyzed_files'] = self.file_processor.analyze_code_files(repo_data['code_files'])
        print(f"   ✓ Analyzed {len(repo_data['analyzed_files'])} files")

        # Step 4: Collect GitHub data (issues, PRs, commits) - ENHANCED
        print("\n🐙 Step 4/8: Collecting GitHub activity data...")
        self._collect_github_data(owner, repo, repo_data)

        # Step 5: Extract onboarding information
        print("\n📚 Step 5/8: Extracting onboarding information...")
        self._collect_onboarding_data(repo_data)

        # Step 6: Extract offboarding/knowledge information
        print("\n🧠 Step 6/8: Extracting knowledge and patterns...")
        self._collect_offboarding_data(repo_data)

        # Step 7: Collect workflow and CI/CD information
        print("\n⚙️  Step 7/8: Analyzing workflows and CI/CD...")
        self._collect_workflow_data(repo_data)

        # Step 8: Knowledge signals and Teams data
        print("\n💬 Step 8/8: Collecting knowledge signals...")
        unified = self.github_client.fetch_unified_activity(owner, repo, limit=getattr(self.config, 'MAX_COMMITS', 100))
        normalized_events = [self.normalizer.normalize_github_event(u) for u in unified]
        repo_data["knowledge_data"].extend(normalized_events)

        # if team_id and channel_id:
        #     print("   Fetching Teams discussions...")
        #     messages = self.teams_client.fetch_channel_messages(team_id, channel_id, limit=50)
        #     normalized_msgs = [self.normalizer.normalize_teams_message(m) for m in messages]
        #     repo_data["knowledge_data"].extend(normalized_msgs)

        # Generate summary statistics
        self._generate_summary_stats(repo_data)

        # Add developer and activity summary
        self._add_developer_and_activity_summary(owner, repo, repo_data)

        # Technology stack detection
        all_files = repo_data['code_files'] + repo_data['documentation'] + repo_data['dependencies']
        repo_data['technology_stack'] = self.file_utils.detect_technologies_from_files(all_files)

        processing_time = time.time() - start_time
        repo_data['stats']['processing_time'] = processing_time

        print(f"\n{'='*60}")
        print(f"✅ Processing Complete!")
        print(f"   Total time: {processing_time:.2f}s")
        print(f"   Onboarding data points: {repo_data['stats']['onboarding_data_points']}")
        print(f"   Offboarding data points: {repo_data['stats']['offboarding_data_points']}")
        print(f"{'='*60}\n")

        return repo_data

    def _collect_onboarding_data(self, repo_data: Dict[str, Any]) -> None:
        """Collect all onboarding-related information"""

        # Extract from README and documentation
        readme_data = self.readme_collector.collect_readme_data(repo_data['documentation'])
        repo_data['onboarding']['setup_instructions'] = readme_data['setup_instructions']
        repo_data['onboarding']['quick_start_guide'] = readme_data['quick_start_guide']
        repo_data['onboarding']['architecture_overview'] = readme_data['architecture_overview']
        repo_data['onboarding']['api_documentation'] = readme_data['api_documentation']
        repo_data['onboarding']['deployment_guide'] = readme_data['deployment_info']

        # Extract from configuration files
        config_data = self.config_collector.collect_config_data(
            repo_data['dependencies'],
            repo_data['code_files']
        )
        repo_data['onboarding']['environment_config'] = config_data['environment_setup']
        repo_data['onboarding']['dependencies'] = config_data['dependencies']
        repo_data['onboarding']['scripts'] = config_data['scripts']

        # Extract code structure
        structure_data = self.structure_collector.collect_structure_data(
            repo_data['code_files'],
            repo_data['analyzed_files']
        )
        repo_data['architecture'].update(structure_data)

        # Count onboarding data points
        count = (
            len(readme_data['setup_instructions']) +
            len(readme_data['quick_start_guide']) +
            len(readme_data['api_documentation']) +
            len(config_data['scripts']) +
            len(structure_data['entry_points'])
        )
        repo_data['stats']['onboarding_data_points'] = count

        print(f"   ✓ Setup instructions: {len(readme_data['setup_instructions'])}")
        print(f"   ✓ Quick start steps: {len(readme_data['quick_start_guide'])}")
        print(f"   ✓ Environment variables: {len(config_data['environment_setup']['required_env_vars'])}")
        print(f"   ✓ API endpoints: {len(structure_data['api_endpoints'])}")

    def _collect_offboarding_data(self, repo_data: Dict[str, Any]) -> None:
        """Collect all offboarding/knowledge retention information"""

        knowledge_data = self.knowledge_collector.collect_knowledge_data(
            repo_data['code_files'],
            repo_data['commits'],
            repo_data['issues'],
            repo_data['prs']
        )

        repo_data['offboarding'].update(knowledge_data)

        # Count offboarding data points
        count = (
            len(knowledge_data['workarounds_and_hacks']) +
            len(knowledge_data['gotchas_and_warnings']) +
            len(knowledge_data['design_decisions']) +
            len(knowledge_data['domain_knowledge']) +
            len(knowledge_data['complex_areas'])
        )
        repo_data['stats']['offboarding_data_points'] = count

        print(f"   ✓ Workarounds/hacks: {len(knowledge_data['workarounds_and_hacks'])}")
        print(f"   ✓ Gotchas/warnings: {len(knowledge_data['gotchas_and_warnings'])}")
        print(f"   ✓ Design decisions: {len(knowledge_data['design_decisions'])}")
        print(f"   ✓ Complex areas: {len(knowledge_data['complex_areas'])}")
        print(f"   ✓ Expert knowledge areas: {len(knowledge_data['expert_knowledge_areas'].get('file_experts', {}))}")

    def _collect_workflow_data(self, repo_data: Dict[str, Any]) -> None:
        """Collect CI/CD and workflow information"""

        workflow_data = self.workflow_collector.collect_workflow_data(
            repo_data['code_files'],
            repo_data
        )

        repo_data['workflows'].update(workflow_data)

        print(f"   ✓ CI/CD pipelines: {len(workflow_data['ci_cd_pipelines'])}")
        print(f"   ✓ Build scripts: {len(workflow_data['scripts'])}")
        print(f"   ✓ Test commands: {len(workflow_data['test_commands'])}")

    def _collect_github_data(self, owner: str, repo: str, repo_data: Dict[str, Any]) -> None:
        """
        Collect issues, PRs, and commits with COMPLETE details and bidirectional linking.

        ENHANCED: Now fetches:
        - For Issues: title, body, comments, status, labels, dates, linked PRs
        - For PRs: title, body, changed files with FULL CODE, review comments, status, merge info
        - Bidirectional linking between issues and PRs
        - Issue resolution status based on merged PRs
        """

        # Step 1: Fetch all issues with COMPLETE data
        issues_map = {}  # number -> issue data
        try:
            issues_count = 0
            print("Fetching issues with complete details...")
            for issue in self.github_client.fetch_issues(owner, repo, limit=getattr(self.config, "MAX_ISSUES", None)):
                if issue.get("pull_request"):
                    continue

                number = issue.get("number")
                body = issue.get("body") or ""
                title = issue.get("title") or ""
                state = issue.get("state", "open")
                user = issue.get("user") or {}
                slim_user = {"login": user.get("login"), "html_url": user.get("html_url")}
                labels = [label.get("name") for label in issue.get("labels", []) if label.get("name")]

                # Fetch ALL comments for the issue
                print(f"   Fetching comments for issue #{number}...")
                comments = self.github_client.get_issue_comments(owner, repo, number)

                # Parse referenced PRs from body and title
                referenced_prs = []
                for word in f"{body} {title}".split():
                    if any(x in word.lower() for x in ["fixes", "closes", "resolves", "closed"]):
                        try:
                            if "#" in word:
                                ref = int(word.split("#")[1])
                                referenced_prs.append(ref)
                        except:
                            pass

                # Build enriched issue object with COMPLETE information
                issue_data = {
                    "number": number,
                    "title": title.strip(),
                    "body": body.strip(),
                    "state": state,
                    "user": slim_user,
                    "labels": labels,
                    "created_at": issue.get("created_at"),
                    "updated_at": issue.get("updated_at"),
                    "closed_at": issue.get("closed_at"),
                    "comments": comments,  # COMPLETE comments list
                    "comments_count": len(comments),
                    "referenced_prs": list(set(referenced_prs)),
                    "linked_prs": [],  # Will populate after PR collection
                    "is_truly_resolved": False,  # Will compute after linking
                    "resolution_status": "open",  # open/closed/resolved_by_merged_pr
                    "html_url": issue.get("html_url"),
                    "assignees": [{"login": a.get("login")} for a in issue.get("assignees", [])],
                    "milestone": issue.get("milestone", {}).get("title") if issue.get("milestone") else None
                }

                issues_map[number] = issue_data
                issues_count += 1

            print(f"✓ Collected {issues_count} issues with complete details")
        except Exception as e:
            print(f"Error fetching issues: {e}")

        # Step 2: Fetch all PRs with COMPLETE data including FULL FILE CODE
        prs_map = {}  # number -> PR data
        try:
            prs_count = 0
            print("Fetching pull requests with complete details...")
            for pr in self.github_client.fetch_prs(owner, repo, limit=getattr(self.config, "MAX_PRS", None)):
                pr_number = pr.get("number")
                body = pr.get("body") or ""
                title = pr.get("title") or ""
                state = pr.get("state", "open")
                user = pr.get("user") or {}
                slim_user = {"login": user.get("login"), "html_url": user.get("html_url")}
                is_merged = pr.get("merged", False)

                # Parse linked issues from PR body/title
                linked_issues = []
                for word in f"{body} {title}".split():
                    if any(x in word.lower() for x in ["fixes", "closes", "resolves", "fix", "close", "resolve"]):
                        try:
                            if "#" in word:
                                ref = int(word.split("#")[1])
                                linked_issues.append(ref)
                        except:
                            pass

                # Get changed files with patch AND FULL FILE CODE
                print(f"   Fetching changed files for PR #{pr_number}...")
                pr_files = self.github_client.get_pr_files(owner, repo, pr_number)
                changed_files = []

                for f in pr_files:
                    filename = f.get("filename")
                    raw_url = f.get("raw_url")
                    patch = f.get("patch", "")
                    additions = f.get("additions", 0)
                    deletions = f.get("deletions", 0)
                    status = f.get("status", "")
                    changes = f.get("changes", 0)

                    # Fetch FULL FILE CONTENT (not just patch)
                    file_code = ""
                    if raw_url:
                        print(f"      Downloading full code for {filename}...")
                        file_code = self.github_client.get_file_content(raw_url)

                    changed_files.append({
                        "filename": filename,
                        "patch": patch,  # Git diff/patch
                        "raw_url": raw_url,
                        "file_code": file_code,  # COMPLETE file content
                        "additions": additions,
                        "deletions": deletions,
                        "changes": changes,
                        "status": status  # added, modified, removed, renamed
                    })

                # Get ALL review comments for PR
                print(f"   Fetching review comments for PR #{pr_number}...")
                review_comments = self.github_client.get_pr_reviews(owner, repo, pr_number)

                # Get line-by-line review comments
                print(f"   Fetching line-by-line comments for PR #{pr_number}...")
                line_comments = self.github_client.get_pr_review_comments(owner, repo, pr_number)

                # Get commit SHAs for PR
                pr_commits = self.github_client.get_pr_commits(owner, repo, pr_number)

                # Build enriched PR object with COMPLETE information
                pr_data = {
                    "number": pr_number,
                    "title": title.strip(),
                    "body": body.strip(),
                    "state": state,
                    "created_at": pr.get("created_at"),
                    "updated_at": pr.get("updated_at"),
                    "closed_at": pr.get("closed_at"),
                    "merged_at": pr.get("merged_at"),
                    "is_merged": is_merged,
                    "merge_commit_sha": pr.get("merge_commit_sha"),
                    "user": slim_user,
                    "linked_issues": list(set(linked_issues)),
                    "changed_files": changed_files,  # WITH FULL CODE
                    "changed_files_count": len(changed_files),
                    "review_comments": review_comments,  # General PR reviews
                    "line_comments": line_comments,  # Line-by-line code review comments
                    "total_comments_count": len(review_comments) + len(line_comments),
                    "commits": [c.get("sha") for c in pr_commits] if pr_commits else [],
                    "commits_count": len(pr_commits) if pr_commits else 0,
                    "html_url": pr.get("html_url"),
                    "pr_status": "merged" if is_merged else state,  # merged/open/closed
                    "additions": pr.get("additions", 0),
                    "deletions": pr.get("deletions", 0),
                    "changed_files_total": pr.get("changed_files", 0)
                }

                prs_map[pr_number] = pr_data
                prs_count += 1

            print(f"✓ Collected {prs_count} pull requests with complete details")
        except Exception as e:
            print(f"Error fetching PRs: {e}")

        # Step 3: Create bidirectional links and compute resolution status
        print("Linking issues and PRs...")
        for pr_num, pr_data in prs_map.items():
            for issue_num in pr_data["linked_issues"]:
                if issue_num in issues_map:
                    # Add PR to issue's linked_prs
                    if pr_num not in issues_map[issue_num]["linked_prs"]:
                        issues_map[issue_num]["linked_prs"].append(pr_num)

        # Also link PRs that are referenced in issue body
        for issue_num, issue_data in issues_map.items():
            for pr_num in issue_data["referenced_prs"]:
                if pr_num in prs_map:
                    if pr_num not in issue_data["linked_prs"]:
                        issue_data["linked_prs"].append(pr_num)
                    if issue_num not in prs_map[pr_num]["linked_issues"]:
                        prs_map[pr_num]["linked_issues"].append(issue_num)

        # Step 4: Determine true resolution status for issues
        for issue_num, issue_data in issues_map.items():
            linked_prs = issue_data["linked_prs"]
            issue_state = issue_data["state"]

            if linked_prs:
                # Check if any linked PR is merged
                has_merged_pr = any(
                    prs_map[pr_num]["is_merged"]
                    for pr_num in linked_prs
                    if pr_num in prs_map
                )

                if has_merged_pr:
                    issue_data["is_truly_resolved"] = True
                    issue_data["resolution_status"] = "resolved_by_merged_pr"
                elif issue_state == "closed":
                    issue_data["resolution_status"] = "closed_without_merged_pr"
                else:
                    issue_data["resolution_status"] = "open_with_pr"
            else:
                if issue_state == "closed":
                    issue_data["resolution_status"] = "closed_no_pr"
                else:
                    issue_data["resolution_status"] = "open_no_pr"

        # Step 5: Add to repo_data
        repo_data["issues"] = list(issues_map.values())
        repo_data["prs"] = list(prs_map.values())
        repo_data["stats"]["issues_count"] = len(issues_map)
        repo_data["stats"]["prs_count"] = len(prs_map)

        print(f"✓ Linked {sum(1 for i in issues_map.values() if i['linked_prs'])} issues with PRs")
        print(f"✓ Truly resolved issues: {sum(1 for i in issues_map.values() if i['is_truly_resolved'])}")

        # Step 6: Collect commits (existing logic)
        try:
            commits_count = 0
            print("Fetching commits...")
            for c in self.github_client.fetch_commits(owner, repo, limit=getattr(self.config, "MAX_COMMITS", None)):
                sha = c.get("sha")
                commit = c.get("commit", {})
                message = commit.get("message", "")
                author = commit.get("author", {}) or {}
                committer = commit.get("committer", {}) or {}

                linked_issues, linked_prs = [], []
                for word in message.split():
                    if word.startswith("#") and word[1:].isdigit():
                        linked_issues.append(int(word[1:]))
                    elif any(x in word.lower() for x in ["fixes", "closes", "resolves"]):
                        try:
                            ref = int(word.split("#")[1])
                            linked_prs.append(ref)
                        except:
                            pass

                commit_files = self.github_client.get_commit_files(owner, repo, sha) or []

                simplified_commit = {
                    "sha": sha,
                    "message": message.strip(),
                    "author": {"name": author.get("name"), "email": author.get("email")},
                    "committer": {"name": committer.get("name"), "email": committer.get("email")},
                    "linked_issues": list(set(linked_issues)),
                    "linked_prs": list(set(linked_prs)),
                    "changed_files": [f.get("filename") for f in commit_files if f.get("filename")]
                }
                repo_data["commits"].append(simplified_commit)
                commits_count += 1

            repo_data["stats"]["commits_count"] = commits_count
            print(f"✓ Collected {commits_count} commits")
        except Exception as e:
            print(f"Error fetching commits: {e}")

    def _add_developer_and_activity_summary(self, owner: str, repo: str, repo_data: Dict[str, Any]) -> None:
        """Add developer summary and incomplete work tracking"""
        developer_summary = defaultdict(lambda: {'commits': 0, 'prs': 0, 'issues': 0})
        file_ownership = defaultdict(lambda: defaultdict(int))
        todos_detected = []

        for commit in repo_data['commits']:
            author = commit.get('author', {}).get('name', 'unknown')
            for f in commit.get('changed_files', []):
                file_ownership[f][author] += 1
            developer_summary[author]['commits'] += 1

        for pr in repo_data['prs']:
            author = pr.get('user', {}).get('login', 'unknown')
            developer_summary[author]['prs'] += 1

        for issue in repo_data['issues']:
            user = issue.get('user', {}).get('login', 'unknown')
            developer_summary[user]['issues'] += 1

        for file in repo_data['code_files']:
            anns = self.file_processor.detect_annotations(file['content'])
            if anns:
                todos_detected.append({'file': file['path'], 'annotations': anns})

        branches = self.github_client.get_branches(owner, repo)
        stale_branches = []
        for b in branches:
            commit = b.get('commit', {}).get('commit', {})
            if not commit:
                continue
            date = commit.get('author', {}).get('date')
            stale_branches.append({'branch': b['name'], 'last_commit': date})

        contributors = self.github_client.get_contributors_activity(owner, repo)
        top_contributors = [{'author': c.get('author', {}).get('login'), 'commits': c.get('total', 0)} for c in contributors]

        repo_data['developer_summary'] = {
            'contributors': top_contributors,
            'ownership_map': {f: max(a, key=a.get) for f, a in file_ownership.items()},
            'activity_summary': dict(developer_summary)
        }

        repo_data['incomplete_work'] = {
            'open_prs': [p['number'] for p in repo_data['prs'] if p['state'] == 'open'],
            'open_issues': [i['number'] for i in repo_data['issues'] if i['state'] == 'open'],
            'todos': todos_detected,
            'stale_branches': stale_branches
        }

    def _generate_summary_stats(self, repo_data: Dict[str, Any]) -> None:
        """Generate summary statistics for knowledge signals"""
        tag_counts = defaultdict(int)
        for e in repo_data["knowledge_data"]:
            for t in e.get("tags", []):
                tag_counts[t] += 1
        repo_data["knowledge_summary"] = dict(tag_counts)

        repo_data['knowledge_stats'] = {
            'onboarding_signals': tag_counts.get('onboarding', 0),
            'offboarding_signals': tag_counts.get('offboarding', 0),
            'knowledge_signals': tag_counts.get('knowledge', 0)
        }

    def save_repository_data(self, repo_data: Dict[str, Any], owner: str, repo: str) -> str:
        """Save repository data to JSON file"""
        from pathlib import Path

        # Create output directory
        output_dir = Path("../../data/DataCollectionFromGit")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create output file path
        output_file = output_dir / f"{owner}_{repo}_data.json"

        # Save the file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(repo_data, f, indent=2, ensure_ascii=False)

        return str(output_file)

    def _process_directory_recursive(self, owner: str, repo: str, path: str, repo_data: Dict, depth: int = 0) -> None:
        """Recursively process directory contents"""
        if depth > self.config.MAX_RECURSION_DEPTH:
            return
        contents = self.github_client.get_repository_contents(owner, repo, path)
        with tqdm(contents, desc=f"Processing {path or 'root'}", leave=False) as pbar:
            for item in pbar:
                if item['type'] == 'file':
                    self._process_single_file(item, repo_data)
                elif item['type'] == 'dir' and not self.file_processor.should_skip_directory(item['name']):
                    self._process_directory_recursive(owner, repo, item['path'], repo_data, depth + 1)
        self.rate_limiter.apply_delay()

    def _process_single_file(self, file_item: Dict, repo_data: Dict) -> None:
        """Process a single file"""
        file_path = file_item['path']
        repo_data['stats']['total_files_found'] += 1
        if self.file_processor.should_skip_file(file_item):
            return
        file_content = self.github_client.get_file_content(file_item['download_url'])
        if not file_content:
            return
        file_data = self.file_processor.process_file_content(file_item, file_content)
        if getattr(self.config, 'SKIP_DUPLICATE_FILES', True):
            if self.file_utils.is_duplicate_file(file_data, self.processed_hashes):
                original_path = self._find_original_file_path(file_data, repo_data)
                repo_data['duplicate_files'].append({
                    'path': file_path,
                    'original_path': original_path,
                    'size': file_item['size']
                })
                repo_data['stats']['duplicates_skipped'] += 1
                return
        category = self.file_processor.categorize_file(file_item)
        repo_data['stats']['files_processed'] += 1
        file_ext = file_data.get('extension', 'unknown')
        repo_data['stats']['language_breakdown'][file_ext] = repo_data['stats']['language_breakdown'].get(file_ext, 0) + 1
        if category == 'code':
            repo_data['code_files'].append(file_data)
        elif category == 'documentation':
            repo_data['documentation'].append(file_data)
        elif category == 'dependencies':
            repo_data['dependencies'].append(file_data)

    def _find_original_file_path(self, duplicate_file: Dict, repo_data: Dict) -> str:
        """Find the original file path for a duplicate"""
        duplicate_hash = self.file_utils.get_file_hash(duplicate_file['content'])
        all_files = (repo_data['code_files'] + repo_data['documentation'] + repo_data['dependencies'])
        for file_data in all_files:
            if self.file_utils.get_file_hash(file_data['content']) == duplicate_hash:
                return file_data['path']
        return "unknown"

    def _calculate_final_stats(self, repo_data: Dict) -> None:
        """Calculate final statistics"""
        all_files = (repo_data['code_files'] + repo_data['documentation'] + repo_data['dependencies'])
        stats = repo_data['stats']
        if all_files:
            total_size = sum(file_data.get('size', 0) for file_data in all_files)
            avg_size = total_size / len(all_files) if all_files else 0
            stats['file_size_stats'] = {
                'total_size_bytes': total_size,
                'total_size_kb': round(total_size / 1024, 2),
                'total_size_mb': round(total_size / (1024 * 1024), 3),
                'avg_file_size_bytes': round(avg_size, 2),
                'avg_file_size_kb': round(avg_size / 1024, 2),
                'file_count': len(all_files)
            }
        if repo_data['stats']['duplicates_skipped'] > 0:
            print(f"   Found {repo_data['stats']['duplicates_skipped']} duplicate files")

    def print_summary(self, repo_data: Dict[str, Any], owner: str, repo: str, output_file: str) -> None:
        """Print comprehensive summary of collected data"""
        print(f"\n{'='*70}")
        print(f"REPOSITORY SUMMARY: {owner}/{repo}")
        print(f"{'='*70}")

        print(f"\n📊 BASIC STATISTICS:")
        print(f"   Code Files: {len(repo_data['code_files'])}")
        print(f"   Documentation: {len(repo_data['documentation'])}")
        print(f"   Dependencies: {len(repo_data['dependencies'])}")
        print(f"   Issues: {repo_data['stats']['issues_count']}")
        print(f"   Pull Requests: {repo_data['stats']['prs_count']}")
        print(f"   Commits: {repo_data['stats']['commits_count']}")

        print(f"\n🎓 ONBOARDING DATA:")
        print(f"   Setup Instructions: {len(repo_data['onboarding']['setup_instructions'])}")
        print(f"   Quick Start Steps: {len(repo_data['onboarding']['quick_start_guide'])}")
        print(f"   API Endpoints: {len(repo_data['architecture']['api_endpoints'])}")
        print(f"   Entry Points: {len(repo_data['architecture']['entry_points'])}")
        print(f"   Environment Variables: {len(repo_data['onboarding']['environment_config']['required_env_vars'])}")
        print(f"   Total Onboarding Data Points: {repo_data['stats']['onboarding_data_points']}")

        print(f"\n🧠 OFFBOARDING/KNOWLEDGE DATA:")
        print(f"   Workarounds/Hacks: {len(repo_data['offboarding']['workarounds_and_hacks'])}")
        print(f"   Gotchas/Warnings: {len(repo_data['offboarding']['gotchas_and_warnings'])}")
        print(f"   Design Decisions: {len(repo_data['offboarding']['design_decisions'])}")
        print(f"   Domain Knowledge: {len(repo_data['offboarding']['domain_knowledge'])}")
        print(f"   Technical Debt Items: {len(repo_data['offboarding']['technical_debt'])}")
        print(f"   Complex Areas: {len(repo_data['offboarding']['complex_areas'])}")
        print(f"   Frequently Modified Files: {len(repo_data['offboarding']['frequently_modified_files'])}")
        print(f"   Total Offboarding Data Points: {repo_data['stats']['offboarding_data_points']}")

        print(f"\n⚙️  CI/CD & WORKFLOWS:")
        print(f"   CI/CD Pipelines: {len(repo_data['workflows']['ci_cd_pipelines'])}")
        print(f"   Test Commands: {len(repo_data['workflows']['test_commands'])}")
        print(f"   Build Scripts: {len(repo_data['workflows']['scripts'])}")

        print(f"\n👥 DEVELOPER ACTIVITY:")
        top_contributors = repo_data['developer_summary']['contributors'][:5]
        print(f"   Top Contributors:")
        for contrib in top_contributors:
            print(f"      - {contrib['author']}: {contrib['commits']} commits")

        print(f"\n🔧 FRAMEWORKS & TECHNOLOGIES:")
        frameworks = repo_data['architecture'].get('frameworks', {})
        if frameworks:
            for framework, files in list(frameworks.items())[:5]:
                print(f"   {framework}: {len(files)} files")

        print(f"\n💾 OUTPUT:")
        print(f"   Saved to: {output_file}")
        print(f"   File size: {self._get_file_size(output_file)}")
        print(f"   Processing time: {repo_data['stats']['processing_time']:.2f}s")

        print(f"\n{'='*70}\n")

    def _get_file_size(self, file_path: str) -> str:
        """Get human-readable file size"""
        try:
            import os
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size/1024:.2f} KB"
            else:
                return f"{size/(1024*1024):.2f} MB"
        except:
            return "unknown"