"""
GitHub Installation Manager - S3 Version
Handles installation_id lookup using S3 storage (no database required)
"""

import asyncio
import aiohttp
import jwt
import time
import os
from typing import Optional, Dict, List
import logging

from utils.s3 import s3_manager

logger = logging.getLogger(__name__)

INSTALLATIONS_S3_KEY = "Admin/state/github_installations.json"


class GitHubInstallationManager:
    """
    Manages GitHub App installations using S3 storage

    Storage: s3://bucket/Admin/state/github_installations.json
    """

    def __init__(self):
        self.app_id = os.getenv("GITHUB_APP_ID")
        self.private_key = os.getenv("GITHUB_PRIVATE_KEY")

        if self.private_key:
            self.private_key = self.private_key.replace("\\n", "\n")

    def _generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication"""
        now = int(time.time())
        payload = {
            "iat": now,
            "exp": now + 600,  # 10 minutes
            "iss": self.app_id
        }
        return jwt.encode(payload, self.private_key, algorithm="RS256")

    def _load_installations_from_s3(self) -> Dict:
        """
        Load installations mapping from S3

        Returns:
            Dict with structure: {"installations": {"owner": {...}}}
        """
        try:
            data = s3_manager.download_json(INSTALLATIONS_S3_KEY)
            if not isinstance(data, dict):
                return {"installations": {}}
            return data
        except Exception as e:
            logger.warning(f"Installations file not found in S3, creating new: {e}")
            return {"installations": {}}

    def _save_installations_to_s3(self, data: Dict) -> None:
        """Save installations mapping to S3"""
        try:
            s3_manager.upload_json(data, INSTALLATIONS_S3_KEY, public_read=False)
            logger.info(f"Saved installations to S3: {INSTALLATIONS_S3_KEY}")
        except Exception as e:
            logger.error(f"Failed to save installations to S3: {e}")
            raise

    def get_installation_id_from_s3(self, owner: str) -> Optional[int]:
        """
        Get installation_id from S3 for a specific owner

        Args:
            owner: Repository owner (username or org name)

        Returns:
            installation_id or None if not found
        """
        data = self._load_installations_from_s3()
        installations = data.get("installations", {})

        if owner in installations:
            installation_info = installations[owner]
            installation_id = installation_info.get("installation_id")
            logger.info(f"Found installation_id {installation_id} for {owner} in S3")
            return installation_id

        logger.warning(f"No installation found for {owner} in S3")
        return None

    async def get_installation_id_from_api(self, owner: str, repo: str) -> Optional[int]:
        """
        Get installation_id by querying GitHub API

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            installation_id or None if app not installed
        """
        if not self.app_id or not self.private_key:
            raise ValueError("GitHub App credentials not configured")

        jwt_token = self._generate_jwt()
        url = f"https://api.github.com/repos/{owner}/{repo}/installation"

        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        installation_id = data["id"]
                        logger.info(f"Found installation_id {installation_id} for {owner}/{repo} via API")
                        return installation_id
                    elif response.status == 404:
                        logger.warning(f"GitHub App not installed on {owner}/{repo}")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Failed to query installation API: {e}")
            return None

    async def get_installation_id(self, owner: str, repo: str) -> int:
        """
        Get installation_id using best available method

        Tries:
        1. S3 lookup (fast)
        2. API lookup (fallback)
        3. Raises error if not found

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            installation_id

        Raises:
            ValueError if installation not found
        """
        # Try S3 first
        installation_id = self.get_installation_id_from_s3(owner)

        if installation_id:
            return installation_id

        # Fallback to API
        logger.info(f"S3 lookup failed for {owner}, querying GitHub API...")
        installation_id = await self.get_installation_id_from_api(owner, repo)

        if installation_id:
            # Auto-store in S3 for future use
            logger.info(f"Auto-storing installation {installation_id} for {owner} in S3")
            self.store_installation(
                owner=owner,
                installation_id=installation_id,
                account_type="Unknown",  # We don't know yet
                repositories=[]
            )
            return installation_id

        # Not found
        raise ValueError(
            f"GitHub App not installed on {owner}/{repo}. "
            f"Please install the app first: https://github.com/apps/YOUR_APP_NAME/installations/new"
        )

    def store_installation(
            self,
            owner: str,
            installation_id: int,
            account_type: str,
            repositories: List[Dict]
    ) -> bool:
        """
        Store installation in S3

        Args:
            owner: GitHub username or org name
            installation_id: GitHub installation ID
            account_type: 'User' or 'Organization'
            repositories: List of repo dicts

        Returns:
            True if stored successfully
        """
        try:
            data = self._load_installations_from_s3()

            # Update or add installation
            data["installations"][owner] = {
                "installation_id": installation_id,
                "account_type": account_type,
                "installed_at": data.get("installations", {}).get(owner, {}).get("installed_at",
                                                                                 time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                                               time.gmtime())
                                                                                 ),
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "repositories": repositories
            }

            self._save_installations_to_s3(data)
            logger.info(f"Stored installation {installation_id} for {owner}")
            return True

        except Exception as e:
            logger.error(f"Failed to store installation: {e}")
            return False

    def remove_installation(self, owner: str) -> bool:
        """
        Remove installation from S3

        Args:
            owner: GitHub username or org name

        Returns:
            True if removed successfully
        """
        try:
            data = self._load_installations_from_s3()

            if owner in data.get("installations", {}):
                del data["installations"][owner]
                self._save_installations_to_s3(data)
                logger.info(f"Removed installation for {owner}")
                return True
            else:
                logger.warning(f"No installation found for {owner} to remove")
                return False

        except Exception as e:
            logger.error(f"Failed to remove installation: {e}")
            return False

    def list_all_installations(self) -> Dict[str, Dict]:
        """
        Get all installations from S3

        Returns:
            Dict of all installations: {"owner": {...}}
        """
        data = self._load_installations_from_s3()
        return data.get("installations", {})

    def update_repositories(self, owner: str, repositories: List[Dict]) -> bool:
        """
        Update repository list for an installation

        Args:
            owner: GitHub username or org name
            repositories: List of repo dicts

        Returns:
            True if updated successfully
        """
        try:
            data = self._load_installations_from_s3()

            if owner not in data.get("installations", {}):
                logger.warning(f"No installation found for {owner}")
                return False

            data["installations"][owner]["repositories"] = repositories
            data["installations"][owner]["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            self._save_installations_to_s3(data)
            logger.info(f"Updated repositories for {owner}")
            return True

        except Exception as e:
            logger.error(f"Failed to update repositories: {e}")
            return False
