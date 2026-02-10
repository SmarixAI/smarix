"""
Direct issue lookup by exact issue number match.
Enables fast retrieval of specific issues without vector search.
"""
import json
import logging
from typing import Optional, Dict, Any, List
import boto3
from botocore.exceptions import ClientError


class IssueDirectLookup:
    """Direct lookup for issue chunks by issue number."""

    S3_BUCKET = "smarix-data-apsouth1"

    def __init__(self, org_name: str, repo_name: str, issue_chunks_path: str = None):
        """
        Initialize issue direct lookup.

        Args:
            org_name: GitHub organization/owner name
            repo_name: GitHub repository name
            issue_chunks_path: S3 key for issue_chunks.json file. If None, uses default based on org/repo.
        """
        self.logger = logging.getLogger(__name__)
        self.org_name = org_name
        self.repo_name = repo_name
        self.issue_chunks_path = issue_chunks_path
        self.issue_map = {}  # Map of issue number -> issue chunk data
        self.loaded = False

        # Load from S3
        if self.issue_chunks_path:
            self._load_from_s3(self.issue_chunks_path)
        else:
            self._load_from_s3_default()

    def _load_from_s3_default(self):
        """Load issue chunks from S3 default location based on org/repo."""
        default_key = f"DataProcessing/{self.org_name}/{self.repo_name}/chunks/issue_chunks.json"
        self._load_from_s3(default_key)

    def _load_from_s3(self, s3_key: str):
        """Load issue chunks from S3."""
        try:
            s3_client = boto3.client('s3')

            self.logger.info(f"Loading issue chunks from S3: s3://{self.S3_BUCKET}/{s3_key}")

            response = s3_client.get_object(Bucket=self.S3_BUCKET, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            chunks = json.loads(content)

            # Index all issue chunks by issue number
            for chunk in chunks:
                if chunk.get('type') == 'issue':
                    issue_number = chunk.get('entities', {}).get('issue_number')
                    if issue_number is not None:
                        self.issue_map[int(issue_number)] = chunk

            self.loaded = True
            self.issue_chunks_path = f"s3://{self.S3_BUCKET}/{s3_key}"
            self.logger.info(f"✅ Loaded {len(self.issue_map)} issue chunks for direct lookup from S3 ({self.org_name}/{self.repo_name})")

        except ClientError as e:
            self.logger.error(f"Failed to load issue chunks from S3 for {self.org_name}/{self.repo_name}: {e}")
            self.loaded = False
        except Exception as e:
            self.logger.error(f"Unexpected error loading from S3 for {self.org_name}/{self.repo_name}: {e}")
            self.loaded = False

    def lookup_by_number(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """
        Look up an issue by its exact number.

        Args:
            issue_number: The issue number to look up

        Returns:
            Issue chunk data if found, None otherwise
        """
        if not self.loaded:
            return None

        return self.issue_map.get(int(issue_number))

    def lookup_by_number_str(self, issue_number_str: str) -> Optional[Dict[str, Any]]:
        """
        Look up an issue by number given as string.
        Handles formats like "563", "#563", "issue#563", etc.

        Args:
            issue_number_str: Issue number as string (can include # prefix)

        Returns:
            Issue chunk data if found, None otherwise
        """
        if not self.loaded:
            return None

        try:
            # Extract just the number part
            clean_number = ''.join(filter(str.isdigit, issue_number_str))
            if clean_number:
                issue_number = int(clean_number)
                return self.lookup_by_number(issue_number)
        except (ValueError, TypeError):
            pass

        return None

    def extract_issue_number_from_query(self, query: str) -> Optional[int]:
        """
        Extract issue number from query text.
        Looks for patterns like "issue 563", "issue#563", "#563", "bug 563", etc.

        Args:
            query: The query text

        Returns:
            Issue number if found, None otherwise
        """
        import re

        # Patterns to match: "issue 563", "issue#563", "#563", "bug 563", etc.
        patterns = [
            r'(?:issue|bug|ticket|problem)\s*#?(\d+)',  # "issue 563" or "issue#563"
            r'#(\d+)',  # "#563"
            r'issue(\d+)',  # "issue563"
        ]

        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                try:
                    issue_number = int(match.group(1))
                    self.logger.debug(f"ISSUE_LOOKUP | Extracted issue #{issue_number} from query using pattern: {pattern}")
                    return issue_number
                except (ValueError, IndexError):
                    pass

        self.logger.debug(f"ISSUE_LOOKUP | No issue number pattern matched in query")
        return None

    def check_and_retrieve(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Check if query contains an issue number reference and retrieve it if found.
        This is the main entry point for integration with the chatbot.

        Args:
            query: The user query

        Returns:
            Issue chunk data if an issue was found and loaded, None otherwise
        """
        if not self.loaded:
            self.logger.debug("ISSUE_LOOKUP | check_and_retrieve: Issue lookup not loaded, returning None")
            return None

        issue_number = self.extract_issue_number_from_query(query)

        if issue_number is not None:
            self.logger.debug(f"ISSUE_LOOKUP | check_and_retrieve: Extracted issue #{issue_number} from query: '{query[:80]}'")
            issue_data = self.lookup_by_number(issue_number)
            if issue_data:
                self.logger.info(f"✅ ISSUE_LOOKUP | check_and_retrieve: Found issue #{issue_number} in {self.org_name}/{self.repo_name}")
                return issue_data
            else:
                self.logger.info(f"⚠️ ISSUE_LOOKUP | check_and_retrieve: Issue #{issue_number} not found in {self.org_name}/{self.repo_name}")
        else:
            self.logger.debug(f"ISSUE_LOOKUP | check_and_retrieve: No issue number extracted from query: '{query[:80]}'")

        return None

    def get_available_issue_numbers(self) -> List[int]:
        """Get list of all available issue numbers for validation."""
        if not self.loaded:
            return []
        return sorted(self.issue_map.keys())

    def is_loaded(self) -> bool:
        """Check if issue chunks are loaded."""
        return self.loaded


def get_issue_lookup(org_name: str, repo_name: str, issue_chunks_path: str = None) -> IssueDirectLookup:
    """
    Get an issue lookup instance for the specified repository.
    Note: This is NOT a singleton - each org/repo combination gets its own instance.

    Args:
        org_name: GitHub organization/owner name
        repo_name: GitHub repository name
        issue_chunks_path: Optional S3 key to issue chunks JSON.

    Returns:
        IssueDirectLookup instance
    """
    return IssueDirectLookup(org_name, repo_name, issue_chunks_path)
