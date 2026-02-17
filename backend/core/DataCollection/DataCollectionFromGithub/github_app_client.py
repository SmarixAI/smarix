"""
Async GitHub App Client - For Private Repository Access
Uses GitHub App installation tokens instead of personal access tokens
Compatible with all AsyncGitHubClient methods
"""

import asyncio
import aiohttp
import time
import jwt
import os
import re
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from tqdm.asyncio import tqdm as async_tqdm
import logging

logger = logging.getLogger(__name__)


class AsyncGitHubAppClient:
    """
    Async GitHub API client using GitHub App authentication
    
    Key differences from AsyncGitHubClient:
    - Uses installation tokens (1-hour validity) instead of personal tokens
    - Generates JWT for authentication
    - Auto-refreshes tokens when needed
    - Can access private repositories the app is installed on
    
    All methods are identical to AsyncGitHubClient for compatibility
    """

    def __init__(
        self,
        installation_id: int,
        app_id: str = None,
        private_key: str = None,
        max_concurrent_requests: int = 50
    ):
        """
        Args:
            installation_id: GitHub App installation ID (from webhook/callback)
            app_id: GitHub App ID (from environment if not provided)
            private_key: GitHub App private key PEM (from environment if not provided)
            max_concurrent_requests: Max concurrent requests (default: 50)
        """
        self.installation_id = installation_id
        self.app_id = app_id or os.getenv("GITHUB_APP_ID")
        
        # Handle private key from environment (may have escaped newlines)
        raw_key = private_key or os.getenv("GITHUB_PRIVATE_KEY")
        if raw_key:
            # Replace literal \n with actual newlines if needed
            self.private_key = raw_key.replace("\\n", "\n")
        else:
            self.private_key = None
        
        if not self.app_id or not self.private_key:
            raise ValueError(
                "GitHub App credentials not found. Set GITHUB_APP_ID and GITHUB_PRIVATE_KEY in environment"
            )
        
        # Token management
        self.installation_token = None
        self.token_expires_at = None
        
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
        
        self.base_url = "https://api.github.com"

    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=50),
        )
        
        # Generate initial installation token
        await self._refresh_installation_token()
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    def _generate_jwt(self) -> str:
        """
        Generate JWT for GitHub App authentication
        
        Returns:
            JWT token string valid for 10 minutes
        """
        now = int(time.time())
        payload = {
            "iat": now,           # Issued at
            "exp": now + 600,     # Expires in 10 minutes
            "iss": self.app_id    # GitHub App ID
        }
        
        # Sign with RS256
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    async def _refresh_installation_token(self) -> None:
        """
        Generate or refresh installation access token
        
        Flow:
        1. Generate JWT using app private key
        2. Exchange JWT for installation access token (1-hour validity)
        3. Cache token until 5 minutes before expiry
        """
        # Check if current token is still valid (with 5-minute buffer)
        if self.installation_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at - timedelta(minutes=5):
                return  # Token still valid
        
        print(f"🔄 Generating new installation token for installation {self.installation_id}...")
        
        # Step 1: Generate JWT
        jwt_token = self._generate_jwt()
        
        # Step 2: Exchange for installation token
        url = f"{self.base_url}/app/installations/{self.installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        async with self.session.post(url, headers=headers) as response:
            if response.status != 201:
                error_text = await response.text()
                raise Exception(f"Failed to get installation token: {response.status} - {error_text}")
            
            data = await response.json()
            self.installation_token = data["token"]
            
            # Parse expiry (format: "2024-01-01T12:00:00Z")
            expires_at_str = data["expires_at"]
            self.token_expires_at = datetime.strptime(expires_at_str, "%Y-%m-%dT%H:%M:%SZ")
            
            print(f"✅ Installation token generated (expires at {self.token_expires_at})")

    def _build_headers(self) -> Dict[str, str]:
        """Build headers with installation token"""
        return {
            "Authorization": f"Bearer {self.installation_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Smarix-GitHub-App-Client"
        }

    async def test_connection(self) -> bool:
        """Test GitHub API connection"""
        url = f"{self.base_url}/rate_limit"
        try:
            headers = self._build_headers()
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    core_limit = data["resources"]["core"]
                    self.rate_limit_remaining = core_limit["remaining"]
                    self.rate_limit_reset = core_limit["reset"]
                    print(f"✅ GitHub App API connected")
                    print(f"📊 Rate limit: {core_limit['remaining']}/{core_limit['limit']}")
                    print(f"🔄 Reset time: {time.ctime(core_limit['reset'])}")
                    return True
                else:
                    print(f"❌ GitHub API connection failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    async def _wait_for_rate_limit(self):
        """Wait if rate limit is low"""
        if self.rate_limit_remaining < 10:
            wait_time = max(0, self.rate_limit_reset - time.time())
            if wait_time > 0:
                logger.warning(f"Rate limit low ({self.rate_limit_remaining}), waiting {wait_time:.0f}s")
                await asyncio.sleep(min(wait_time, 60))

    async def _make_request(
        self, url: str, params: dict = None, max_retries: int = 3
    ) -> Optional[Dict]:
        """
        Make async request with retry logic and token refresh
        
        Automatically refreshes installation token if needed
        """
        async with self.semaphore:
            # Ensure token is valid before making request
            await self._refresh_installation_token()
            
            for attempt in range(max_retries):
                try:
                    await self._wait_for_rate_limit()
                    
                    headers = self._build_headers()
                    async with self.session.get(url, params=params, headers=headers) as response:
                        # Update rate limit info
                        if "X-RateLimit-Remaining" in response.headers:
                            self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
                        if "X-RateLimit-Reset" in response.headers:
                            self.rate_limit_reset = int(response.headers["X-RateLimit-Reset"])
                        
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 404:
                            return None
                        elif response.status == 403:
                            retry_after = int(response.headers.get("Retry-After", 60))
                            logger.warning(f"Rate limit hit, waiting {retry_after}s")
                            await asyncio.sleep(retry_after)
                            continue
                        elif response.status == 401:
                            # Token might be expired, refresh and retry
                            logger.warning("401 Unauthorized, refreshing token...")
                            self.installation_token = None  # Force refresh
                            await self._refresh_installation_token()
                            continue
                        elif response.status == 422:
                            logger.error(f"422 error for {url}: Invalid parameters")
                            return None
                        elif response.status >= 500:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            logger.error(f"Request failed: {response.status} for {url}")
                            return None
                
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries} for {url}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    continue
                except Exception as e:
                    logger.error(f"Error in request (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                    continue
            
            return None

    async def _paginate_all(
        self, url: str, params: dict = None, max_pages: int = None
    ) -> List[Dict]:
        """
        Fetch all pages for a paginated endpoint
        """
        if params is None:
            params = {}
        
        params["per_page"] = 100
        per_page = params["per_page"]
        
        params["page"] = 1
        first_page = await self._make_request(url, params)
        
        if not first_page:
            return []
        
        results = first_page if isinstance(first_page, list) else [first_page]
        
        if len(results) < per_page:
            return results
        
        if max_pages is None:
            max_pages = 100
        
        current_page = 2
        batch_size = 10
        
        while current_page <= max_pages:
            batch_end = min(current_page + batch_size, max_pages + 1)
            
            page_tasks = []
            for page in range(current_page, batch_end):
                page_params = params.copy()
                page_params["page"] = page
                page_tasks.append(self._make_request(url, page_params))
            
            if not page_tasks:
                break
            
            pages = await asyncio.gather(*page_tasks)
            
            found_last_page = False
            for page_data in pages:
                if page_data and isinstance(page_data, list):
                    if len(page_data) == 0:
                        found_last_page = True
                        break
                    results.extend(page_data)
                    if len(page_data) < per_page:
                        found_last_page = True
                        break
                else:
                    found_last_page = True
                    break
            
            if found_last_page:
                break
            
            current_page = batch_end
        
        return results

    # ============================================
    # Repository Data Methods (Identical to AsyncGitHubClient)
    # ============================================

    async def get_repository_metadata(self, owner: str, repo: str) -> Dict:
        """Fetch repository metadata"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = await self._make_request(url)
        
        if response:
            return {
                "name": response.get("name"),
                "description": response.get("description"),
                "language": response.get("language"),
                "topics": response.get("topics", []),
                "stars": response.get("stargazers_count"),
                "forks": response.get("forks_count"),
                "size": response.get("size"),
                "created_at": response.get("created_at"),
                "updated_at": response.get("updated_at"),
                "default_branch": response.get("default_branch"),
                "private": response.get("private", False),
            }
        return {}

    async def get_repository_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """Get repository contents at path"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        response = await self._make_request(url)
        return response if response else []

    async def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """
        Get file content using GitHub API (works for private repos)

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path in repository

        Returns:
            Decoded file content as string
        """
        try:
            # Use API endpoint instead of raw download URL
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"

            # Refresh token if needed
            await self._refresh_installation_token()

            headers = self._build_headers()

            async with self.session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()

                    # GitHub API returns base64-encoded content for files
                    if data.get('encoding') == 'base64' and data.get('content'):
                        import base64
                        # Remove newlines from base64 string (GitHub adds them)
                        b64_content = data['content'].replace('\n', '')
                        decoded = base64.b64decode(b64_content).decode('utf-8', errors='ignore')
                        return decoded
                    else:
                        # Fallback for non-base64 (shouldn't happen for files)
                        return data.get('content', '')
                elif response.status == 404:
                    logger.warning(f"File not found: {path}")
                    return ""
                else:
                    logger.error(f"Failed to get file {path}: {response.status}")
                    return ""

        except Exception as e:
            logger.error(f"Error fetching file {path}: {e}")
            return ""

    async def get_file_content_from_url(self, download_url: str) -> str:
        """
        DEPRECATED: Use get_file_content() instead

        Download file content from raw URL (doesn't work well for private repos)
        Kept for backward compatibility
        """
        try:
            await self._refresh_installation_token()
            headers = self._build_headers()

            async with self.session.get(download_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
        return ""

    # ============================================
    # Issues Methods
    # ============================================

    async def fetch_issues_batch(
        self, owner: str, repo: str, state: str = "all", limit: int = None
    ) -> List[Dict]:
        """
        Fetch ALL issues with complete data concurrently
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        
        params = {
            "state": state if state else "all",
            "sort": "updated",
            "direction": "desc",
        }
        
        max_pages = (limit // 100 + 1) if limit else 100
        
        print(f"      📥 Fetching issues (state={params['state']})...")
        
        try:
            all_issues = await self._paginate_all(url, params, max_pages)
        except Exception as e:
            print(f"      ⚠️  Error fetching issues: {e}")
            return []
        
        # Filter out PRs (they appear in /issues endpoint)
        issues = [item for item in all_issues if not item.get("pull_request")]
        
        print(f"      ✓ Found {len(issues)} issues (filtered from {len(all_issues)} items)")
        
        if limit:
            issues = issues[:limit]
        
        if not issues:
            print(f"      ℹ️  No issues found")
            return []
        
        # Fetch comments for all issues concurrently
        print(f"   Fetching comments for {len(issues)} issues...")
        comment_tasks = [
            self._fetch_issue_comments(owner, repo, issue["number"]) for issue in issues
        ]
        
        try:
            comments_results = await async_tqdm.gather(
                *comment_tasks, desc="Fetching issue comments"
            )
        except Exception as e:
            print(f"      ⚠️  Error fetching some comments: {e}")
            comments_results = [[] for _ in issues]
        
        # Replace 'comments' (count) with actual comment data
        for issue, comments in zip(issues, comments_results):
            issue["comments_count_original"] = issue.get("comments", 0)
            issue["comments"] = comments if isinstance(comments, list) else []
            issue["comments_data"] = comments if isinstance(comments, list) else []
        
        return issues

    async def _fetch_issue_comments(
        self, owner: str, repo: str, issue_number: int
    ) -> List[Dict]:
        """Fetch all comments for a specific issue"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        comments = await self._paginate_all(url, max_pages=5)
        
        return [
            {
                "id": comment.get("id"),
                "user": {
                    "login": comment.get("user", {}).get("login"),
                    "html_url": comment.get("user", {}).get("html_url"),
                },
                "body": comment.get("body", ""),
                "created_at": comment.get("created_at"),
                "updated_at": comment.get("updated_at"),
                "html_url": comment.get("html_url"),
            }
            for comment in comments
        ]

    # ============================================
    # Pull Requests Methods
    # ============================================

    async def fetch_prs_batch(
        self, owner: str, repo: str, state: str = "all", limit: int = None
    ) -> List[Dict]:
        """
        Fetch ALL pull requests with complete data
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        
        params = {
            "state": state if state else "all",
            "sort": "updated",
            "direction": "desc",
        }
        
        max_pages = (limit // 100 + 1) if limit else 100
        
        print(f"      📥 Fetching PRs (state={params['state']})...")
        
        try:
            all_prs = await self._paginate_all(url, params, max_pages)
        except Exception as e:
            print(f"      ⚠️  Error fetching PRs: {e}")
            return []
        
        print(f"      ✓ Found {len(all_prs)} PRs")
        
        if limit:
            all_prs = all_prs[:limit]
        
        if not all_prs:
            print(f"      ℹ️  No PRs found")
            return []
        
        print(f"   Enriching {len(all_prs)} PRs with reviews, comments, and files...")
        
        # Enrich PRs concurrently
        enrich_tasks = [self._enrich_pr_with_details(owner, repo, pr) for pr in all_prs]
        
        try:
            enriched_prs = await async_tqdm.gather(*enrich_tasks, desc="Enriching PRs")
        except Exception as e:
            print(f"      ⚠️  Error enriching some PRs: {e}")
            enriched_prs = all_prs
        
        return enriched_prs

    async def _fetch_single_pr(self, owner: str, repo: str, pr_number: int) -> Dict:
        """Fetch the specific single PR object for authoritative metadata"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        return await self._make_request(url) or {}

    async def _enrich_pr_with_details(self, owner: str, repo: str, pr: Dict) -> Dict:
        pr_number = pr.get("number")
        if not pr_number:
            return pr
        
        try:
            # Fetch the authoritative SINGLE PR object
            single_pr_task = self._fetch_single_pr(owner, repo, pr_number)
            
            # Fetch related data
            reviews_task = self._fetch_pr_reviews(owner, repo, pr_number)
            review_comments_task = self._fetch_pr_review_comments(owner, repo, pr_number)
            files_task = self._fetch_pr_files(owner, repo, pr_number)
            commits_task = self._fetch_pr_commits(owner, repo, pr_number)
            
            # Gather all
            single_pr_data, reviews, review_comments, files, pr_commits = await asyncio.gather(
                single_pr_task,
                reviews_task,
                review_comments_task,
                files_task,
                commits_task,
                return_exceptions=True,
            )
            
            # Safely handle results
            single_pr_data = single_pr_data if isinstance(single_pr_data, dict) else {}
            reviews = reviews if isinstance(reviews, list) else []
            review_comments = review_comments if isinstance(review_comments, list) else []
            files = files if isinstance(files, list) else []
            pr_commits = pr_commits if isinstance(pr_commits, list) else []
            
            # Merge data
            enriched_pr = {**pr, **single_pr_data}
            
            # Attach lists
            enriched_pr["review_comments"] = reviews
            enriched_pr["line_comments"] = review_comments
            enriched_pr["changed_files"] = files
            enriched_pr["pr_commits"] = pr_commits
            
            single_count = single_pr_data.get("changed_files", 0)
            list_count = len(files)
            
            enriched_pr["changed_files_count"] = max(single_count, list_count)
            enriched_pr["commits_count"] = single_pr_data.get("commits", len(pr_commits))
            
            # Ensure is_merged is accurate
            enriched_pr["is_merged"] = single_pr_data.get("merged", False)
            if not enriched_pr["is_merged"] and enriched_pr.get("merged_at"):
                enriched_pr["is_merged"] = True
            
            enriched_pr["linked_issues"] = self._extract_linked_issues(enriched_pr.get("body", ""))
            
            return enriched_pr
        
        except Exception as e:
            logger.error(f"Error enriching PR #{pr_number}: {e}")
            return pr

    async def _fetch_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Fetch PR changed files"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        
        try:
            files = await self._paginate_all(url, max_pages=10)
            
            if not files:
                logger.debug(f"PR #{pr_number}: No files returned")
                return []
            
            formatted_files = []
            for f in files:
                if not isinstance(f, dict):
                    continue
                
                file_data = {
                    "filename": f.get("filename"),
                    "status": f.get("status"),
                    "additions": f.get("additions", 0),
                    "deletions": f.get("deletions", 0),
                    "changes": f.get("changes", 0),
                    "patch": f.get("patch", ""),
                    "raw_url": f.get("raw_url"),
                }
                
                if file_data["filename"]:
                    formatted_files.append(file_data)
            
            return formatted_files
        
        except Exception as e:
            logger.error(f"Error fetching files for PR #{pr_number}: {e}")
            return []

    async def _fetch_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Fetch PR reviews"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        try:
            reviews = await self._paginate_all(url, max_pages=3)
            return [
                {
                    "id": r.get("id"),
                    "user": {"login": r.get("user", {}).get("login")},
                    "body": r.get("body", ""),
                    "state": r.get("state"),
                    "submitted_at": r.get("submitted_at"),
                }
                for r in reviews
            ]
        except Exception as e:
            logger.error(f"Error fetching reviews for PR #{pr_number}: {e}")
            return []

    async def _fetch_pr_review_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Fetch line-by-line review comments"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        try:
            comments = await self._paginate_all(url, max_pages=5)
            return [
                {
                    "id": c.get("id"),
                    "user": {"login": c.get("user", {}).get("login")},
                    "body": c.get("body", ""),
                    "path": c.get("path"),
                    "line": c.get("line"),
                    "created_at": c.get("created_at"),
                }
                for c in comments
            ]
        except Exception as e:
            logger.error(f"Error fetching review comments for PR #{pr_number}: {e}")
            return []

    async def _fetch_pr_commits(self, owner: str, repo: str, pr_number: int) -> List[str]:
        """Fetch PR commit SHAs"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        try:
            commits = await self._paginate_all(url, max_pages=3)
            return [c.get("sha") for c in commits if c.get("sha")]
        except Exception as e:
            logger.error(f"Error fetching commits for PR #{pr_number}: {e}")
            return []

    def _extract_linked_issues(self, text: str) -> List[int]:
        """Extract linked issue numbers from text"""
        if not text:
            return []
        
        patterns = [
            r"(?:fix|fixes|fixed|close|closes|closed|resolve|resolves|resolved)\s+#(\d+)",
            r"#(\d+)",
        ]
        
        linked_issues = set()
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    linked_issues.add(int(match))
                except ValueError:
                    continue
        
        return sorted(list(linked_issues))

    # ============================================
    # Commits Methods
    # ============================================

    async def fetch_commits_batch(self, owner: str, repo: str, limit: int = None) -> List[Dict]:
        """Fetch commits (lightweight)"""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        
        max_pages = (limit // 100 + 1) if limit else 5
        
        commits = await self._paginate_all(url, max_pages=max_pages)
        
        if limit:
            commits = commits[:limit]
        
        return [
            {
                "sha": c.get("sha"),
                "message": c.get("commit", {}).get("message", ""),
                "author": {
                    "name": c.get("commit", {}).get("author", {}).get("name"),
                    "email": c.get("commit", {}).get("author", {}).get("email"),
                },
                "date": c.get("commit", {}).get("author", {}).get("date"),
            }
            for c in commits
        ]

    # ============================================
    # Other Repository Methods
    # ============================================

    async def get_contributors_activity(self, owner: str, repo: str) -> List[Dict]:
        """Fetch contributor stats"""
        url = f"{self.base_url}/repos/{owner}/{repo}/stats/contributors"
        return await self._make_request(url) or []

    async def get_branches(self, owner: str, repo: str) -> List[Dict]:
        """Fetch branches"""
        url = f"{self.base_url}/repos/{owner}/{repo}/branches"
        return await self._paginate_all(url, max_pages=3)

    async def fetch_unified_activity(
        self, owner: str, repo: str, limit: int = 100
    ) -> List[Dict]:
        """Fetch unified activity (commits, issues, PRs) concurrently"""
        
        commits_task = self.fetch_commits_batch(owner, repo, limit=limit)
        issues_task = self.fetch_issues_batch(owner, repo, state="all", limit=limit)
        prs_task = self.fetch_prs_batch(owner, repo, state="all", limit=limit)
        
        commits, issues, prs = await asyncio.gather(commits_task, issues_task, prs_task)
        
        events = []
        events.extend([{"type": "commit", "payload": c} for c in commits])
        events.extend([{"type": "issue", "payload": i} for i in issues])
        events.extend([{"type": "pr", "payload": p} for p in prs])
        
        return events
