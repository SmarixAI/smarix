import requests
import time
from typing import Any, Dict, List, Optional
from config.DataCollection.settings import Config
from utils.DataCollection.rate_limiter import RateLimiter
from tqdm import tqdm


class GitHubClient:
    """Handles GitHub API interactions with robust retry and pagination."""

    def __init__(self):
        self.config = Config()
        self.rate_limiter = RateLimiter()
        self.headers = self._build_headers()

    def _build_headers(self) -> Dict[str, str]:
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.config.GITHUB_TOKEN:
            headers['Authorization'] = f'token {self.config.GITHUB_TOKEN}'
        return headers

    def test_connection(self) -> bool:
        url = f"{self.config.GITHUB_API_BASE_URL}/rate_limit"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                core_limit = data['resources']['core']
                print(f"✅ GitHub API connected")
                print(f"📊 Rate limit: {core_limit['remaining']}/{core_limit['limit']}")
                print(f"🔄 Reset time: {time.ctime(core_limit['reset'])}")
                return True
            else:
                print(f"❌ GitHub API connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def get_repository_metadata(self, owner: str, repo: str) -> Dict:
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}"
        response = self._make_request_with_retry(url)
        if response and response.status_code == 200:
            data = response.json()
            return {
                'name': data.get('name'),
                'description': data.get('description'),
                'language': data.get('language'),
                'topics': data.get('topics', []),
                'stars': data.get('stargazers_count'),
                'forks': data.get('forks_count'),
                'size': data.get('size'),
                'created_at': data.get('created_at'),
                'updated_at': data.get('updated_at'),
                'default_branch': data.get('default_branch')
            }
        return {}

    def get_repository_contents(self, owner: str, repo: str, path: str = "") -> List[Dict]:
        """Return directory listing for a path. If 404, return empty list."""
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        response = self._make_request_with_retry(url)
        if response and response.status_code == 200:
            return response.json()
        return []

    def get_file_content(self, download_url: str) -> str:
        """Download raw file content given a raw download URL."""
        try:
            response = requests.get(download_url, timeout=15)
            if response.status_code == 200:
                response.encoding = response.apparent_encoding or 'utf-8'
                return response.text
        except Exception as e:
            print(f"❌ Error downloading file: {e}")
        return ""

    def _make_request(self, url: str, params: dict = None) -> Optional[requests.Response]:
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            return response
        except Exception as e:
            print(f"❌ Request error: {e}")
            return None

    def _make_request_with_retry(self, url: str, params: dict = None, max_retries: int = 3) -> Optional[
        requests.Response]:
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                remaining = int(
                    response.headers.get('X-RateLimit-Remaining', 0)) if response and response.headers else 0

                if response.status_code == 200:
                    if remaining and remaining < 10:
                        print(f"⚠️ Rate limit running low ({remaining} remaining). Pausing...")
                        self.rate_limiter.handle_rate_limit(response)
                    return response

                elif response.status_code == 403:
                    # Rate limit or forbidden
                    print(f"⏳ Rate limit / forbidden ({response.status_code}). Attempting backoff...")
                    self.rate_limiter.handle_rate_limit(response)
                    time.sleep(2 ** attempt)
                    continue

                elif response.status_code == 404:
                    return response

                else:
                    print(f"⚠️ Request failed with status {response.status_code}. Retrying...")
                    time.sleep(2 ** attempt)
            except Exception as e:
                print(f"❌ Request error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
        return None

    def _paginate(self, url: str, params: dict = None):
        params = params.copy() if params else {}
        per_page = getattr(self.config, 'PER_PAGE', 100)
        max_pages = getattr(self.config, 'MAX_PAGES', 10)
        params['per_page'] = per_page
        page = 1
        while page <= max_pages:
            params['page'] = page
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                if response.status_code == 403:
                    self.rate_limiter.handle_rate_limit(response)
                    response = requests.get(url, headers=self.headers, params=params, timeout=15)
                if response.status_code != 200:
                    break
                data = response.json()
                if not data:
                    break
                for item in data:
                    yield item
                if len(data) < per_page:
                    break
                page += 1
            except Exception as e:
                print(f"❌ Pagination request error: {e}")
                break

    def fetch_issues(self, owner: str, repo: str, state: str = 'all', limit: int = None):
        """Fetch ALL issues with complete information"""
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/issues"
        count = 0
        max_limit = limit or getattr(self.config, 'MAX_ISSUES', None)
        with tqdm(desc="Fetching issues", unit="issue") as pbar:
            for item in self._paginate(url, {'state': state}):
                if item.get('pull_request'):
                    continue
                yield item
                count += 1
                pbar.update(1)
                if max_limit and count >= max_limit:
                    break
                time.sleep(0.05)

    def fetch_prs(self, owner: str, repo: str, state: str = 'all', limit: int = None):
        """Fetch ALL pull requests with complete information"""
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls"
        count = 0
        max_limit = limit or getattr(self.config, 'MAX_PRS', None)
        with tqdm(desc="Fetching pull requests", unit="PR") as pbar:
            for item in self._paginate(url, {'state': state}):
                yield item
                count += 1
                pbar.update(1)
                if max_limit and count >= max_limit:
                    break
                time.sleep(0.05)

    def fetch_commits(self, owner: str, repo: str, limit: int = None):
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/commits"
        count = 0
        max_limit = limit or getattr(self.config, 'MAX_COMMITS', None)
        with tqdm(desc="Fetching commits", unit="commit") as pbar:
            for item in self._paginate(url):
                yield item
                count += 1
                pbar.update(1)
                if max_limit and count >= max_limit:
                    break
                time.sleep(0.05)

    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict]:
        """
        Fetch ALL comments for a specific issue with COMPLETE information.

        Returns list of comments with:
        - id: comment ID
        - user: username and profile URL
        - body: complete comment text
        - created_at, updated_at: timestamps
        - html_url: link to comment
        """
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        all_comments = []

        try:
            comment_count = 0
            for comment in self._paginate(url):
                comment_data = {
                    'id': comment.get('id'),
                    'user': {
                        'login': comment.get('user', {}).get('login'),
                        'html_url': comment.get('user', {}).get('html_url'),
                        'avatar_url': comment.get('user', {}).get('avatar_url')
                    },
                    'body': comment.get('body', ''),
                    'created_at': comment.get('created_at'),
                    'updated_at': comment.get('updated_at'),
                    'html_url': comment.get('html_url'),
                    'reactions': comment.get('reactions', {})
                }
                all_comments.append(comment_data)
                comment_count += 1

            if comment_count > 0:
                print(f"      ✓ Fetched {comment_count} comment(s)")

        except Exception as e:
            print(f"❌ Error fetching comments for issue #{issue_number}: {e}")

        return all_comments

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Fetch ALL changed files in a PR with COMPLETE information.

        Returns list of files with:
        - filename: file path
        - status: added, modified, removed, renamed
        - additions, deletions, changes: line counts
        - patch: git diff
        - raw_url: URL to download full file content
        """
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        all_files = []

        try:
            file_count = 0
            for file_data in self._paginate(url):
                all_files.append({
                    'filename': file_data.get('filename'),
                    'status': file_data.get('status'),
                    'additions': file_data.get('additions', 0),
                    'deletions': file_data.get('deletions', 0),
                    'changes': file_data.get('changes', 0),
                    'patch': file_data.get('patch', ''),
                    'raw_url': file_data.get('raw_url'),
                    'blob_url': file_data.get('blob_url'),
                    'contents_url': file_data.get('contents_url')
                })
                file_count += 1

            if file_count > 0:
                print(f"      ✓ Fetched {file_count} changed file(s)")

        except Exception as e:
            print(f"❌ Error fetching files for PR #{pr_number}: {e}")

        return all_files

    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Fetch ALL review comments (general PR reviews) with COMPLETE information.

        Returns list of reviews with:
        - id: review ID
        - user: reviewer info
        - body: review comment text
        - state: APPROVED, CHANGES_REQUESTED, COMMENTED, etc.
        - submitted_at: timestamp
        """
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        all_reviews = []

        try:
            review_count = 0
            for review in self._paginate(url):
                review_data = {
                    'id': review.get('id'),
                    'user': {
                        'login': review.get('user', {}).get('login'),
                        'html_url': review.get('user', {}).get('html_url'),
                        'avatar_url': review.get('user', {}).get('avatar_url')
                    },
                    'body': review.get('body', ''),
                    'state': review.get('state'),  # APPROVED, CHANGES_REQUESTED, COMMENTED, etc.
                    'submitted_at': review.get('submitted_at'),
                    'html_url': review.get('html_url'),
                    'commit_id': review.get('commit_id')
                }
                all_reviews.append(review_data)
                review_count += 1

            if review_count > 0:
                print(f"      ✓ Fetched {review_count} review(s)")

        except Exception as e:
            print(f"❌ Error fetching reviews for PR #{pr_number}: {e}")

        return all_reviews

    def get_pr_review_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """
        Fetch ALL line-by-line review comments with COMPLETE information.

        Returns list of line-level comments with:
        - id: comment ID
        - user: commenter info
        - body: comment text
        - path: file being commented on
        - line, position: location in diff
        - created_at, updated_at: timestamps
        """
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        all_comments = []

        try:
            comment_count = 0
            for comment in self._paginate(url):
                comment_data = {
                    'id': comment.get('id'),
                    'user': {
                        'login': comment.get('user', {}).get('login'),
                        'html_url': comment.get('user', {}).get('html_url'),
                        'avatar_url': comment.get('user', {}).get('avatar_url')
                    },
                    'body': comment.get('body', ''),
                    'path': comment.get('path'),
                    'position': comment.get('position'),
                    'line': comment.get('line'),
                    'start_line': comment.get('start_line'),
                    'original_position': comment.get('original_position'),
                    'diff_hunk': comment.get('diff_hunk', ''),
                    'created_at': comment.get('created_at'),
                    'updated_at': comment.get('updated_at'),
                    'html_url': comment.get('html_url'),
                    'commit_id': comment.get('commit_id'),
                    'original_commit_id': comment.get('original_commit_id'),
                    'in_reply_to_id': comment.get('in_reply_to_id'),
                    'reactions': comment.get('reactions', {})
                }
                all_comments.append(comment_data)
                comment_count += 1

            if comment_count > 0:
                print(f"      ✓ Fetched {comment_count} line-by-line comment(s)")

        except Exception as e:
            print(f"❌ Error fetching review comments for PR #{pr_number}: {e}")

        return all_comments

    def get_pr_commits(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """Fetch all commits for a PR"""
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
        response = self._make_request_with_retry(url)
        if response and response.status_code == 200:
            return response.json()
        return []

    def get_commit_files(self, owner: str, repo: str, commit_sha: str) -> List[Dict]:
        """Fetch files changed in a commit"""
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/commits/{commit_sha}"
        response = self._make_request_with_retry(url)
        if response and response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            if files:
                print(f"📄 Found {len(files)} files in commit {commit_sha[:7]}")
            return files
        return []

    def get_contributors_activity(self, owner: str, repo: str) -> List[Dict]:
        """Fetch contributor activity stats"""
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/stats/contributors"
        response = self._make_request_with_retry(url)
        if response and response.status_code == 200:
            return response.json()
        return []

    def get_branches(self, owner: str, repo: str) -> List[Dict]:
        """Fetch all branches"""
        url = f"{self.config.GITHUB_API_BASE_URL}/repos/{owner}/{repo}/branches"
        response = self._make_request_with_retry(url)
        if response and response.status_code == 200:
            return response.json()
        return []

    def fetch_unified_activity(self, owner: str, repo: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch unified activity events (commits, issues, PRs)"""
        events = []
        for c in self.fetch_commits(owner, repo, limit=limit):
            events.append({"type": "commit", "payload": c})
        for i in self.fetch_issues(owner, repo, limit=limit):
            events.append({"type": "issue", "payload": i})
        for p in self.fetch_prs(owner, repo, limit=limit):
            events.append({"type": "pr", "payload": p})
        return events