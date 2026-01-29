import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure core path is accessible
repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import S3 manager
from utils.s3 import s3_manager

# S3 Configuration
S3_BUCKET = "smarix-data-apsouth1"
S3_VECTORDB_PATH = "VectorDB"

# Import RAGChatbot class
try:
    from core.ChatBot.chatbot import RAGChatbot
except ImportError:
    # Fallback for different directory structures
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
    from core.ChatBot.chatbot import RAGChatbot

# ==================== GLOBAL SHARED STATE ====================
chatbot_instance: Optional[RAGChatbot] = None
chatbot_config: Dict[str, Any] = {}
available_providers: Dict[str, bool] = {}


# ==================== SHARED HELPER FUNCTIONS ====================

def get_users_file_from_s3() -> Optional[Dict]:
    """Load users.json from S3"""
    users_s3_key = "Admin/users.json"
    try:
        return s3_manager.download_json(users_s3_key)
    except Exception as e:
        print(f"⚠️  Warning: Could not read users.json from S3: {e}")
        return None


def get_runtime_state_from_s3() -> Optional[Dict]:
    """Load runtime_state.json from S3"""
    state_s3_key = "Admin/state/runtime_state.json"
    try:
        return s3_manager.download_json(state_s3_key)
    except Exception as e:
        print(f"⚠️  Warning: Could not read runtime_state.json from S3: {e}")
        return None


def get_user_repo(username: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Get the repository (owner/name) for a user.
    Priority order:
    1. User's active_repos from users.json in S3 (if username provided)
    2. curr_repo from runtime_state.json in S3 (for new setups)
    3. user_default_repo from runtime_state.json in S3 (final fallback)
    Returns dict with 'owner' and 'name' keys, or None if not found.
    """
    # Priority 1: Try to get from user's active_repos (if username provided)
    if username:
        try:
            users_data = get_users_file_from_s3()
            if users_data:
                users = users_data.get("users", [])
                user = next((u for u in users if u.get("username") == username), None)

                if user:
                    active_repos = user.get("active_repos", [])
                    if active_repos and len(active_repos) > 0:
                        # Use the first active repo
                        repo_str = active_repos[0]
                        # Parse "owner/repo" format
                        if "/" in repo_str:
                            parts = repo_str.split("/", 1)
                            if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                                owner, repo_name = parts[0].strip(), parts[1].strip()
                                return {"owner": owner, "name": repo_name}
                        else:
                            print(
                                f"⚠️  Warning: Invalid repo format in active_repos for user {username}: '{repo_str}' (expected 'owner/repo')")
        except Exception as e:
            print(f"⚠️  Warning: Could not read user's active_repos: {e}")

    # Priority 2 & 3: Fallback to runtime_state.json (curr_repo first, then user_default_repo)
    try:
        state = get_runtime_state_from_s3()
        if state:
            # Priority 2: Try curr_repo (for new setups)
            curr_repo = state.get("curr_repo", {})
            owner = curr_repo.get("owner")
            repo_name = curr_repo.get("name")

            if owner and repo_name:
                return {"owner": owner, "name": repo_name}

            # Priority 3: Fallback to user_default_repo (final fallback)
            user_default_repo = state.get("user_default_repo", {})
            owner = user_default_repo.get("owner")
            repo_name = user_default_repo.get("name")

            if owner and repo_name:
                return {"owner": owner, "name": repo_name}
    except Exception as e:
        print(f"⚠️  Warning: Could not read runtime_state.json: {e}")

    return None


def get_database_path_for_repo_s3(owner: str, repo_name: str) -> Optional[str]:
    """Get the S3 database path for a given owner/repo."""
    s3_vectordb_prefix = f"{S3_VECTORDB_PATH}/{owner}/{repo_name}/"
    
    try:
        # Check if the prefix exists and has expected structure
        response = s3_manager.s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=s3_vectordb_prefix,
            MaxKeys=10
        )
        
        if 'Contents' in response:
            # Check if it has expected index files (at least 'all' index)
            keys = [obj['Key'] for obj in response['Contents']]
            has_all_index = any("all/" in key and "faiss.index" in key for key in keys)
            
            if has_all_index:
                return f"s3://{S3_BUCKET}/{s3_vectordb_prefix}"
    except Exception as e:
        print(f"⚠️  Error checking S3 VectorDB for {owner}/{repo_name}: {e}")
    
    return None


def ensure_chatbot_for_repo(owner: str, repo_name: str) -> bool:
    """
    Ensure the chatbot is initialized with the correct repository database from S3.
    Returns True if successful, False otherwise.
    """
    # These must refer to the module-level variables defined at the top of this file
    global chatbot_instance, chatbot_config, available_providers

    # Get the S3 database path for this repo
    db_path = get_database_path_for_repo_s3(owner, repo_name)

    if not db_path:
        print(f"⚠️  Warning: Database not found in S3 for repo {owner}/{repo_name}")
        return False

    # Check if chatbot is already using this database
    current_db_path = chatbot_config.get("github_db_path")
    if current_db_path == db_path:
        # Already using the correct database
        print(f"✅ Chatbot already using {owner}/{repo_name}")
        return True

    # Need to reinitialize with the new database
    try:
        print(f"🔄 Switching chatbot to repo: {owner}/{repo_name}")
        print(f"   S3 Path: {db_path}")

        # Get gmail_db_path from current config
        gmail_db_path = chatbot_config.get("gmail_db_path")

        # Get provider from current config or default
        provider = chatbot_config.get("provider", "openai")

        # Check availability
        if available_providers and not available_providers.get(provider):
            # Try to find an available provider
            if available_providers.get("openai"):
                provider = "openai"
            elif available_providers.get("anthropic"):
                provider = "anthropic"
            else:
                # If we have no provider info yet (e.g. first run), we proceed hoping keys exist
                pass

        # Reinitialize chatbot
        chatbot_instance = RAGChatbot(
            vector_db_path=db_path,
            gmail_db_path=gmail_db_path,
            provider=provider,
            temperature=0.7,
            top_k=5,
            use_hybrid_retrieval=True,
            verbose=False,
            routing_method="llm",
            repo_owner=owner,
            repo_name=repo_name,
        )

        # Update config
        databases = []
        total_vectors = 0

        if chatbot_instance.multi_index_store:
            stats = chatbot_instance.multi_index_store.get_statistics()
            total_vectors = stats.get("total_vectors", 0)
            databases.append(
                f"Multi-Index ({total_vectors} vectors across {stats.get('total_indices', 0)} indices)"
            )
            for idx_type, idx_stats in stats.get("by_index", {}).items():
                if "total_vectors" in idx_stats:
                    databases.append(
                        f"  - {idx_type}: {idx_stats['total_vectors']} vectors"
                    )

        chatbot_config = {
            "github_db_path": db_path,
            "gmail_db_path": gmail_db_path,
            "provider": provider,
            "model": chatbot_instance.model,
            "total_vectors": total_vectors,
            "databases": databases,
            "status": "ready",
            "available_providers": available_providers,
            "storage_backend": "s3",
        }

        print(f"✅ Chatbot switched to {owner}/{repo_name}")
        print(f"   Total vectors: {total_vectors}")
        return True

    except Exception as e:
        print(f"❌ Error switching chatbot to {owner}/{repo_name}: {e}")
        import traceback
        traceback.print_exc()
        return False