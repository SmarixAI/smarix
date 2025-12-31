import sys
import json
import os
import argparse
from pathlib import Path
from datetime import datetime
from github import Github
from dotenv import load_dotenv

repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

load_dotenv()


def load_pr_numbers(json_file_path: str) -> list[int]:
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        pr_numbers = []
        import re
        for question in data.get('questions', []):
            raw_response = question.get('raw_response', '')
            matches = re.findall(r'(?:Issue|PR)\s*#(\d+)', raw_response)
            if matches:
                pr_numbers.extend([int(num) for num in matches])

        pr_numbers = sorted(list(set(pr_numbers)))
        print(f"Extracted {len(pr_numbers)} unique PR numbers: {pr_numbers}")
        return pr_numbers

    except Exception as e:
        print(f"Error loading PR numbers: {e}")
        return []


def fetch_pr_file_changes(repo_name: str, pr_number: int, github_client: Github) -> dict:
    try:
        print(f"\n{'='*60}")
        print(f"Fetching PR #{pr_number}")
        print(f"{'='*60}")

        repo = github_client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        print(f"  Title: {pr.title}")

        files = pr.get_files()
        file_changes = []

        print(f"  Processing {files.totalCount} files...")

        for file in files:
            file_data = {
                "file_path": file.filename,
                "change_type": file.status,
                "diff": file.patch or "",
                "before_code": "",
                "after_code": "",
                "statistics": {
                    "lines_added": file.additions,
                    "lines_deleted": file.deletions,
                    "total_changes": file.changes
                }
            }

            try:
                if file.status in ['modified', 'renamed']:
                    after = repo.get_contents(file.filename, ref=pr.head.sha)
                    file_data["after_code"] = after.decoded_content.decode('utf-8')

                    try:
                        before = repo.get_contents(file.filename, ref=pr.base.sha)
                        file_data["before_code"] = before.decoded_content.decode('utf-8')
                    except:
                        file_data["before_code"] = ""

                elif file.status == 'added':
                    after = repo.get_contents(file.filename, ref=pr.head.sha)
                    file_data["after_code"] = after.decoded_content.decode('utf-8')
                    file_data["before_code"] = ""

                elif file.status == 'removed':
                    before = repo.get_contents(file.filename, ref=pr.base.sha)
                    file_data["before_code"] = before.decoded_content.decode('utf-8')
                    file_data["after_code"] = ""

            except Exception as e:
                print(f"    Warning: Could not fetch content for {file.filename}: {e}")

            file_changes.append(file_data)
            print(f"    {file.filename} ({file.status})")

        print(f"  Fetched {len(file_changes)} files")

        return {
            "pr_number": pr_number,
            "file_changes": file_changes
        }

    except Exception as e:
        print(f"  Error: {e}")
        return {
            "pr_number": pr_number,
            "error": str(e),
            "file_changes": []
        }


def create_output_json(pr_data_list: list[dict]) -> dict:
    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_prs": len(pr_data_list),
            "format_version": "1.0"
        },
        "pull_requests": [
            {
                "pr_number": pr["pr_number"],
                "file_changes": pr["file_changes"]
            }
            for pr in pr_data_list if "error" not in pr
        ]
    }


def save_json(data: dict, output_path: str) -> bool:
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\nSaved to: {output_file}")
        print(f"   Size: {output_file.stat().st_size:,} bytes")
        return True

    except Exception as e:
        print(f"\nSave error: {e}")
        return False


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Fetch PR file changes from GitHub and structure for chatbot consumption",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python %(prog)s --repo CCExtractor/ccextractor
  python %(prog)s --repo owner/repo --input /path/to/questions.json --output /path/to/solutions.json
  python %(prog)s --repo owner/repo --token ghp_xxxxxxxxxxxxx
        """
    )

    parser.add_argument(
        '-r', '--repo',
        required=True,
        help='GitHub repository in format "owner/repo" (e.g., CCExtractor/ccextractor)'
    )

    parser.add_argument(
        '-i', '--input',
        default=None,
        help='Path to input JSON file (default: data/Onboarding/onboarding_bugfix_data/onboarding_coding_questions.json)'
    )

    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Path to output JSON file (default: data/Onboarding/onboarding_bugfix_data/onboarding_challenge_solution.json)'
    )

    parser.add_argument(
        '-t', '--token',
        default=None,
        help='GitHub personal access token (default: reads from GITHUB_TOKEN env variable)'
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    print("=" * 60)
    print("PR Challenge Solution Fetcher".center(60))
    print("=" * 60 + "\n")

    script_dir = Path(__file__).resolve().parent

    current = script_dir
    # Use new location: backend/data/Onboarding/onboarding_bugfix_data
    repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    base_dir = repo_root / "data" / "Onboarding" / "onboarding_bugfix_data"
    base_dir.mkdir(parents=True, exist_ok=True)

    input_json = args.input if args.input else base_dir / "onboarding_coding_questions.json"
    output_json = args.output if args.output else base_dir / "onboarding_challenge_solution.json"
    
    # Ensure we're saving to the correct category folder (not parent folder)
    assert "onboarding_bugfix_data" in str(output_json), f"Error: Output path should include 'onboarding_bugfix_data' but got: {output_json}"
    print(f"📁 Input file: {input_json}")
    print(f"📁 Output file: {output_json}")
    print(f"   Category folder: onboarding_bugfix_data")

    if not Path(input_json).exists():
        print(f"Input file not found: {input_json}")
        print(f"   Please specify correct path using --input flag")
        return

    github_token = args.token if args.token else os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("GitHub token not provided")
        print("   Use --token flag or set GITHUB_TOKEN in .env file")
        return

    print(f"Config:")
    print(f"  Repo: {args.repo}")
    print(f"  Input: {input_json}")
    print(f"  Output: {output_json}\n")

    pr_numbers = load_pr_numbers(str(input_json))
    if not pr_numbers:
        print("No PR numbers found")
        return

    try:
        github_client = Github(github_token)
        print("GitHub client initialized\n")
    except Exception as e:
        print(f"GitHub init failed: {e}")
        return

    print(f"Fetching {len(pr_numbers)} PRs...")
    all_pr_data = []
    for pr_num in pr_numbers:
        pr_data = fetch_pr_file_changes(args.repo, pr_num, github_client)
        all_pr_data.append(pr_data)

    output_data = create_output_json(all_pr_data)

    success = save_json(output_data, str(output_json))

    print("\n" + "=" * 60)
    print("SUMMARY".center(60))
    print("=" * 60)
    print(f"PRs Processed: {len(pr_numbers)}")
    print(f"Status: {'SUCCESS' if success else 'FAILED'}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
