"""
Event Normalizer - UPDATED FOR ASYNC DATA STRUCTURE
Converts GitHub events (issues, PRs, commits) into unified format
Compatible with AsyncGitHubClient data structure
"""

from typing import Dict, Any, List
from datetime import datetime


class EventNormalizer:
    """Normalizes different event types into a unified format for knowledge extraction"""

    def __init__(self):
        self.event_types = {
            "commit": self._normalize_commit,
            "issue": self._normalize_issue,
            "pr": self._normalize_pr,
            "pull_request": self._normalize_pr,  # Alias
        }

    def normalize_github_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize any GitHub event into unified format

        Args:
            event: Raw event data with 'type' and 'payload' keys

        Returns:
            Normalized event dictionary
        """
        event_type = event.get("type", "").lower()
        payload = event.get("payload", {})

        normalizer = self.event_types.get(event_type)
        if normalizer:
            return normalizer(payload)

        # Fallback for unknown types
        return self._normalize_generic(event)

    def _normalize_commit(self, commit: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize commit event

        NEW: Handles lightweight commit structure from async client
        """
        # Extract author info (handles both sync and async structures)
        author_data = commit.get("author", {})
        if isinstance(author_data, dict):
            author_name = author_data.get("name", "unknown")
            author_email = author_data.get("email", "")
        else:
            author_name = str(author_data) if author_data else "unknown"
            author_email = ""

        # Get commit date
        commit_date = commit.get("date") or commit.get("created_at", "")

        # Get message
        message = commit.get("message", "")

        # Detect knowledge signals in commit message
        tags = self._extract_knowledge_tags(message, "commit")

        # Extract linked issues/PRs from message
        linked_items = self._extract_linked_items_from_text(message)

        normalized = {
            "event_type": "commit",
            "id": commit.get("sha", "")[:8],  # Short SHA
            "title": message.split("\n")[0] if message else "No message",
            "description": message,
            "author": author_name,
            "author_email": author_email,
            "date": commit_date,
            "tags": tags,
            "metadata": {
                "sha": commit.get("sha"),
                "full_message": message,
                "linked_issues": linked_items.get("issues", []),
                "linked_prs": linked_items.get("prs", []),
            },
        }

        return normalized

    def _normalize_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize issue event
        
        FIXED: Handles both comments as int (count) and list (actual comments)
        """
        number = issue.get('number')
        title = issue.get('title', '')
        body = issue.get('body', '')
        state = issue.get('state', 'open')
        
        # User info
        user = issue.get('user', {})
        author = user.get('login', 'unknown') if isinstance(user, dict) else 'unknown'
        
        # Dates
        created_at = issue.get('created_at', '')
        updated_at = issue.get('updated_at', '')
        closed_at = issue.get('closed_at')
        
        # FIXED: Handle comments as either int or list
        comments_data = issue.get('comments', [])
        
        if isinstance(comments_data, int):
            # It's a count, not actual comments
            comments_count = comments_data
            comments = []
        elif isinstance(comments_data, list):
            # It's actual comment objects
            comments = comments_data
            comments_count = len(comments)
        else:
            # Fallback
            comments = []
            comments_count = 0
        
        # Also check for 'comments_data' key (from async client)
        if 'comments_data' in issue:
            comments = issue.get('comments_data', [])
            comments_count = len(comments) if isinstance(comments, list) else 0
        
        # Linked PRs (from async client)
        linked_prs = issue.get('linked_prs', [])
        is_resolved = issue.get('is_truly_resolved', False)
        resolution_status = issue.get('resolution_status', 'open')
        
        # Labels
        labels = issue.get('labels', [])
        
        # Extract knowledge tags from title, body, and comments
        combined_text = f"{title} {body}"
        if isinstance(comments, list):
            for comment in comments:
                if isinstance(comment, dict):
                    combined_text += f" {comment.get('body', '')}"
        
        tags = self._extract_knowledge_tags(combined_text, 'issue')
        
        # Add resolution-based tags
        if is_resolved:
            tags.append('resolved')
        if state == 'closed':
            tags.append('closed')
        if comments_count > 5:
            tags.append('high_discussion')
        
        normalized = {
            'event_type': 'issue',
            'id': f"issue-{number}",
            'title': title,
            'description': body[:500] if body else '',
            'author': author,
            'date': created_at,
            'tags': tags,
            'metadata': {
                'number': number,
                'state': state,
                'resolution_status': resolution_status,
                'is_truly_resolved': is_resolved,
                'labels': labels,
                'comments_count': comments_count,
                'linked_prs': linked_prs,
                'created_at': created_at,
                'updated_at': updated_at,
                'closed_at': closed_at,
                'html_url': issue.get('html_url'),
                'has_detailed_discussion': comments_count > 3,
            }
        }
        
        return normalized

    def _normalize_pr(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize pull request event (FIXED - includes changed_files and accurate merged status)
        """
        number = pr.get('number')
        title = pr.get('title', '')
        body = pr.get('body', '')
        state = pr.get('state', 'open')

        # FIXED: Robust Merged Status Check
        # Check 'is_merged' (our enriched flag), 'merged' (GitHub API flag), or 'merged_at' date
        is_merged = pr.get('is_merged', False)
        if pr.get('merged') is True:
            is_merged = True
        elif not is_merged and pr.get('merged_at'):
            is_merged = True
        
        # User info
        user = pr.get('user', {})
        author = user.get('login', 'unknown') if isinstance(user, dict) else 'unknown'
        
        # Dates
        created_at = pr.get('created_at', '')
        merged_at = pr.get('merged_at')
        closed_at = pr.get('closed_at')
        
        # FIXED: Changed files handling
        # It might be a list (from enrichment) or an int (from raw summary)
        raw_files_data = pr.get('changed_files', [])
        
        if isinstance(raw_files_data, list):
            changed_files = raw_files_data
            # Prefer the explicit count from metadata if available (more accurate), else list length
            changed_files_count = pr.get('changed_files_count', len(changed_files))
        else:
            changed_files = []
            # If raw data is just an int, use it as the count
            changed_files_count = raw_files_data if isinstance(raw_files_data, int) else 0

        # Reviews and comments
        review_comments = pr.get('review_comments', [])
        line_comments = pr.get('line_comments', [])
        total_comments = (
            (len(review_comments) if isinstance(review_comments, list) else 0) +
            (len(line_comments) if isinstance(line_comments, list) else 0)
        )
        
        # Linked issues
        linked_issues = pr.get('linked_issues', [])
        
        # FIXED: Handle commits as either list or count
        commits = pr.get('commits', [])
        if isinstance(commits, list):
            commits_count = len(commits)
        elif isinstance(commits, int):
            commits_count = commits
            commits = []
        else:
            commits_count = pr.get('commits_count', 0)
            commits = []
        
        # Also check pr_commits key (from enrichment)
        if 'pr_commits' in pr:
            pr_commits = pr.get('pr_commits', [])
            if isinstance(pr_commits, list):
                commits = pr_commits
                commits_count = len(pr_commits)
        
        # Extract knowledge tags
        combined_text = f"{title} {body}"
        if isinstance(review_comments, list):
            for review in review_comments:
                if isinstance(review, dict):
                    combined_text += f" {review.get('body', '')}"
        if isinstance(line_comments, list):
            for comment in line_comments:
                if isinstance(comment, dict):
                    combined_text += f" {comment.get('body', '')}"
        
        tags = self._extract_knowledge_tags(combined_text, 'pr')
        
        # Add PR-specific tags
        if is_merged:
            tags.append('merged')
        if state == 'closed' and not is_merged:
            tags.append('closed_unmerged')
        if changed_files_count > 20:
            tags.append('large_pr')
        if total_comments > 10:
            tags.append('heavily_reviewed')
        if linked_issues:
            tags.append('fixes_issue')
        
        # Analyze changed files for patterns
        file_patterns = self._analyze_changed_files(changed_files)
        
        normalized = {
            'event_type': 'pull_request',
            'id': f"pr-{number}",
            'title': title,
            'description': body[:500] if body else '',
            'author': author,
            'date': created_at,
            'tags': tags,
            'metadata': {
                'number': number,
                'state': state,
                'is_merged': is_merged,
                'changed_files_count': changed_files_count,
                'changed_files': changed_files,
                'commits_count': commits_count,
                'total_comments': total_comments,
                'linked_issues': linked_issues,
                'created_at': created_at,
                'merged_at': merged_at,
                'closed_at': closed_at,
                'html_url': pr.get('html_url'),
                'file_patterns': file_patterns,
                'has_code_review': total_comments > 0,
                'additions': pr.get('additions', 0),
                'deletions': pr.get('deletions', 0),
                'merged_by': pr.get('merged_by', {}).get('login') if pr.get('merged_by') else None,
            }
        }
        
        return normalized

    def _normalize_generic(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback normalizer for unknown event types"""
        return {
            "event_type": "unknown",
            "id": str(event.get("id", "unknown")),
            "title": str(event.get("title", "Unknown Event")),
            "description": "",
            "author": "unknown",
            "date": event.get("created_at", ""),
            "tags": ["unknown"],
            "metadata": event,
        }

    def _extract_knowledge_tags(self, text: str, event_type: str) -> List[str]:
        """
        Extract knowledge-related tags from text content

        Tags help categorize events for onboarding/offboarding knowledge extraction
        """
        if not text:
            return [event_type]

        text_lower = text.lower()
        tags = [event_type]

        # Onboarding-related keywords
        onboarding_keywords = [
            "setup",
            "install",
            "configure",
            "getting started",
            "quickstart",
            "documentation",
            "readme",
            "guide",
            "tutorial",
            "how to",
            "architecture",
            "design",
            "structure",
            "overview",
        ]

        # Offboarding-related keywords
        offboarding_keywords = [
            "workaround",
            "hack",
            "temporary",
            "fixme",
            "todo",
            "bug",
            "gotcha",
            "careful",
            "warning",
            "important",
            "note",
            "decision",
            "reason",
            "why",
            "because",
            "chosen",
            "technical debt",
            "refactor",
            "cleanup",
            "improve",
        ]

        # Knowledge keywords
        knowledge_keywords = [
            "explained",
            "understand",
            "clarify",
            "context",
            "background",
            "learned",
            "discovered",
            "found out",
            "realized",
            "pattern",
            "approach",
            "solution",
            "alternative",
        ]

        # Check for keyword matches
        for keyword in onboarding_keywords:
            if keyword in text_lower:
                tags.append("onboarding")
                break

        for keyword in offboarding_keywords:
            if keyword in text_lower:
                tags.append("offboarding")
                break

        for keyword in knowledge_keywords:
            if keyword in text_lower:
                tags.append("knowledge")
                break

        # Additional context tags
        if "breaking change" in text_lower:
            tags.append("breaking_change")

        if any(word in text_lower for word in ["security", "vulnerability", "cve"]):
            tags.append("security")

        if any(
            word in text_lower
            for word in ["performance", "optimization", "speed", "slow"]
        ):
            tags.append("performance")

        if any(word in text_lower for word in ["deprecat", "obsolete", "removed"]):
            tags.append("deprecation")

        if any(word in text_lower for word in ["test", "testing", "spec", "coverage"]):
            tags.append("testing")

        # Remove duplicates
        return list(set(tags))

    def _extract_linked_items_from_text(self, text: str) -> Dict[str, List[int]]:
        """
        Extract linked issues and PRs from text (e.g., "fixes #123", "closes #456")
        """
        import re

        linked = {"issues": [], "prs": []}

        if not text:
            return linked

        # Pattern: fixes/closes/resolves #123
        patterns = [
            r"(?:fix(?:es|ed)?|close(?:s|d)?|resolve(?:s|d)?)\s*#(\d+)",
            r"#(\d+)",  # Generic reference
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    num = int(match)
                    # We can't distinguish issues from PRs just from number
                    # So we add to both and let downstream processing handle it
                    if num not in linked["issues"]:
                        linked["issues"].append(num)
                except ValueError:
                    continue

        return linked

    def _analyze_changed_files(self, changed_files: List[Dict]) -> Dict[str, Any]:
        """
        Analyze changed files to extract patterns

        NEW: Works with async client's changed_files structure
        """
        if not changed_files:
            return {}

        patterns = {
            "file_types": {},
            "directories": {},
            "total_additions": 0,
            "total_deletions": 0,
            "largest_change": None,
        }

        max_changes = 0

        for file_item in changed_files:
            # Handle both dict and string formats
            if isinstance(file_item, dict):
                filename = file_item.get("filename", "")
                additions = file_item.get("additions", 0)
                deletions = file_item.get("deletions", 0)
                changes = file_item.get("changes", 0)
            else:
                filename = str(file_item)
                additions = 0
                deletions = 0
                changes = 0

            if not filename:
                continue

            # Extract file extension
            if "." in filename:
                ext = filename.split(".")[-1]
                patterns["file_types"][ext] = patterns["file_types"].get(ext, 0) + 1

            # Extract directory
            if "/" in filename:
                directory = filename.split("/")[0]
                patterns["directories"][directory] = (
                    patterns["directories"].get(directory, 0) + 1
                )

            # Track changes
            patterns["total_additions"] += additions
            patterns["total_deletions"] += deletions

            # Track largest change
            if changes > max_changes:
                max_changes = changes
                patterns["largest_change"] = {
                    "filename": filename,
                    "changes": changes,
                    "additions": additions,
                    "deletions": deletions,
                }

        return patterns

    def normalize_teams_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Teams message (if you're using Teams integration)

        Kept for backwards compatibility
        """
        return {
            "event_type": "teams_message",
            "id": message.get("id", "unknown"),
            "title": message.get("subject", "No Subject"),
            "description": message.get("body", {}).get("content", "")[:500],
            "author": message.get("from", {})
            .get("user", {})
            .get("displayName", "unknown"),
            "date": message.get("createdDateTime", ""),
            "tags": ["teams", "communication"],
            "metadata": {
                "message_type": message.get("messageType", "message"),
                "importance": message.get("importance", "normal"),
            },
        }

    def batch_normalize(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a batch of events

        Args:
            events: List of raw events

        Returns:
            List of normalized events
        """
        normalized_events = []

        for event in events:
            try:
                normalized = self.normalize_github_event(event)
                normalized_events.append(normalized)
            except Exception as e:
                print(f"⚠️  Error normalizing event: {e}")
                # Add a fallback normalized event
                normalized_events.append(self._normalize_generic(event))

        return normalized_events

    def get_event_statistics(
        self, normalized_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate statistics from normalized events

        Useful for understanding the knowledge base composition
        """
        stats = {
            "total_events": len(normalized_events),
            "by_type": {},
            "by_tag": {},
            "by_author": {},
            "date_range": {"earliest": None, "latest": None},
        }

        for event in normalized_events:
            # Count by type
            event_type = event.get("event_type", "unknown")
            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1

            # Count by tags
            for tag in event.get("tags", []):
                stats["by_tag"][tag] = stats["by_tag"].get(tag, 0) + 1

            # Count by author
            author = event.get("author", "unknown")
            stats["by_author"][author] = stats["by_author"].get(author, 0) + 1

            # Track date range
            event_date = event.get("date")
            if event_date:
                if (
                    stats["date_range"]["earliest"] is None
                    or event_date < stats["date_range"]["earliest"]
                ):
                    stats["date_range"]["earliest"] = event_date
                if (
                    stats["date_range"]["latest"] is None
                    or event_date > stats["date_range"]["latest"]
                ):
                    stats["date_range"]["latest"] = event_date

        return stats
