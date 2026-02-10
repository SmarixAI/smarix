"""
Direct PR lookup by exact PR number match.
Enables fast retrieval of specific PRs without vector search.
"""
import json
import logging
from typing import Optional, Dict, Any, List
import boto3
from botocore.exceptions import ClientError


class PRDirectLookup:
    """Direct lookup for PR chunks by PR number."""

    S3_BUCKET = "smarix-data-apsouth1"

    def __init__(self, org_name: str, repo_name: str, pr_chunks_path: str = None):
        """
        Initialize PR direct lookup.

        Args:
            org_name: GitHub organization/owner name
            repo_name: GitHub repository name
            pr_chunks_path: S3 key for pr_chunks.json file. If None, uses default based on org/repo.
        """
        self.logger = logging.getLogger(__name__)
        self.org_name = org_name
        self.repo_name = repo_name
        self.pr_chunks_path = pr_chunks_path
        self.pr_map = {}  # Map of PR number -> PR chunk data
        self.loaded = False

        # Load from S3
        if self.pr_chunks_path:
            self._load_from_s3(self.pr_chunks_path)
        else:
            self._load_from_s3_default()

    def _load_from_s3_default(self):
        """Load PR chunks from S3 default location based on org/repo."""
        default_key = f"DataProcessing/{self.org_name}/{self.repo_name}/chunks/pr_chunks.json"
        self._load_from_s3(default_key)

    def _load_from_s3(self, s3_key: str):
        """Load PR chunks from S3."""
        try:
            s3_client = boto3.client('s3')

            self.logger.info(f"Loading PR chunks from S3: s3://{self.S3_BUCKET}/{s3_key}")

            response = s3_client.get_object(Bucket=self.S3_BUCKET, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            chunks = json.loads(content)

            # Index all PR chunks by PR number
            for chunk in chunks:
                if chunk.get('type') == 'pr':
                    pr_number = chunk.get('entities', {}).get('pr_number')
                    if pr_number is not None:
                        self.pr_map[int(pr_number)] = chunk

            self.loaded = True
            self.pr_chunks_path = f"s3://{self.S3_BUCKET}/{s3_key}"
            self.logger.info(f"✅ Loaded {len(self.pr_map)} PR chunks for direct lookup from S3 ({self.org_name}/{self.repo_name})")

        except ClientError as e:
            self.logger.error(f"Failed to load PR chunks from S3 for {self.org_name}/{self.repo_name}: {e}")
            self.loaded = False
        except Exception as e:
            self.logger.error(f"Unexpected error loading from S3 for {self.org_name}/{self.repo_name}: {e}")
            self.loaded = False

    def lookup_by_number(self, pr_number: int) -> Optional[Dict[str, Any]]:
        """
        Look up a PR by its exact number.

        Args:
            pr_number: The PR number to look up

        Returns:
            PR chunk data if found, None otherwise
        """
        if not self.loaded:
            return None

        return self.pr_map.get(int(pr_number))

    def lookup_by_number_str(self, pr_number_str: str) -> Optional[Dict[str, Any]]:
        """
        Look up a PR by number given as string.
        Handles formats like "565", "#565", "PR#565", etc.

        Args:
            pr_number_str: PR number as string (can include # prefix)

        Returns:
            PR chunk data if found, None otherwise
        """
        if not self.loaded:
            return None

        try:
            # Extract just the number part
            clean_number = ''.join(filter(str.isdigit, pr_number_str))
            if clean_number:
                pr_number = int(clean_number)
                return self.lookup_by_number(pr_number)
        except (ValueError, TypeError):
            pass

        return None

    def extract_pr_number_from_query(self, query: str) -> Optional[int]:
        """
        Extract PR number from query text.
        Looks for patterns like "PR 565", "PR#565", "#565", "pull request 565", etc.

        Args:
            query: The query text

        Returns:
            PR number if found, None otherwise
        """
        import re

        # Patterns to match: "PR 565", "PR#565", "#565", "pull request 565", etc.
        patterns = [
            r'(?:PR|pull\s+request)\s*#?(\d+)',  # "PR 565" or "PR#565" or "pull request 565"
            r'#(\d+)',  # "#565"
            r'PR(\d+)',  # "PR565"
        ]

        query_lower = query.lower()
        for pattern in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                try:
                    pr_number = int(match.group(1))
                    self.logger.debug(f"PR_LOOKUP | Extracted PR #{pr_number} from query using pattern: {pattern}")
                    return pr_number
                except (ValueError, IndexError):
                    pass

        self.logger.debug(f"PR_LOOKUP | No PR number pattern matched in query")
        return None

    def check_and_retrieve(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Check if query contains a PR number reference and retrieve it if found.
        This is the main entry point for integration with the chatbot.

        Args:
            query: The user query

        Returns:
            PR chunk data if a PR was found and loaded, None otherwise
        """
        if not self.loaded:
            self.logger.debug("PR_LOOKUP | check_and_retrieve: PR lookup not loaded, returning None")
            return None

        pr_number = self.extract_pr_number_from_query(query)

        if pr_number is not None:
            self.logger.debug(f"PR_LOOKUP | check_and_retrieve: Extracted PR #{pr_number} from query: '{query[:80]}'")
            pr_data = self.lookup_by_number(pr_number)
            if pr_data:
                self.logger.info(f"✅ PR_LOOKUP | check_and_retrieve: Found PR #{pr_number} in {self.org_name}/{self.repo_name}")
                return pr_data
            else:
                self.logger.info(f"⚠️ PR_LOOKUP | check_and_retrieve: PR #{pr_number} not found in {self.org_name}/{self.repo_name}")
        else:
            self.logger.debug(f"PR_LOOKUP | check_and_retrieve: No PR number extracted from query: '{query[:80]}'")

        return None

    def get_available_pr_numbers(self) -> List[int]:
        """Get list of all available PR numbers for validation."""
        if not self.loaded:
            return []
        return sorted(self.pr_map.keys())

    def is_loaded(self) -> bool:
        """Check if PR chunks are loaded."""
        return self.loaded


def get_pr_lookup(org_name: str, repo_name: str, pr_chunks_path: str = None) -> PRDirectLookup:
    """
    Get a PR lookup instance for the specified repository.
    Note: This is NOT a singleton - each org/repo combination gets its own instance.

    Args:
        org_name: GitHub organization/owner name
        repo_name: GitHub repository name
        pr_chunks_path: Optional S3 key to PR chunks JSON.

    Returns:
        PRDirectLookup instance
    """
    return PRDirectLookup(org_name, repo_name, pr_chunks_path)
