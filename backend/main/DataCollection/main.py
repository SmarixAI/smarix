"""
Enhanced Main Script - ASYNC VERSION
Uses AsyncRepositoryProcessor for 4-5x faster data collection
Time reduced: 45-60min → 12-15min
"""

from datetime import datetime
import time
import asyncio
import os
from pathlib import Path
import sys
import json
import traceback

from dotenv import load_dotenv 

load_dotenv()

_backend_dir = Path(__file__).resolve().parents[2]
_backend_dir_str = str(_backend_dir)
if _backend_dir_str not in sys.path:
    sys.path.insert(0, _backend_dir_str)

from core.DataCollection.DataCollectionFromGithub.repository_processor import AsyncRepositoryProcessor
from core.DataCollection.DataCollectionFromGithub.github_client import AsyncGitHubClient

from core.DataCollection.DataCollectionFromGmail.gmail_client import build_gmail_service
from core.DataCollection.DataCollectionFromGmail.gmail_collector import GmailCollector

from utils.s3 import s3_manager

S3_BUCKET = "smarix-data"
S3_REGION = "us-east-1"

STATE_S3_KEY = "Admin/state/runtime_state.json"

def load_current_repo_from_state():
    """Load repository info from S3 state file"""
    try:
        state = s3_manager.download_json(STATE_S3_KEY)
    except Exception as e:
        raise RuntimeError(f"State file not found in S3 key {STATE_S3_KEY}: {e}")

    curr_repo = state.get("curr_repo")
    if not curr_repo:
        raise RuntimeError("curr_repo not found in runtime_state.json")

    owner = curr_repo.get("owner")
    repo = curr_repo.get("name")

    if not owner or not repo:
        raise RuntimeError("curr_repo.owner or curr_repo.name missing")

    return owner, repo


def update_runtime_state(owner: str, name: str):
    """
    Updates the active repository in the S3 state file.
    Required for Data Processing, Embedding, and VectorDB steps to know which repo to target.
    """
    state_s3_key = "Admin/state/runtime_state.json"
    
    print(f"🔵 Updating S3 runtime state to: {owner}/{name}")
    
    try:
        try:
            state = s3_manager.download_json(state_s3_key)
            if not isinstance(state, dict):
                state = {}
        except Exception:
            state = {}

        state["curr_repo"] = {
            "owner": owner,
            "name": name,
            "updated_at": str(datetime.now())
        }
        
        s3_manager.upload_json(state, state_s3_key)
        print("✅ Runtime state updated successfully in S3")
        
        return {
            "success": True, 
            "message": f"State updated to {owner}/{name}"
        }

    except Exception as e:
        error_msg = f"Failed to update runtime state: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False, 
            "error": error_msg
        }

async def process_single_repo_async(owner, repo, team_id=None, channel_id=None):
    """Process a single repository asynchronously"""
    processor = AsyncRepositoryProcessor()
    
    # Test connection first
    async with AsyncGitHubClient() as github_client:
        connection_ok = await processor.test_connection(github_client)
        if not connection_ok:
            print("Cannot proceed without API access. Please check your GitHub token.")
            return owner, repo, "Connection failed", "Failed", None
    
    try:
        # Process repository
        repo_data = await processor.process_repository(owner, repo, team_id=team_id, channel_id=channel_id)
        output_file = processor.save_repository_data(repo_data, owner, repo)
        processor.print_summary(repo_data, owner, repo, output_file)
        return owner, repo, output_file, "Success", repo_data
    except Exception as e:
        print(f"\nError processing {owner}/{repo}: {str(e)}")
        traceback.print_exc()
        return owner, repo, str(e), "Failed", None


def process_gmail_collection(save_output: bool = True):
    """
    Collects Gmail messages and optionally saves to S3 (not local).
    """
    print("\n" + "="*70)
    print(" GMAIL DATA COLLECTION (START) ")
    print("="*70 + "\n")

    try:
        service = build_gmail_service()
    except Exception as e:
        print(f"[GMAIL] Failed to initialize Gmail service: {e}")
        traceback.print_exc()
        return None

    try:
        collector = GmailCollector(service=service)
        gmail_data = collector.collect_all_messages()
    except Exception as e:
        print(f"[GMAIL] Error while collecting messages: {e}")
        traceback.print_exc()
        return None

    if save_output and gmail_data:
        try:
            s3_key = "DataCollectionFromGmail/gmail_data.json"

            s3_manager.upload_json(gmail_data, s3_key, public_read=False)

            print(f"[GMAIL] Data saved → s3://{S3_BUCKET}/{s3_key}")
        except Exception as e:
            print(f"[GMAIL] Failed to save gmail data to S3: {e}")
            traceback.print_exc()

    print("\n" + "="*70)
    print(" GMAIL DATA COLLECTION (END) ")
    print("="*70 + "\n")

    return gmail_data

