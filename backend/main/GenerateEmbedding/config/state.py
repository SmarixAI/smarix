import json
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parents[3] / "data/Admin/state/runtime_state.json"

def load_current_repo_from_state():
    if not STATE_FILE.exists():
        raise RuntimeError(f"State file not found: {STATE_FILE}")

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    curr_repo = state.get("curr_repo") or {}
    owner = curr_repo.get("owner")
    name = curr_repo.get("name")

    if not owner or not name:
        raise RuntimeError("curr_repo.owner or curr_repo.name missing")

    return owner, name
