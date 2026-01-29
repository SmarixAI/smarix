from dotenv import load_dotenv

load_dotenv()

from backend.utils.s3 import s3_manager

S3_BUCKET = "smarix-data-apsouth1"
S3_REGION = "ap-south-1"
STATE_S3_KEY = "Admin/state/runtime_state.json"


def load_current_repo_from_state():
    """Load repository info from S3 state file"""
    try:
        state = s3_manager.download_json(STATE_S3_KEY)
    except Exception as e:
        raise RuntimeError(f"❌ State file not found in S3 key {STATE_S3_KEY}: {e}")

    curr_repo = state.get("curr_repo")
    if not curr_repo:
        raise RuntimeError("❌ curr_repo missing in runtime_state.json")

    owner = curr_repo.get("owner")
    name = curr_repo.get("name")

    if not owner or not name:
        raise RuntimeError("❌ curr_repo.owner or curr_repo.name missing")

    return owner, name


# Module-level constants for convenience
try:
    REPO_OWNER, REPO_NAME = load_current_repo_from_state()
except RuntimeError as e:
    # If state file is not available, set to None
    # This allows the module to be imported even if state is not yet initialized
    print(f"⚠️  Warning: {e}")
    REPO_OWNER = None
    REPO_NAME = None