async def main_async():
    """Main async execution function"""
    print("\n" + "="*70)
    print("ASYNC REPOSITORY PROCESSOR")
    print("="*70 + "\n")

    # Load repo from runtime_state.json
    owner, repo = load_current_repo_from_state()
    test_repos = [(owner, repo)]

    # --- Step 1: Collect Gmail data first (optional) ---
    gmail_data = None
    try:
        # Uncomment to enable Gmail collection
        # gmail_data = process_gmail_collection(save_output=True)
        if gmail_data is None:
            print("[MAIN] Gmail collection skipped or returned no data.")
        else:
            print(f"[MAIN] Gmail collection complete. Total messages: {gmail_data.get('total_messages', 0)}")
    except Exception as e:
        print(f"[MAIN] Unexpected error during Gmail collection: {e}")
        traceback.print_exc()

    # --- Step 2: Process GitHub repositories (ASYNC) ---
    print(f"Processing mode: Async (Concurrent)\n")

    start_time = time.time()
    results = []

    # Process repositories (currently single repo, but supports multiple)
    for owner, repo in test_repos:
        print(f"\n{'='*70}")
        print(f"Processing {owner}/{repo}")
        print(f"{'='*70}\n")
        
        result = await process_single_repo_async(owner, repo, None, None)
        results.append(result)

    total_time = time.time() - start_time

    # --- Final Summary ---
    print("\n" + "="*70)
    print(" FINAL SUMMARY")
    print("="*70 + "\n")

    successful = [r for r in results if r[3] == "Success"]
    failed = [r for r in results if r[3] == "Failed"]

    print(f"Total Repositories: {len(test_repos)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Total Time: {total_time:.2f}s ({total_time/60:.1f} minutes)")
    
    if total_time < 900:  # 15 minutes
        print(f"✅ SUCCESS: Completed in under 15 minutes!")
    else:
        print(f"⚠️  WARNING: Took longer than 15 minutes target")

    if successful:
        print(f"\nSUCCESSFULLY PROCESSED:")
        for owner, repo, output, status, data in successful:
            print(f" • {owner}/{repo}")
            print(f"   → Output: {output}")
            if data:
                stats = data.get('stats', {}) if isinstance(data, dict) else {}
                print(f"   → Onboarding data points: {stats.get('onboarding_data_points', 'N/A')}")
                print(f"   → Offboarding data points: {stats.get('offboarding_data_points', 'N/A')}")

    if failed:
        print(f"\nFAILED TO PROCESS:")
        for owner, repo, error, status, _ in failed:
            print(f" • {owner}/{repo}")
            print(f"   → Error: {error}")

    if successful:
        print(f"\nAGGREGATE STATISTICS:")
        total_onboarding = sum(
            (data.get('stats', {}).get('onboarding_data_points', 0) if data else 0)
            for _, _, _, _, data in successful
        )
        total_offboarding = sum(
            (data.get('stats', {}).get('offboarding_data_points', 0) if data else 0)
            for _, _, _, _, data in successful
        )
        total_files = sum(
            (len(data.get('code_files', [])) if data else 0)
            for _, _, _, _, data in successful
        )
        total_issues = sum(
            (data.get('stats', {}).get('issues_count', 0) if data else 0)
            for _, _, _, _, data in successful
        )
        total_prs = sum(
            (data.get('stats', {}).get('prs_count', 0) if data else 0)
            for _, _, _, _, data in successful
        )
        total_commits = sum(
            (data.get('stats', {}).get('commits_count', 0) if data else 0)
            for _, _, _, _, data in successful
        )

        print(f" Total Onboarding Data Points: {total_onboarding}")
        print(f" Total Offboarding Data Points: {total_offboarding}")
        print(f" Total Code Files Analyzed: {total_files}")
        print(f" Total Issues Collected: {total_issues}")
        print(f" Total PRs Collected: {total_prs}")
        print(f" Total Commits Collected: {total_commits}")

    if gmail_data:
        print(f"\nGMAIL SUMMARY:")
        print(f" Total messages fetched: {gmail_data.get('total_messages', 0)}")

    if successful:
        print(f"\nKNOWLEDGE SIGNALS SUMMARY:")
        combined_signals = {"onboarding": 0, "offboarding": 0, "knowledge": 0}

        for _, _, _, _, data in successful:
            if data and "knowledge_summary" in data:
                ks = data.get("knowledge_summary", {})
                for key in combined_signals:
                    combined_signals[key] += ks.get(key, 0)

        for signal_type, count in combined_signals.items():
            print(f" {signal_type.capitalize()} Signals: {count}")


def main():
    """Entry point - runs async main"""
    try:
        # Run the async main function
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
