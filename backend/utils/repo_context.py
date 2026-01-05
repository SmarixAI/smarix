import json
from pathlib import Path

def get_runtime_state_file_path() -> Path:
    """Get the path to the runtime state JSON file"""
    repo_root = Path(__file__).resolve().parent.parent
    possible_paths = [
        repo_root / "data" / "Admin" / "state" / "runtime_state.json",
        Path("data/Admin/state/runtime_state.json"),
        Path("../../data/Admin/state/runtime_state.json"),
        Path("backend/data/Admin/state/runtime_state.json"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Return default path if none exist
    return repo_root / "data" / "Admin" / "state" / "runtime_state.json"

STATE_FILE = get_runtime_state_file_path()

def get_repo_context():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    curr = state.get("curr_repo")
    if not curr:
        raise RuntimeError("curr_repo missing in runtime_state.json")

    owner = curr["owner"]
    repo = curr["name"]
    backend_root = Path(__file__).resolve().parents[1]   # backend/
    base = backend_root / "data"

    return {
        "owner": owner,
        "repo": repo,

        "vector_db": base / "VectorDB" / owner / repo,
        "onboarding": base / "Onboarding" / owner / repo,
    }
