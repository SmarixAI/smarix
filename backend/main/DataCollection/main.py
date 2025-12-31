"""
Enhanced Main Script
Uses EnhancedRepositoryProcessor for comprehensive data collection
Adds Gmail data collection integration and ensures Gmail is collected first.
"""

import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys
import json
import traceback

# Make sure backend root is on sys.path for local imports when executed directly
_backend_dir = Path(__file__).resolve().parents[2]
_backend_dir_str = str(_backend_dir)
if _backend_dir_str not in sys.path:
    sys.path.insert(0, _backend_dir_str)

from core.DataCollection.DataCollectionFromGithub.repository_processor import RepositoryProcessor

# Gmail imports
from core.DataCollection.DataCollectionFromGmail.gmail_client import build_gmail_service
from core.DataCollection.DataCollectionFromGmail.gmail_collector import GmailCollector
from core.DataCollection.DataCollectionFromGmail.user_consent import (
    load_credentials_if_exists,
    run_console_authorization,
)


def process_single_repo(owner, repo, team_id=None, channel_id=None):
    """Process a single repository with enhanced data collection"""
    processor = RepositoryProcessor()
    try:
        repo_data = processor.process_repository(owner, repo, team_id=team_id, channel_id=channel_id)
        output_file = processor.save_repository_data(repo_data, owner, repo)
        processor.print_summary(repo_data, owner, repo, output_file)
        return owner, repo, output_file, "Success", repo_data
    except Exception as e:
        print(f"\nError processing {owner}/{repo}: {str(e)}")
        traceback.print_exc()
        return owner, repo, str(e), "Failed", None


def process_gmail_collection(save_output: bool = True):
    """
    Collects Gmail messages and stores them under ../../data/DataCollectionFromGmail/gmail_data.json
    (Hardcoded path, same style used for GitHub data).
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
            output_dir = Path("../../data/DataCollectionFromGmail")
            output_dir.mkdir(parents=True, exist_ok=True)

            output_path = output_dir / "gmail_data.json"

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(gmail_data, f, indent=2, ensure_ascii=False)

            print(f"[GMAIL] Data saved → {output_path.resolve()}")

        except Exception as e:
            print(f"[GMAIL] Failed to save gmail data: {e}")
            traceback.print_exc()

    print("\n" + "="*70)
    print(" GMAIL DATA COLLECTION (END) ")
    print("="*70 + "\n")

    return gmail_data


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("ENHANCED REPOSITORY PROCESSOR - ONBOARDING/OFFBOARDING MVP")
    print("="*70 + "\n")

    test_repos = [
        ('CCExtractor', 'taskwarrior-flutter'),
    ]

    output_dir = Path("../../data/DataCollectionFromGit")
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir.absolute()}\n")

    base_processor = RepositoryProcessor()
    if not base_processor.test_connection():
        print("Cannot proceed without API access. Please check your GitHub token.")
        return

    # --- Step 1: Collect Gmail data first (no interactive prompt here; will run auth flow if needed) ---
    gmail_data = None
    try:
        # gmail_data = process_gmail_collection(save_output=True)
        if gmail_data is None:
            print("[MAIN] Gmail collection returned no data (skipped or failed). Continuing with GitHub collection.")
        else:
            print(f"[MAIN] Gmail collection complete. Total messages collected: {gmail_data.get('total_messages', 0)}")
    except Exception as e:
        print(f"[MAIN] Unexpected error during Gmail collection: {e}")
        traceback.print_exc()
        # continue to GitHub processing even if Gmail fails

    # --- Step 2: Process GitHub repositories ---
    max_workers = 1
    print(f"Processing mode: {'Sequential' if max_workers == 1 else f'Parallel ({max_workers} workers)'}\n")

    start_time = time.time()
    results = []

    if max_workers == 1:
        for owner, repo in test_repos:
            print(f"\n{'='*70}")
            print(f"Processing {owner}/{repo} ({test_repos.index((owner, repo)) + 1}/{len(test_repos)})")
            print(f"{'='*70}\n")
            result = process_single_repo(owner, repo, None, None)
            results.append(result)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_single_repo, owner, repo, None, None): (owner, repo)
                for owner, repo in test_repos
            }

            for future in as_completed(futures):
                owner, repo = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"\nError processing {owner}/{repo}: {e}")
                    results.append((owner, repo, str(e), "Failed", None))

    total_time = time.time() - start_time
    print("\n" + "="*70)
    print(" FINAL SUMMARY")
    print("="*70 + "\n")

    successful = [r for r in results if r[3] == "Success"]
    failed = [r for r in results if r[3] == "Failed"]

    print(f"Total Repositories: {len(test_repos)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Total Time: {total_time:.2f}s")

    if successful:
        print(f"\nSUCCESSFULLY PROCESSED:")
        for owner, repo, output, status, data in successful:
            print(f"   • {owner}/{repo}")
            print(f"     → Output: {output}")
            if data:
                # guard for missing keys
                stats = data.get('stats', {}) if isinstance(data, dict) else {}
                print(f"     → Onboarding data points: {stats.get('onboarding_data_points', 'N/A')}")
                print(f"     → Offboarding data points: {stats.get('offboarding_data_points', 'N/A')}")

    if failed:
        print(f"\nFAILED TO PROCESS:")
        for owner, repo, error, status, _ in failed:
            print(f"   • {owner}/{repo}")
            print(f"     → Error: {error}")

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

        print(f"   Total Onboarding Data Points: {total_onboarding}")
        print(f"   Total Offboarding Data Points: {total_offboarding}")
        print(f"   Total Code Files Analyzed: {total_files}")
        print(f"   Total Issues Collected: {total_issues}")
        print(f"   Total PRs Collected: {total_prs}")
        print(f"   Total Commits Collected: {total_commits}")

    # Optional: include a brief summary for Gmail results if available
    if gmail_data:
        print(f"\nGMAIL SUMMARY:")
        print(f"   Total messages fetched: {gmail_data.get('total_messages', 0)}")
        # sample top-level signals if any
        # e.g., number of messages with attachments
        try:
            messages = gmail_data.get("messages", []) or []
            with_attachments = sum(1 for m in messages if m.get("has_attachments"))
            print(f"   Messages with attachments: {with_attachments}")
        except Exception:
            pass

    if successful:
        print(f"\nKNOWLEDGE SIGNALS SUMMARY:")
        combined_signals = {"onboarding": 0, "offboarding": 0, "knowledge": 0}

        for _, _, _, _, data in successful:
            if data and "knowledge_summary" in data:
                ks = data.get("knowledge_summary", {})
                for key in combined_signals:
                    combined_signals[key] += ks.get(key, 0)

        for signal_type, count in combined_signals.items():
            print(f"   {signal_type.capitalize()} Signals: {count}")

    print("\n" + "="*70)
    print(" PIPELINE COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
