import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure core path is accessible
repo_root = Path(__file__).resolve().parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

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

def get_users_file_path() -> Path:
    possible_paths = [
        repo_root / "data" / "Admin" / "users.json",
        Path("data/Admin/users.json"),
        Path("../../data/Admin/users.json"),
    ]
    for path in possible_paths:
        if path.exists(): return path
    return repo_root / "data" / "Admin" / "users.json"


def get_runtime_state_file_path() -> Path:
    possible_paths = [
        repo_root / "data" / "Admin" / "state" / "runtime_state.json",
        Path("data/Admin/state/runtime_state.json"),
        Path("../../data/Admin/state/runtime_state.json"),
        Path("backend/data/Admin/state/runtime_state.json"),
    ]
    for path in possible_paths:
        if path.exists(): return path
    return repo_root / "data" / "Admin" / "state" / "runtime_state.json"


def get_user_repo(username: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    Get the repository (owner/name) for a user.
    Priority order:
    1. User's active_repos from users.json (if username provided)
    2. curr_repo from runtime_state.json (for new setups)
    3. user_default_repo from runtime_state.json (final fallback)
    Returns dict with 'owner' and 'name' keys, or None if not found.
    """
    # Priority 1: Try to get from user's active_repos (if username provided)
    if username:
        try:
            users_file = get_users_file_path()
            if users_file.exists():
                with open(users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users = data.get("users", [])
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
                                    f"⚠ Warning: Invalid repo format in active_repos for user {username}: '{repo_str}' (expected 'owner/repo')")
        except Exception as e:
            print(f"⚠ Warning: Could not read user's active_repos: {e}")

    # Priority 2 & 3: Fallback to runtime_state.json (curr_repo first, then user_default_repo)
    try:
        state_file = get_runtime_state_file_path()
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

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
        print(f"⚠ Warning: Could not read runtime_state.json: {e}")

    return None


def get_database_path_for_repo(owner: str, repo_name: str) -> Optional[str]:
    """Get the database path for a given owner/repo."""
    possible_db_dirs = [
        repo_root / "data" / "VectorDB" / owner / repo_name,
        Path("data/VectorDB") / owner / repo_name,
        Path("backend/data/VectorDB") / owner / repo_name,
        Path("../../data/VectorDB") / owner / repo_name,
    ]

    for db_dir in possible_db_dirs:
        # We check if the directory exists and has at least one index folder inside (e.g., 'all')
        if db_dir.exists() and (db_dir / "all" / "faiss.index").exists():
            return str(db_dir)
    return None


def ensure_chatbot_for_repo(owner: str, repo_name: str) -> bool:
    """
    Ensure the chatbot is initialized with the correct repository database.
    Returns True if successful, False otherwise.
    """
    # These must refer to the module-level variables defined at the top of this file
    global chatbot_instance, chatbot_config, available_providers

    # Get the database path for this repo
    db_path = get_database_path_for_repo(owner, repo_name)

    if not db_path:
        print(f"⚠ Warning: Database not found for repo {owner}/{repo_name}")
        return False

    # Check if chatbot is already using this database
    current_db_path = chatbot_config.get("github_db_path")
    if current_db_path == db_path:
        # Already using the correct database
        return True

    # Need to reinitialize with the new database
    try:
        print(f"Switching chatbot to repo: {owner}/{repo_name}")

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
        }

        print(f"✅ Chatbot switched to {owner}/{repo_name}")
        return True

    except Exception as e:
        print(f"⚠ Error switching chatbot to {owner}/{repo_name}: {e}")
        import traceback
        traceback.print_exc()
        return False