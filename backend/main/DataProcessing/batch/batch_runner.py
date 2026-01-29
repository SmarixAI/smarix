from collections import Counter
from ..pipeline.file_processor import process_file
from ..chunking.base_chunker import DataChunker
from ..state.repo_state import load_current_repo_from_state

import json

# Import S3Manager
from backend.utils.s3 import s3_manager

REPO_OWNER, REPO_NAME = load_current_repo_from_state()

# S3 config
S3_BUCKET = "smarix-data"


def batch_process():
    """
    Batch process with Git-first → Gmail correlation strategy
    Only processes files for the current repo specified in runtime_state.json
    Reads from S3, writes to S3 (no local data/ directory)
    """
    # S3 paths
    git_s3_key = f"DataCollectionFromGit/{REPO_OWNER}/{REPO_NAME}/{REPO_NAME}.json"
    gmail_s3_key = "DataCollectionFromGmail/gmail_data.json"

    # Display current repo being processed
    print(f"\n{'=' * 70}")
    print(f"PROCESSING DATA FOR CURRENT REPO: {REPO_OWNER}/{REPO_NAME}")
    print(f"{'=' * 70}\n")

    # Initialize shared chunker
    chunker = DataChunker(REPO_NAME, REPO_OWNER)

    # Load Git data from S3
    git_data = None
    print(f"📂 Looking for Git data in S3: s3://{S3_BUCKET}/{git_s3_key}")

    if s3_manager.key_exists(git_s3_key):
        git_data = s3_manager.download_json(git_s3_key)
        print(
            f"✅ Found and loaded Git file for current repo: {REPO_OWNER}/{REPO_NAME}"
        )
    else:
        print(f"⚠️  No Git file found for current repo: {REPO_OWNER}/{REPO_NAME}")
        print(f"   Expected S3 key: {git_s3_key}")

    # Load Gmail data from S3
    gmail_data = None
    if s3_manager.key_exists(gmail_s3_key):
        gmail_data = s3_manager.download_json(gmail_s3_key)
        print(f"📧 Found and loaded Gmail file: {gmail_s3_key}")
    else:
        print(f"⚠️  No Gmail file found in S3")

    if not git_data and not gmail_data:
        print(f"❌ No JSON files found in S3")
        return

    print(
        f"\n📦 Total files to process: {(1 if git_data else 0) + (1 if gmail_data else 0)}"
    )
    print(
        f"   Strategy: Git first → Code analysis → Extract entities → Gmail with correlation\n"
    )

    results = []
    all_git_entities = {}
    all_tech_stacks = {}

    # Phase 1: Process Git data first
    if git_data:
        print(f"\n{'=' * 70}")
        print("PHASE 1: Processing GitHub Data with Code Analysis")
        print(f"{'=' * 70}\n")

        try:
            result = process_file(
                git_data,  # Pass dict directly
                chunker,
            )
            results.append((git_s3_key, "Success", result))

            # Collect entities
            if result.get("entities"):
                all_git_entities[result["repo_name"]] = result["entities"]

            # Collect tech stacks
            if result.get("tech_stack"):
                all_tech_stacks[result["repo_name"]] = result["tech_stack"]

        except Exception as e:
            print(f"❌ Failed {git_s3_key}: {e}")
            import traceback

            traceback.print_exc()
            results.append((git_s3_key, "Failed", str(e)))

    # Phase 2: Process Gmail data with Git correlation
    if gmail_data:
        print(f"\n{'=' * 70}")
        print("PHASE 2: Processing Gmail Data (with GitHub correlation)")
        print(f"{'=' * 70}\n")

        # Merge all Git entities for comprehensive correlation
        merged_entities = {
            "authors": set(),
            "issue_numbers": set(),
            "pr_numbers": set(),
            "commit_shas": set(),
            "file_paths": set(),
            "branches": set(),
            "labels": set(),
            "emails": set(),
            "keywords": set(),
        }

        for entities in all_git_entities.values():
            for key, values in entities.items():
                if key in merged_entities:
                    merged_entities[key].update(values)

        print(f"   📊 Merged GitHub entities:")
        for key, values in merged_entities.items():
            print(f"      • {key}: {len(values)}")
        print()

        try:
            result = process_file(
                gmail_data,  # Pass dict directly
                chunker,
                merged_entities,
            )

            results.append((gmail_s3_key, "Success", result))
        except Exception as e:
            print(f"❌ Failed {gmail_s3_key}: {e}")
            import traceback

            traceback.print_exc()
            results.append((gmail_s3_key, "Failed", str(e)))

    # Summary
    print(f"\n{'=' * 70}")
    print("BATCH PROCESSING SUMMARY")
    print(f"{'=' * 70}\n")

    successful = [r for r in results if r[1] == "Success"]
    failed = [r for r in results if r[1] == "Failed"]

    print(f"✅ Success: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")

    if successful:
        total_chunks = sum(r[2]["chunk_count"] for r in successful)
        total_processed = sum(r[2]["processed_count"] for r in successful)
        total_raw = sum(r[2]["raw_count"] for r in successful)

        print(f"\n📊 Statistics:")
        print(f"   Total chunks: {total_chunks}")
        print(f"   Processed chunks: {total_processed}")
        print(f"   Raw data references: {total_raw}")

        # Entity statistics
        print(f"\n   GitHub entities extracted:")
        for key in [
            "authors",
            "issue_numbers",
            "pr_numbers",
            "commit_shas",
            "file_paths",
        ]:
            total = sum(
                len(r[2].get("entities", {}).get(key, []))
                for r in successful
                if r[2].get("entities")
            )
            if total > 0:
                print(f"      • {key}: {total}")

        # Tech stack summary
        if all_tech_stacks:
            print(f"\n   Tech Stack Summary:")
            all_languages = Counter()
            all_frameworks = Counter()
            all_tools = Counter()
            total_code_lines = 0
            total_functions = 0
            total_classes = 0

            for tech_stack in all_tech_stacks.values():
                for lang, count in tech_stack["languages"]["all"].items():
                    all_languages[lang] += count
                for fw in tech_stack["frameworks"]["detected"]:
                    all_frameworks[fw] += 1
                for tool in tech_stack["tools"]["detected"]:
                    all_tools[tool] += 1
                total_code_lines += tech_stack["metrics"]["total_code_lines"]
                total_functions += tech_stack["functions_and_classes"][
                    "total_functions"
                ]
                total_classes += tech_stack["functions_and_classes"]["total_classes"]

            print(f"      • Total code lines: {total_code_lines:,}")
            print(f"      • Total functions: {total_functions:,}")
            print(f"      • Total classes: {total_classes:,}")
            print(f"      • Languages detected: {len(all_languages)}")
            print(
                f"        Top 5: {', '.join([f'{l}({c})' for l, c in all_languages.most_common(5)])}"
            )
            print(f"      • Frameworks detected: {len(all_frameworks)}")
            print(f"        {', '.join(all_frameworks.keys())}")
            print(f"      • Tools detected: {len(all_tools)}")
            print(f"        {', '.join(all_tools.keys())}")

    if failed:
        print(f"\n❌ Failed files:")
        for name, _, error in failed:
            print(f"   • {name}: {error}")

    # Save aggregated tech stack summary to S3
    if all_tech_stacks:
        aggregated_s3_key = "DataProcessing/aggregated_tech_stack_summary.json"

        aggregated_data = {
            "repositories": all_tech_stacks,
            "summary": {
                "total_repositories": len(all_tech_stacks),
                "languages": dict(all_languages),
                "frameworks": dict(all_frameworks),
                "tools": dict(all_tools),
                "total_code_lines": total_code_lines,
                "total_functions": total_functions,
                "total_classes": total_classes,
            },
        }

        s3_manager.upload_json(aggregated_data, aggregated_s3_key, public_read=False)
        print(
            f"\n💾 Aggregated tech stack summary saved -> s3://{S3_BUCKET}/{aggregated_s3_key}"
        )
