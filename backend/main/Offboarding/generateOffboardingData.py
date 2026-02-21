"""
Offboarding data generation: runs for a single user only.
The user is derived from the GitHub repo data (top contributor); paths are
configured in generate_knowledge_transfer_tasks.py (GITHUB_REPO_JSON_PATH, OFFBOARDING_OUTPUT_DIR).
"""

import sys
from pathlib import Path

# Ensure we can import from sibling module
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from generate_knowledge_transfer_tasks import run_single_user_offboarding


def main():
    success = run_single_user_offboarding()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
