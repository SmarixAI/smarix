"""
Private Repository State Manager
Manages private_runtime_state.json for GitHub App integration
Stores only ONE connected account (simpler than installations.json)
"""

import logging
import time
from typing import Optional, Dict, List
from utils.s3 import s3_manager

logger = logging.getLogger(__name__)

PRIVATE_STATE_S3_KEY = "Admin/state/private_runtime_state.json"


class PrivateRepoStateManager:
    """
    Manages the single connected GitHub account for private repos
    
    Storage: s3://bucket/Admin/state/private_runtime_state.json
    """

    def _ensure_file_exists(self) -> bool:
        """
        Ensure the state file exists in S3
        Creates an empty state file if it doesn't exist
        
        Returns:
            True if file exists or was created successfully
        """
        try:
            # Check if file exists
            if s3_manager.key_exists(PRIVATE_STATE_S3_KEY):
                print(f"✅ State file exists in S3")
                return True
            
            # File doesn't exist - create empty state
            print(f"⚠️ State file not found in S3")
            print(f"📝 Creating empty state file: {PRIVATE_STATE_S3_KEY}")
            
            empty_state = {
                "owner": None,
                "installation_id": None,
                "account_type": None,
                "repositories": [],
                "connected_at": None,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            s3_manager.upload_json(empty_state, PRIVATE_STATE_S3_KEY, public_read=False)
            print(f"✅ Created empty state file successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to ensure file exists: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _load_state(self) -> Optional[Dict]:
        """
        Load private repo state from S3
        
        Returns:
            Dict with structure: {
                "owner": str,
                "installation_id": int,
                "account_type": str,
                "repositories": List[Dict],
                "connected_at": str,
                "updated_at": str
            }
            or None if not found/invalid
        """
        try:
            print(f"🔍 Loading state from S3: {PRIVATE_STATE_S3_KEY}")
            print(f"   Bucket: {s3_manager.bucket}")
            
            # ✅ Ensure file exists first (creates if missing)
            if not self._ensure_file_exists():
                print(f"❌ Cannot ensure file exists")
                return None
            
            # Now download the file (it's guaranteed to exist)
            data = s3_manager.download_json(PRIVATE_STATE_S3_KEY)
            
            print(f"📥 Downloaded data type: {type(data)}")
            print(f"📥 Downloaded data: {data}")
            
            # Check if this is a valid connected state (has owner)
            if isinstance(data, dict) and data.get("owner"):
                print(f"✅ Valid state found - Owner: {data.get('owner')}")
                logger.info(f"✅ Loaded private repo state from S3")
                return data
            else:
                print(f"⚠️ File exists but no account connected (empty state)")
                logger.info(f"⚠️ Empty state file (no account connected)")
                return None
                
        except Exception as e:
            print(f"❌ Exception loading state: {e}")
            import traceback
            traceback.print_exc()
            logger.warning(f"Failed to load private repo state: {e}")
            return None

    def _save_state(self, state: Dict) -> bool:
        """Save private repo state to S3"""
        try:
            print(f"💾 Saving state to S3: {PRIVATE_STATE_S3_KEY}")
            print(f"   Owner: {state.get('owner')}")
            print(f"   Repos: {len(state.get('repositories', []))}")
            
            s3_manager.upload_json(state, PRIVATE_STATE_S3_KEY, public_read=False)
            
            print(f"✅ State saved successfully")
            logger.info(f"✅ Saved private repo state to S3: {PRIVATE_STATE_S3_KEY}")
            return True
        except Exception as e:
            print(f"❌ Failed to save state: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"❌ Failed to save private repo state to S3: {e}")
            return False

    def get_state(self) -> Optional[Dict]:
        """
        Get current private repo state
        
        Returns:
            Current state dict or None if no account connected
        """
        print("=" * 60)
        print("🔍 PrivateRepoStateManager.get_state() called")
        result = self._load_state()
        print(f"🔍 get_state() returning: {result}")
        print("=" * 60)
        return result

    def set_state(
        self,
        owner: str,
        installation_id: int,
        account_type: str,
        repositories: List[Dict]
    ) -> bool:
        """
        Set/Update the entire private repo state
        
        Args:
            owner: GitHub username or org name
            installation_id: GitHub installation ID
            account_type: 'User' or 'Organization'
            repositories: List of repo dicts
        
        Returns:
            True if saved successfully
        """
        try:
            print(f"📝 Setting state for: {owner}")
            print(f"   Installation ID: {installation_id}")
            print(f"   Account Type: {account_type}")
            print(f"   Repositories: {len(repositories)}")
            
            # Load existing state to preserve connected_at
            existing_state = self._load_state()
            
            # If existing state has same owner, preserve connected_at
            if existing_state and existing_state.get('owner') == owner:
                connected_at = existing_state.get("connected_at")
                print(f"   Preserving connected_at: {connected_at}")
            else:
                connected_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                print(f"   New connection, setting connected_at: {connected_at}")

            state = {
                "owner": owner,
                "installation_id": installation_id,
                "account_type": account_type,
                "repositories": repositories,
                "connected_at": connected_at,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }

            success = self._save_state(state)
            if success:
                logger.info(f"✅ Set private repo state for {owner}: {len(repositories)} repos")
            return success

        except Exception as e:
            print(f"❌ Failed to set private repo state: {e}")
            logger.error(f"❌ Failed to set private repo state: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_repositories(self, repositories: List[Dict]) -> bool:
        """
        Update only the repositories list (keeps owner and installation_id)
        
        Args:
            repositories: List of repo dicts
        
        Returns:
            True if updated successfully
        """
        try:
            state = self._load_state()
            if not state:
                print(f"❌ No existing state to update")
                logger.error("❌ No existing state to update")
                return False

            state["repositories"] = repositories
            state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            success = self._save_state(state)
            if success:
                logger.info(f"✅ Updated repositories: {len(repositories)} repos")
            return success

        except Exception as e:
            print(f"❌ Failed to update repositories: {e}")
            logger.error(f"❌ Failed to update repositories: {e}")
            import traceback
            traceback.print_exc()
            return False

    def clear_state(self) -> bool:
        """
        Clear/disconnect the current account
        Creates an empty state file (doesn't delete the file)
        
        Returns:
            True if cleared successfully
        """
        try:
            print(f"🗑️ Clearing private repo state...")
            
            # Create empty state instead of deleting
            empty_state = {
                "owner": None,
                "installation_id": None,
                "account_type": None,
                "repositories": [],
                "connected_at": None,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            
            s3_manager.upload_json(empty_state, PRIVATE_STATE_S3_KEY, public_read=False)
            
            print(f"✅ Cleared private repo state (created empty state)")
            logger.info(f"✅ Cleared private repo state")
            return True
        except Exception as e:
            print(f"❌ Failed to clear private repo state: {e}")
            logger.error(f"❌ Failed to clear private repo state: {e}")
            return False

    def get_owner(self) -> Optional[str]:
        """Get the currently connected owner"""
        state = self._load_state()
        return state.get("owner") if state else None

    def get_installation_id(self) -> Optional[int]:
        """Get the installation ID for the connected account"""
        state = self._load_state()
        return state.get("installation_id") if state else None

    def get_repositories(self) -> List[Dict]:
        """Get the list of repositories"""
        state = self._load_state()
        return state.get("repositories", []) if state else []


# Global instance
private_repo_state = PrivateRepoStateManager()
