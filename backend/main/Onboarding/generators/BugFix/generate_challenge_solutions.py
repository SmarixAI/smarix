"""
PR Challenge Solution Generator
Fetches real PR file diffs & code changes for onboarding challenges
"""

import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime
from github import Github
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Ensure backend/ is on PYTHONPATH
# ------------------------------------------------------------------
BACKEND_ROOT = Path(__file__).resolve().parents[4]  # backend/
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from utils.repo_context import get_repo_context

# ------------------------------------------------------------------
# Bootstrap
# ------------------------------------------------------------------
load_dotenv()

ctx = get_repo_context()

REPO_OWNER = ctx["owner"]
REPO_NAME = ctx["repo"]
ONBOARDING_ROOT = ctx["onboarding"]

REPO_FULL_NAME = f"{REPO_OWNER}/{REPO_NAME}"

BUGFIX_DIR = ONBOARDING_ROOT / "bugfix"
INPUT_JSON = BUGFIX_DIR / "onboarding_coding_questions.json"
OUTPUT_JSON = BUGFIX_DIR / "onboarding_challenge_solution.json"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def load_pr_numbers(json_file: Path) -> list[int]:
    """
    Extract PR numbers from LLM raw responses.
    Supports:
      - PR #14
      - PR Number: #14
      - Pull Request 14
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        pr_numbers: list[int] = []

        for q in data.get("questions", []):
            raw = q.get("raw_response", "")

            matches = re.findall(
                r"(?:PR Number|Pull Request|PR)\s*#?\s*(\d+)",
                raw,
                re.IGNORECASE,
            )

            if not matches:
                print("⚠️  No PR found in response preview:")
                print(raw[:200])

            pr_numbers.extend(int(m) for m in matches)

        pr_numbers = sorted(set(pr_numbers))
        print(f"Extracted {len(pr_numbers)} PRs → {pr_numbers}")
        return pr_numbers

    except Exception as e:
        print(f"❌ Failed to extract PR numbers: {e}")
        return []


def fetch_pr_file_changes(repo_name: str, pr_number: int, gh: Github) -> dict:
    try:
        print(f"\n{'=' * 60}")
        print(f"Fetching PR #{pr_number}")
        print(f"{'=' * 60}")

        repo = gh.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        files_data = []

        for f in pr.get_files():
            entry = {
                "file_path": f.filename,
                "change_type": f.status,
                "diff": f.patch or "",
                "before_code": "",
                "after_code": "",
                "statistics": {
                    "lines_added": f.additions,
                    "lines_deleted": f.deletions,
                    "total_changes": f.changes,
                },
            }

            try:
                if f.status in ("modified", "renamed"):
                    entry["after_code"] = repo.get_contents(
                        f.filename, ref=pr.head.sha
                    ).decoded_content.decode("utf-8")

                    try:
                        entry["before_code"] = repo.get_contents(
                            f.filename, ref=pr.base.sha
                        ).decoded_content.decode("utf-8")
                    except Exception:
                        pass

                elif f.status == "added":
                    entry["after_code"] = repo.get_contents(
                        f.filename, ref=pr.head.sha
                    ).decoded_content.decode("utf-8")

                elif f.status == "removed":
                    entry["before_code"] = repo.get_contents(
                        f.filename, ref=pr.base.sha
                    ).decoded_content.decode("utf-8")

            except Exception as e:
                print(f"⚠️  Could not fetch code for {f.filename}: {e}")

            files_data.append(entry)
            print(f"  {f.filename} ({f.status})")

        return {
            "pr_number": pr_number,
            "title": pr.title,
            "files": files_data,
        }

    except Exception as e:
        print(f"❌ PR #{pr_number} failed: {e}")
        return {
            "pr_number": pr_number,
            "error": str(e),
            "files": [],
        }


def create_output(prs: list[dict]) -> dict:
    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "repo": REPO_FULL_NAME,
            "total_prs": len(prs),
            "generator": "challenge-solution-v2",
        },
        "pull_requests": [p for p in prs if "error" not in p],
    }


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def generate_challenge_solutions() -> Path:

    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_JSON}")

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN not set in environment")

    pr_numbers = load_pr_numbers(INPUT_JSON)
    if not pr_numbers:
        raise RuntimeError("No PR numbers found in coding questions")

    gh = Github(github_token)
    print(f"\nGitHub client ready for {REPO_FULL_NAME}")

    results = []
    for pr in pr_numbers:
        results.append(fetch_pr_file_changes(REPO_FULL_NAME, pr, gh))

    output = create_output(results)

    BUGFIX_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ PR challenge solutions saved to:")
    print(f"   {OUTPUT_JSON}")

    return OUTPUT_JSON


if __name__ == "__main__":
    generate_challenge_solutions()
