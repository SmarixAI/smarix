"""
Knowledge Signals Collector - OPTIMIZED FOR ASYNC DATA
Captures implicit knowledge from code patterns, comments, and history
Compatible with AsyncGitHubClient enriched data structures
"""

from typing import Dict, List, Any, Set
import re
from collections import defaultdict


class KnowledgeCollector:
    """Extracts implicit knowledge and patterns for offboarding"""

    def __init__(self):
        self.knowledge_indicators = {
            "workarounds": ["workaround", "hack", "temporary", "fixme", "todo", "xxx"],
            "gotchas": [
                "gotcha",
                "careful",
                "warning",
                "note",
                "important",
                "attention",
                "watch out",
            ],
            "decisions": ["decided", "chosen", "because", "reason", "why", "rationale"],
            "domain_knowledge": [
                "business",
                "requirement",
                "spec",
                "customer",
                "user story",
                "stakeholder",
            ],
            "technical_debt": [
                "debt",
                "refactor",
                "cleanup",
                "improve",
                "optimize",
                "todo",
            ],
        }

    def collect_knowledge_data(
        self,
        code_files: List[Dict],
        commits: List[Dict],
        issues: List[Dict],
        prs: List[Dict],
    ) -> Dict[str, Any]:
        """
        Extract knowledge signals from various sources

        OPTIMIZED: Works with async client's enriched data structures
        """

        knowledge_data = {
            "code_patterns": {},
            "workarounds_and_hacks": [],
            "gotchas_and_warnings": [],
            "design_decisions": [],
            "domain_knowledge": [],
            "technical_debt": [],
            "frequently_modified_files": [],
            "complex_areas": [],
            "expert_knowledge_areas": {},
            "undocumented_features": [],
            "critical_paths": [],
        }

        print("   Extracting knowledge from code comments...")
        self._extract_from_comments(code_files, knowledge_data)

        print("   Extracting knowledge from commits...")
        self._extract_from_commits(commits, knowledge_data)

        print("   Extracting knowledge from issues...")
        self._extract_from_issues(issues, knowledge_data)

        print("   Extracting knowledge from PRs...")
        self._extract_from_prs(prs, knowledge_data)

        print("   Identifying complex code areas...")
        knowledge_data["complex_areas"] = self._identify_complex_areas(code_files)

        print("   Mapping expert knowledge...")
        knowledge_data["expert_knowledge_areas"] = self._map_expert_knowledge(
            commits, prs
        )

        print("   Finding frequently modified files...")
        knowledge_data["frequently_modified_files"] = self._find_frequently_modified(
            commits, prs
        )

        return knowledge_data

    def _extract_from_comments(
        self, code_files: List[Dict], knowledge_data: Dict
    ) -> None:
        """Extract knowledge from code comments (OPTIMIZED)"""

        # Combined pattern for better performance
        comment_patterns = [
            (r"#\s*(.+)", "single"),  # Python, Ruby, Shell
            (r"//\s*(.+)", "single"),  # JavaScript, C++, Java
            (r"/\*\s*(.+?)\*/", "multi"),  # Multi-line comments
        ]

        for file_data in code_files:
            try:
                content = file_data.get("content", "")
                file_path = file_data.get("path", "")

                if not content or not file_path:
                    continue

                # Extract all comments efficiently
                all_comments = []
                for pattern, comment_type in comment_patterns:
                    matches = re.findall(
                        pattern, content, re.DOTALL if comment_type == "multi" else 0
                    )
                    all_comments.extend(matches)

                # Process comments
                for comment in all_comments:
                    comment_text = comment.strip()
                    comment_lower = comment_text.lower()

                    if len(comment_text) < 5:  # Skip very short comments
                        continue

                    # Check all categories
                    matched = False

                    # Workarounds and hacks
                    if any(
                        indicator in comment_lower
                        for indicator in self.knowledge_indicators["workarounds"]
                    ):
                        knowledge_data["workarounds_and_hacks"].append(
                            {
                                "file": file_path,
                                "comment": comment_text[:300],  # Limit length
                                "type": "workaround",
                                "severity": (
                                    "high" if "fixme" in comment_lower else "medium"
                                ),
                            }
                        )
                        matched = True

                    # Gotchas and warnings
                    if any(
                        indicator in comment_lower
                        for indicator in self.knowledge_indicators["gotchas"]
                    ):
                        knowledge_data["gotchas_and_warnings"].append(
                            {
                                "file": file_path,
                                "comment": comment_text[:300],
                                "type": "gotcha",
                                "severity": (
                                    "high" if "warning" in comment_lower else "medium"
                                ),
                            }
                        )
                        matched = True

                    # Design decisions
                    if any(
                        indicator in comment_lower
                        for indicator in self.knowledge_indicators["decisions"]
                    ):
                        knowledge_data["design_decisions"].append(
                            {
                                "file": file_path,
                                "comment": comment_text[:300],
                                "type": "decision",
                            }
                        )
                        matched = True

                    # Domain knowledge
                    if any(
                        indicator in comment_lower
                        for indicator in self.knowledge_indicators["domain_knowledge"]
                    ):
                        knowledge_data["domain_knowledge"].append(
                            {
                                "file": file_path,
                                "comment": comment_text[:300],
                                "type": "domain",
                            }
                        )
                        matched = True

                    # Technical debt
                    if any(
                        indicator in comment_lower
                        for indicator in self.knowledge_indicators["technical_debt"]
                    ):
                        knowledge_data["technical_debt"].append(
                            {
                                "file": file_path,
                                "comment": comment_text[:300],
                                "type": "debt",
                                "priority": (
                                    "high"
                                    if "must" in comment_lower
                                    or "urgent" in comment_lower
                                    else "normal"
                                ),
                            }
                        )
                        matched = True

            except Exception as e:
                print(
                    f"      ⚠️  Error processing file {file_data.get('path', 'unknown')}: {e}"
                )
                continue

    def _extract_from_commits(self, commits: List[Dict], knowledge_data: Dict) -> None:
        """Extract knowledge from commit messages (OPTIMIZED for async structure)"""

        for commit in commits:
            try:
                message = commit.get("message", "")
                if not message:
                    continue

                message_lower = message.lower()
                sha = commit.get("sha", "unknown")

                # Get author safely
                author_data = commit.get("author", {})
                if isinstance(author_data, dict):
                    author = (
                        author_data.get("name") or author_data.get("email") or "unknown"
                    )
                else:
                    author = str(author_data) if author_data else "unknown"

                # Look for explanation keywords
                if any(
                    word in message_lower
                    for word in ["because", "reason", "why", "fix for", "rationale"]
                ):
                    knowledge_data["design_decisions"].append(
                        {
                            "source": "commit",
                            "sha": sha[:8],
                            "message": message[:200],
                            "author": author,
                            "type": "commit_explanation",
                        }
                    )

                # Technical debt mentions
                if any(
                    word in message_lower
                    for word in ["debt", "refactor", "cleanup", "improve", "optimize"]
                ):
                    knowledge_data["technical_debt"].append(
                        {
                            "source": "commit",
                            "sha": sha[:8],
                            "message": message[:200],
                            "author": author,
                            "type": "debt_commit",
                        }
                    )

                # Workaround mentions
                if any(
                    word in message_lower
                    for word in ["workaround", "temporary", "hack", "quick fix"]
                ):
                    knowledge_data["workarounds_and_hacks"].append(
                        {
                            "source": "commit",
                            "sha": sha[:8],
                            "message": message[:200],
                            "author": author,
                            "type": "workaround_commit",
                        }
                    )

            except Exception as e:
                print(f"      ⚠️  Error processing commit: {e}")
                continue

    def _extract_from_issues(self, issues: List[Dict], knowledge_data: Dict) -> None:
        """
        Extract knowledge from issues (OPTIMIZED for async enriched data)

        NEW: Uses pre-fetched comments from async client
        """

        for issue in issues:
            try:
                title = issue.get("title", "")
                body = issue.get("body", "")
                number = issue.get("number")
                state = issue.get("state", "open")

                if not title and not body:
                    continue

                combined = f"{title} {body}".lower()

                # Get comments (NEW: pre-fetched by async client)
                comments = issue.get("comments", [])

                # Build full text including comments
                all_comments_text = " ".join(
                    [c.get("body", "") for c in comments if c.get("body")]
                )
                full_text = (combined + " " + all_comments_text).lower()

                # Bug patterns that reveal gotchas
                if any(
                    word in full_text
                    for word in [
                        "gotcha",
                        "unexpected",
                        "confusing",
                        "tricky",
                        "surprising",
                    ]
                ):
                    knowledge_data["gotchas_and_warnings"].append(
                        {
                            "source": "issue",
                            "number": number,
                            "title": title[:200],
                            "state": state,
                            "comments_count": len(comments),
                            "type": "issue_gotcha",
                            "has_discussion": len(comments) > 3,
                        }
                    )

                # Domain knowledge in requirements
                if any(
                    word in full_text
                    for word in [
                        "requirement",
                        "business",
                        "customer",
                        "user needs",
                        "stakeholder",
                    ]
                ):
                    knowledge_data["domain_knowledge"].append(
                        {
                            "source": "issue",
                            "number": number,
                            "title": title[:200],
                            "has_detailed_discussion": len(comments) > 3,
                            "type": "requirement",
                            "comments_count": len(comments),
                        }
                    )

                # Undocumented features
                if any(
                    word in full_text
                    for word in [
                        "undocumented",
                        "not documented",
                        "missing docs",
                        "no documentation",
                    ]
                ):
                    knowledge_data["undocumented_features"].append(
                        {
                            "source": "issue",
                            "number": number,
                            "title": title[:200],
                            "type": "undocumented",
                        }
                    )

                # Extract design decisions from issue discussions
                if len(comments) > 2:
                    for comment in comments:
                        try:
                            comment_body = comment.get("body", "")
                            if not comment_body:
                                continue

                            comment_lower = comment_body.lower()

                            if any(
                                word in comment_lower
                                for word in [
                                    "decided",
                                    "approach",
                                    "solution",
                                    "we should",
                                    "agreed",
                                ]
                            ):
                                user = comment.get("user", {})
                                author = (
                                    user.get("login", "unknown")
                                    if isinstance(user, dict)
                                    else "unknown"
                                )

                                knowledge_data["design_decisions"].append(
                                    {
                                        "source": "issue_comment",
                                        "issue_number": number,
                                        "comment_id": comment.get("id"),
                                        "author": author,
                                        "content_preview": comment_body[:200],
                                        "type": "issue_discussion",
                                    }
                                )
                        except Exception:
                            continue

            except Exception as e:
                print(
                    f"      ⚠️  Error processing issue #{issue.get('number', 'unknown')}: {e}"
                )
                continue

    def _extract_from_prs(self, prs: List[Dict], knowledge_data: Dict) -> None:
        """
        Extract knowledge from PRs (OPTIMIZED for async enriched data)

        NEW: Uses pre-fetched review_comments and line_comments from async client
        """

        for pr in prs:
            try:
                title = pr.get("title", "")
                body = pr.get("body", "")
                number = pr.get("number")
                is_merged = pr.get("is_merged", False)
                state = pr.get("state", "open")

                if not title and not body:
                    continue

                combined = f"{title} {body}".lower()

                # Get reviews and comments (NEW: pre-fetched by async client)
                review_comments = pr.get("review_comments", [])
                line_comments = pr.get("line_comments", [])

                # Build full text including all reviews
                all_review_text = " ".join(
                    [r.get("body", "") for r in review_comments if r.get("body")]
                )
                all_line_text = " ".join(
                    [c.get("body", "") for c in line_comments if c.get("body")]
                )

                full_text = (
                    combined + " " + all_review_text + " " + all_line_text
                ).lower()
                total_comments = len(review_comments) + len(line_comments)

                # Design decisions in PR descriptions and reviews
                if any(
                    word in full_text
                    for word in ["approach", "decided", "chose", "because", "rationale"]
                ):
                    knowledge_data["design_decisions"].append(
                        {
                            "source": "pr",
                            "number": number,
                            "title": title[:200],
                            "is_merged": is_merged,
                            "has_review_discussion": total_comments > 0,
                            "comments_count": total_comments,
                            "type": "pr_decision",
                        }
                    )

                # Refactoring and debt reduction
                if any(
                    word in full_text
                    for word in ["refactor", "cleanup", "improve", "optimize", "debt"]
                ):
                    knowledge_data["technical_debt"].append(
                        {
                            "source": "pr",
                            "number": number,
                            "title": title[:200],
                            "files_changed": pr.get("changed_files_count", 0),
                            "is_merged": is_merged,
                            "type": "refactor_pr",
                        }
                    )

                # Extract knowledge from line-by-line comments (code-level insights)
                for line_comment in line_comments:
                    try:
                        comment_body = line_comment.get("body", "")
                        if not comment_body:
                            continue

                        comment_lower = comment_body.lower()
                        file_path = line_comment.get("path", "")

                        user = line_comment.get("user", {})
                        author = (
                            user.get("login", "unknown")
                            if isinstance(user, dict)
                            else "unknown"
                        )

                        # Gotchas mentioned in code review
                        if any(
                            word in comment_lower
                            for word in [
                                "gotcha",
                                "careful",
                                "watch out",
                                "note",
                                "warning",
                            ]
                        ):
                            knowledge_data["gotchas_and_warnings"].append(
                                {
                                    "source": "pr_line_comment",
                                    "pr_number": number,
                                    "file": file_path,
                                    "comment": comment_body[:200],
                                    "author": author,
                                    "type": "code_review_gotcha",
                                }
                            )

                        # Workarounds identified in reviews
                        if any(
                            word in comment_lower
                            for word in ["workaround", "hack", "temporary", "quick fix"]
                        ):
                            knowledge_data["workarounds_and_hacks"].append(
                                {
                                    "source": "pr_line_comment",
                                    "pr_number": number,
                                    "file": file_path,
                                    "comment": comment_body[:200],
                                    "author": author,
                                    "type": "review_workaround",
                                }
                            )

                    except Exception:
                        continue

            except Exception as e:
                print(
                    f"      ⚠️  Error processing PR #{pr.get('number', 'unknown')}: {e}"
                )
                continue

    def _identify_complex_areas(self, code_files: List[Dict]) -> List[Dict]:
        """Identify complex code areas that need documentation (OPTIMIZED)"""
        complex_areas = []

        for file_data in code_files:
            try:
                file_path = file_data.get("path", "")
                content = file_data.get("content", "")
                lines = file_data.get("lines", 0)

                if not content or lines == 0:
                    continue

                # Calculate complexity indicators
                complexity_score = 0
                indicators = []

                # Long files
                if lines > 500:
                    complexity_score += 2
                    indicators.append(f"long_file ({lines} lines)")

                # High nesting depth (optimized calculation)
                content_lines = content.split("\n")
                non_empty_lines = [line for line in content_lines if line.strip()]
                if non_empty_lines:
                    max_indent = max(
                        [len(line) - len(line.lstrip()) for line in non_empty_lines],
                        default=0,
                    )
                    if max_indent > 16:
                        complexity_score += 2
                        indicators.append(f"deep_nesting ({max_indent//4} levels)")

                # Many conditional statements
                conditional_count = len(
                    re.findall(r"\b(if|elif|else|switch|case|when)\b", content)
                )
                if conditional_count > 20:
                    complexity_score += 1
                    indicators.append(f"many_conditionals ({conditional_count})")

                # Many function definitions
                function_count = len(
                    re.findall(r"\b(def|function|func|fn)\s+\w+", content)
                )
                if function_count > 15:
                    complexity_score += 1
                    indicators.append(f"many_functions ({function_count})")

                # Complex regex patterns
                regex_count = len(
                    re.findall(r"(re\.|RegExp|regex|\/.*\/[gimuy]*)", content)
                )
                if regex_count > 5:
                    complexity_score += 1
                    indicators.append(f"complex_regex ({regex_count})")

                # Low comment ratio
                comment_lines = len(re.findall(r"^\s*[#/]", content, re.MULTILINE))
                comment_ratio = comment_lines / lines if lines > 0 else 0
                if comment_ratio < 0.1 and lines > 100:
                    complexity_score += 1
                    indicators.append(f"low_comments ({comment_ratio:.1%})")

                # Long functions (NEW)
                long_functions = len(
                    re.findall(r"(def|function)\s+\w+[^}]{500,}", content, re.DOTALL)
                )
                if long_functions > 0:
                    complexity_score += 1
                    indicators.append(f"long_functions ({long_functions})")

                # Store if complex enough
                if complexity_score >= 3:
                    complex_areas.append(
                        {
                            "file": file_path,
                            "complexity_score": complexity_score,
                            "indicators": indicators,
                            "lines": lines,
                            "priority": (
                                "critical"
                                if complexity_score >= 6
                                else ("high" if complexity_score >= 5 else "medium")
                            ),
                        }
                    )

            except Exception as e:
                print(
                    f"      ⚠️  Error analyzing complexity for {file_data.get('path', 'unknown')}: {e}"
                )
                continue

        # Sort by complexity score
        complex_areas.sort(key=lambda x: x["complexity_score"], reverse=True)
        return complex_areas[:20]  # Top 20 most complex

    def _map_expert_knowledge(
        self, commits: List[Dict], prs: List[Dict]
    ) -> Dict[str, Any]:
        """
        Map which developers are experts in which areas (OPTIMIZED for async data)

        UPDATED: Handles new PR structure with changed_files as list of dicts
        """

        file_expertise = defaultdict(lambda: defaultdict(int))
        developer_areas = defaultdict(set)

        # Analyze commits (optimized)
        for commit in commits:
            try:
                if not isinstance(commit, dict):
                    continue

                # Get author safely
                author_data = commit.get("author", {})
                if isinstance(author_data, dict):
                    author = (
                        author_data.get("name") or author_data.get("email") or "unknown"
                    )
                else:
                    author = str(author_data) if author_data else "unknown"

                # Note: Async client doesn't include changed_files in commits
                # We rely on PR data for file expertise mapping

            except Exception:
                continue

        # Analyze PRs (handles new async structure)
        for pr in prs:
            try:
                if not isinstance(pr, dict):
                    continue

                # Get author safely
                user_data = pr.get("user", {})
                if isinstance(user_data, dict):
                    author = user_data.get("login") or "unknown"
                else:
                    author = str(user_data) if user_data else "unknown"

                # Get changed files (NEW async structure)
                changed_files = pr.get("changed_files", [])

                # Extract filenames from dict objects
                for file_item in changed_files:
                    try:
                        if isinstance(file_item, dict):
                            file_path = file_item.get("filename")
                        elif isinstance(file_item, str):
                            file_path = file_item
                        else:
                            continue

                        if file_path:
                            file_expertise[file_path][author] += 1

                            # Extract module/area from path
                            if "/" in file_path:
                                area = file_path.split("/")[0]
                                developer_areas[author].add(area)
                    except Exception:
                        continue

            except Exception:
                continue

        # Build expertise map
        expertise_map = {
            "file_experts": {},
            "developer_specializations": {},
            "critical_knowledge_holders": [],
        }

        # File experts (top contributor to each file)
        for file_path, authors in file_expertise.items():
            if authors:
                try:
                    top_expert = max(authors.items(), key=lambda x: x[1])
                    expertise_map["file_experts"][file_path] = {
                        "expert": top_expert[0],
                        "contributions": top_expert[1],
                        "all_contributors": dict(authors),
                    }
                except Exception:
                    continue

        # Developer specializations
        for developer, areas in developer_areas.items():
            expertise_map["developer_specializations"][developer] = {
                "areas": list(areas),
                "area_count": len(areas),
            }

        # Critical knowledge holders (experts in many areas)
        critical_developers = [
            {"developer": dev, "areas": len(areas), "area_list": list(areas)[:5]}
            for dev, areas in developer_areas.items()
            if len(areas) >= 3
        ]
        critical_developers.sort(key=lambda x: x["areas"], reverse=True)
        expertise_map["critical_knowledge_holders"] = critical_developers[:10]  # Top 10

        return expertise_map

    def _find_frequently_modified(
        self, commits: List[Dict], prs: List[Dict]
    ) -> List[Dict]:
        """
        Find files that are frequently modified (OPTIMIZED - uses PR data)

        NEW: Uses PR changed_files since async commits don't include file lists
        """

        file_modifications = defaultdict(int)
        file_authors = defaultdict(set)

        # Use PR data for file modification tracking (more reliable)
        for pr in prs:
            try:
                user_data = pr.get("user", {})
                if isinstance(user_data, dict):
                    author = user_data.get("login", "unknown")
                else:
                    author = "unknown"

                changed_files = pr.get("changed_files", [])

                for file_item in changed_files:
                    try:
                        if isinstance(file_item, dict):
                            file_path = file_item.get("filename")
                        elif isinstance(file_item, str):
                            file_path = file_item
                        else:
                            continue

                        if file_path:
                            file_modifications[file_path] += 1
                            file_authors[file_path].add(author)
                    except Exception:
                        continue

            except Exception:
                continue

        # Build list of frequently modified files
        frequent_files = []
        for file_path, count in file_modifications.items():
            if count >= 3:  # Modified in at least 3 PRs
                try:
                    frequent_files.append(
                        {
                            "file": file_path,
                            "modification_count": count,
                            "unique_authors": len(file_authors[file_path]),
                            "authors": list(file_authors[file_path])[
                                :5
                            ],  # Limit to top 5
                            "stability": (
                                "unstable"
                                if count > 10
                                else ("moderate" if count > 5 else "stable")
                            ),
                        }
                    )
                except Exception:
                    continue

        # Sort by modification count
        frequent_files.sort(key=lambda x: x["modification_count"], reverse=True)
        return frequent_files[:30]  # Top 30 most modified
