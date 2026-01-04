import json
from pathlib import Path

STATE_FILE = Path(
    "/Users/vishalkeshari/Desktop/smarix/backend/data/Admin/state/runtime_state.json"
)

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
