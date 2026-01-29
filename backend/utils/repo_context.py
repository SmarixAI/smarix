import json
from pathlib import Path
from utils.s3 import s3_manager

# S3 Configuration
S3_BUCKET = "smarix-data"
STATE_S3_KEY = "Admin/state/runtime_state.json"


def get_runtime_state_from_s3():
    """Get the runtime state from S3"""
    try:
        return s3_manager.download_json(STATE_S3_KEY)
    except Exception as e:
        raise RuntimeError(f"Failed to load runtime_state.json from S3: {e}")


def get_repo_context():
    """
    Get repository context from S3 state file.
    Returns paths for both local temp storage and S3 locations.
    """
    state = get_runtime_state_from_s3()
    
    curr = state.get("curr_repo")
    if not curr:
        raise RuntimeError("curr_repo missing in runtime_state.json")
    
    owner = curr["owner"]
    repo = curr["name"]
    
    # S3 paths for vector database and onboarding data
    s3_vector_db = f"s3://{S3_BUCKET}/VectorDB/{owner}/{repo}"
    s3_onboarding = f"s3://{S3_BUCKET}/Onboarding/{owner}/{repo}"
    
    return {
        "owner": owner,
        "repo": repo,
        "vector_db": s3_vector_db,  # S3 path for vector database
        "onboarding": s3_onboarding,  # S3 path for onboarding data
        "s3_vector_db_prefix": f"VectorDB/{owner}/{repo}/",  # S3 prefix without bucket
        "s3_onboarding_prefix": f"Onboarding/{owner}/{repo}/",  # S3 prefix without bucket
    }