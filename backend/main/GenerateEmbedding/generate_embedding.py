"""
Enterprise-Grade Embedding Generation (Step 3) - OPTIMIZED
Optimized for GitHub-first → Gmail correlation with rich metadata
Supports hybrid embedding: content + entities + temporal context
WITH ASYNC S3 OPERATIONS FOR 3-5x SPEED IMPROVEMENT
"""

import sys
import json
import argparse
import os
import tempfile
import asyncio
import concurrent.futures
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from collections import defaultdict
from functools import lru_cache

# Add workspace root (parent of backend) to path BEFORE any imports to support both script and module execution
# This allows importing 'backend' as a module
_workspace_root = Path(__file__).resolve().parents[3]  # Go up to workspace root
_workspace_root_str = str(_workspace_root)
if _workspace_root_str not in sys.path:
    sys.path.insert(0, _workspace_root_str)

# Also add backend directory for core imports
_backend_dir = Path(__file__).resolve().parents[2]
_backend_dir_str = str(_backend_dir)
if _backend_dir_str not in sys.path:
    sys.path.insert(0, _backend_dir_str)

# Now import using absolute imports (works for both script and module)
from backend.main.GenerateEmbedding.analytics.graph_nodes import prepare_graph_nodes
from backend.main.GenerateEmbedding.utils.file_utils import get_size
from backend.main.GenerateEmbedding.loaders.source_detector import detect_source_type
from backend.main.GenerateEmbedding.config.state import load_current_repo_from_state
from backend.main.GenerateEmbedding.preparation.chunk_preparer import (
    prepare_chunks_for_embedding,
)
from backend.main.GenerateEmbedding.analytics.repo_metrics import compute_repo_metrics
from backend.main.GenerateEmbedding.analytics.cost_estimator import estimate_cost
from backend.main.GenerateEmbedding.config.provider import auto_detect_provider
from backend.main.GenerateEmbedding.loaders.tech_summary_loader import (
    inject_tech_summary,
)
from core.GenerateEmbedding.generator import EmbeddingGenerator
from backend.utils.repo_normalizer import (
    repo_matches,
    normalize_repo_name,
    normalize_repo_owner,
    extract_repo_parts,
)
from utils.s3 import s3_manager

load_dotenv()

# S3 Configuration
S3_BUCKET = "smarix-data-apsouth1"
S3_BASE_PATH = "DataProcessing"
S3_EMBEDDINGS_PATH = "Embeddings"

REPO_OWNER, REPO_NAME = load_current_repo_from_state()
FULL_REPO_NAME = f"{REPO_OWNER}/{REPO_NAME}"

print(f"\n{'='*70}")
print(f"GENERATING EMBEDDINGS FOR REPO: {REPO_OWNER}/{REPO_NAME} (OPTIMIZED)")
print(f"{'='*70}\n")


# Thread pool for parallel S3 operations
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)


def download_json_parallel(s3_key):
    """Download JSON from S3 in parallel"""
    try:
        return s3_key, s3_manager.download_json(s3_key), None
    except Exception as e:
        return s3_key, None, str(e)


def upload_to_s3_parallel(args):
    """Upload file to S3 in parallel"""
    file_path, s3_key = args
    try:
        with open(file_path, "rb") as f:
            s3_manager.s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=f.read())
        return s3_key, True, None
    except Exception as e:
        return s3_key, False, str(e)


def save_embeddings_to_s3_fast(generator, result, s3_key_prefix):
    """Save embeddings to S3 with parallel uploads"""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = os.path.join(tmpdir, "temp")
        generator.save_embeddings(result, temp_path)

        # Prepare upload tasks
        upload_tasks = [
            (f"{temp_path}.npy", f"{s3_key_prefix}.npy"),
        ]

        # Upload .npy in parallel
        futures = [
            executor.submit(upload_to_s3_parallel, task) for task in upload_tasks
        ]

        # Upload .json separately (text data)
        with open(f"{temp_path}.json", "r") as f:
            metadata = json.load(f)
            s3_manager.upload_json(metadata, f"{s3_key_prefix}.json")

        # Wait for .npy upload to complete
        for future in concurrent.futures.as_completed(futures):
            s3_key, success, error = future.result()
            if not success:
                print(f"      ⚠️  Upload warning for {s3_key}: {error}")


@lru_cache(maxsize=128)
def get_s3_size_cached(s3_key):
    """Get size of S3 object with caching"""
    try:
        response = s3_manager.s3.head_object(Bucket=S3_BUCKET, Key=s3_key)
        size_bytes = response["ContentLength"]
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    except:
        return "N/A"


def batch_generate(args):
    s3_processed_prefix = f"{S3_BASE_PATH}/{REPO_OWNER}/{REPO_NAME}/chunks/"
    s3_output_prefix = f"{S3_EMBEDDINGS_PATH}/{REPO_OWNER}/{REPO_NAME}/"

    normalized_current_owner, normalized_current_repo = extract_repo_parts(
        FULL_REPO_NAME
    )
    normalized_current_owner = normalized_current_owner or normalize_repo_owner(
        REPO_OWNER
    )
    normalized_current_repo = normalized_current_repo or normalize_repo_name(REPO_NAME)

    # List chunk files from S3
    print("📥 Listing files from S3...")
    try:
        response = s3_manager.s3.list_objects_v2(
            Bucket=S3_BUCKET, Prefix=s3_processed_prefix
        )
    except Exception as e:
        print(f"Error listing S3 objects: {e}")
        return

    if "Contents" not in response:
        print(
            f"Error: No files found in S3 path: s3://{S3_BUCKET}/{s3_processed_prefix}"
        )
        return

    # Filter for chunk files
    chunks_files = []
    for obj in response["Contents"]:
        key = obj["Key"]
        filename = key.split("/")[-1]
        if filename.endswith("_chunks.json") and not any(
            skip in filename
            for skip in [
                "strategy",
                "entities",
                "_git_chunks",
                "_gmail_chunks",
                "aggregated",
            ]
        ):
            chunks_files.append(key)

    if not chunks_files:
        print(f"Error: No chunks files found in s3://{S3_BUCKET}/{s3_processed_prefix}")
        return

    print(f"Found {len(chunks_files)} type-specific chunks files\n")

    # Group by repository and type with BETTER parsing
    by_repo = defaultdict(dict)
    for s3_key in chunks_files:
        filename = s3_key.split("/")[-1]
        parts = filename.replace(".json", "").split("_")

        if "chunks" in parts:
            chunks_idx = parts.index("chunks")
            if chunks_idx > 0:
                chunk_type = parts[chunks_idx - 1]
                repo_name = "_".join(parts[: chunks_idx - 1])

                if not chunk_type or chunk_type in ["git", "gmail", "unknown"]:
                    print(
                        f"   ⚠️  Skipping invalid chunk type '{chunk_type}' from {filename}"
                    )
                    continue

                by_repo[repo_name][chunk_type] = s3_key
            else:
                print(f"   ⚠️  Could not parse filename: {filename}")
        else:
            print(f"   ⚠️  Invalid filename format (missing 'chunks'): {filename}")

    if not by_repo:
        print(f"Error: No valid chunk files found after parsing")
        return

    print(f"Repositories found in filenames: {len(by_repo)}\n")
    for repo_name, types in by_repo.items():
        print(f"   {repo_name}:")
        for chunk_type, s3_key in types.items():
            print(f"      {chunk_type}: {s3_key.split('/')[-1]}")
    print()

    # Check for graph data in S3
    graph_s3_key = f"{S3_BASE_PATH}/{REPO_OWNER}/{REPO_NAME}/graph_data.json"
    has_graph = s3_manager.key_exists(graph_s3_key)

    provider = args.provider
    model = args.model

    if not provider:
        provider, default_model = auto_detect_provider()
        if not model:
            model = default_model
        print(f"Using provider: {provider} ({model})\n")

    try:
        temp_cache_dir = tempfile.mkdtemp(prefix="embeddings_cache_")
        generator = EmbeddingGenerator(
            provider=provider,
            model=model,
            batch_size=args.batch_size,
            cache_dir=Path(temp_cache_dir),
        )
    except Exception as e:
        print(f"Error initializing generator: {e}")
        return

    results = []

    # Process each type-specific file
    for repo_name, type_files in by_repo.items():
        print(f"\n{'=' * 70}")
        print(f"Processing repository: {repo_name}")
        print(f"{'=' * 70}")

        if has_graph:
            print(f"   🕸️  Found Graph Data: s3://{S3_BUCKET}/{graph_s3_key}")
        else:
            print(f"   ⚠️  Graph Data NOT found at: s3://{S3_BUCKET}/{graph_s3_key}")

        # OPTIMIZATION: Download all chunk files in parallel
        print(f"\n📥 Downloading {len(type_files)} chunk files in parallel...")
        download_futures = [
            executor.submit(download_json_parallel, s3_key)
            for s3_key in type_files.values()
        ]

        # Collect downloaded chunks
        chunks_by_type = {}
        for future in concurrent.futures.as_completed(download_futures):
            s3_key, chunks, error = future.result()
            if error:
                print(f"   ⚠️  Error downloading {s3_key.split('/')[-1]}: {error}")
                continue

            # Find chunk_type from s3_key
            for ct, key in type_files.items():
                if key == s3_key:
                    chunks_by_type[ct] = chunks
                    break

        print(f"✅ Downloaded {len(chunks_by_type)} files successfully\n")

        # Collect all chunks for combined index
        all_chunks_for_repo = []

        for chunk_type, chunks in chunks_by_type.items():
            print(f"\n   Type: {chunk_type}")

            try:
                if not chunks:
                    print(f"      Warning: Empty file, skipping...")
                    continue

                print(f"      Raw chunks: {len(chunks)}")

                filtered_chunks = []
                skipped_count = 0
                for chunk in chunks:
                    chunk_repo_raw = chunk.get("repo_name", "")
                    chunk_owner_raw = chunk.get("repo_owner", "")

                    normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(
                        chunk_repo_raw
                    )
                    if not normalized_chunk_owner and chunk_owner_raw:
                        normalized_chunk_owner = normalize_repo_owner(chunk_owner_raw)
                    if not normalized_chunk_repo:
                        normalized_chunk_repo = normalize_repo_name(chunk_repo_raw)

                    matches_repo = repo_matches(
                        normalized_current_owner,
                        normalized_current_repo,
                        normalized_chunk_owner,
                        normalized_chunk_repo,
                    )

                    if matches_repo:
                        chunk["repo_name"] = REPO_NAME
                        chunk["repo_owner"] = REPO_OWNER
                        filtered_chunks.append(chunk)
                    else:
                        skipped_count += 1

                if skipped_count > 0:
                    print(
                        f"      ⚠️  Filtered out {skipped_count} chunks from other repositories"
                    )

                chunks = filtered_chunks

                if not chunks:
                    print(
                        f"      Warning: No chunks for current repo after filtering, skipping..."
                    )
                    results.append(
                        (repo_name, chunk_type, "Skipped", "No chunks for current repo")
                    )
                    continue

                print(f"      Chunks for {REPO_OWNER}/{REPO_NAME}: {len(chunks)}")

                # Prepare chunks for embedding
                prepared_chunks, prep_stats = prepare_chunks_for_embedding(chunks)

                print(f"      Enhanced chunks: {prep_stats['processed']}")
                print(f"      Skipped: {prep_stats['skipped']}")

                if prep_stats["processed"] == 0:
                    print(f"      Warning: No chunks to embed, skipping...")
                    results.append(
                        (repo_name, chunk_type, "Skipped", "No embeddable chunks")
                    )
                    continue

                # Generate embeddings
                print(f"      Generating embeddings...")
                result = generator.generate_embeddings(prepared_chunks)

                # Save embeddings to S3 (optimized)
                print(f"      📤 Uploading to S3...")
                s3_output_path = f"{s3_output_prefix}{chunk_type}/{chunk_type}"
                save_embeddings_to_s3_fast(generator, result, s3_output_path)

                print(
                    f"      ✅ Saved -> s3://{S3_BUCKET}/{s3_output_path}.npy + .json"
                )

                results.append((repo_name, chunk_type, "Success", result["statistics"]))

                all_chunks_for_repo.extend(chunks)

            except Exception as e:
                print(f"      Error: {e}")
                import traceback

                traceback.print_exc()
                results.append((repo_name, chunk_type, "Failed", str(e)))

        # Generate combined "all" index
        final_all_chunks = []
        for chunk in all_chunks_for_repo:
            chunk_repo_raw = chunk.get("repo_name", "")
            chunk_owner_raw = chunk.get("repo_owner", "")

            normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(
                chunk_repo_raw
            )
            if not normalized_chunk_owner and chunk_owner_raw:
                normalized_chunk_owner = normalize_repo_owner(chunk_owner_raw)
            if not normalized_chunk_repo:
                normalized_chunk_repo = normalize_repo_name(chunk_repo_raw)

            if repo_matches(
                normalized_current_owner,
                normalized_current_repo,
                normalized_chunk_owner,
                normalized_chunk_repo,
            ):
                chunk["repo_name"] = REPO_NAME
                chunk["repo_owner"] = REPO_OWNER
                final_all_chunks.append(chunk)

        if final_all_chunks:
            print(
                f"\n   Generating combined 'all' index for {REPO_OWNER}/{REPO_NAME}..."
            )

            try:
                print(f"      Total chunks: {len(final_all_chunks)}")

                prepared_all, prep_all_stats = prepare_chunks_for_embedding(
                    final_all_chunks
                )

                print(f"      Enhanced: {prep_all_stats['processed']}")

                if prep_all_stats["processed"] > 0:
                    combined_result = generator.generate_embeddings(prepared_all)

                    print(f"      📤 Uploading combined index to S3...")
                    s3_all_output_path = f"{s3_output_prefix}all/all"
                    save_embeddings_to_s3_fast(
                        generator, combined_result, s3_all_output_path
                    )

                    print(
                        f"      ✅ Saved -> s3://{S3_BUCKET}/{s3_all_output_path}.npy + .json"
                    )

                    results.append(
                        (repo_name, "all", "Success", combined_result["statistics"])
                    )

            except Exception as e:
                print(f"      Failed to generate combined index: {e}")
                results.append((repo_name, "all", "Failed", str(e)))

    if has_graph:
        print(f"\n{'=' * 70}\nProcessing Graph Nodes: {REPO_NAME}\n{'=' * 70}")
        try:
            print(f"      📥 Downloading graph data...")
            graph_data = s3_manager.download_json(graph_s3_key)

            prepared_nodes, node_stats = prepare_graph_nodes(graph_data)

            if prepared_nodes:
                print(
                    f"      Generating embeddings for {len(prepared_nodes)} graph nodes..."
                )
                result = generator.generate_embeddings(prepared_nodes)

                print(f"      📤 Uploading graph embeddings to S3...")
                s3_graph_output_path = f"{s3_output_prefix}graph/graph_nodes"
                save_embeddings_to_s3_fast(generator, result, s3_graph_output_path)

                print(
                    f"      ✅ Saved -> s3://{S3_BUCKET}/{s3_graph_output_path}.npy + .json"
                )

                results.append(
                    (REPO_NAME, "graph_nodes", "Success", result["statistics"])
                )
            else:
                print("      No embeddable nodes found.")

        except Exception as e:
            print(f"      Failed to embed graph nodes: {e}")
            import traceback

            traceback.print_exc()
            results.append((REPO_NAME, "graph_nodes", "Failed", str(e)))

    # Cleanup
    try:
        import shutil

        shutil.rmtree(temp_cache_dir, ignore_errors=True)
    except:
        pass

    # Print summary
    print(f"\n{'=' * 70}")
    print("BATCH GENERATION SUMMARY")
    print(f"{'=' * 70}\n")

    successful = [r for r in results if r[2] == "Success"]
    skipped = [r for r in results if r[2] == "Skipped"]
    failed = [r for r in results if r[2] == "Failed"]

    print(f"Successful: {len(successful)}/{len(results)}")
    if skipped:
        print(f"Skipped: {len(skipped)}/{len(results)}")
    if failed:
        print(f"Failed: {len(failed)}/{len(results)}")

    if successful:
        by_type_summary = defaultdict(int)
        total_embeddings = 0

        for repo, ctype, status, stats in successful:
            if isinstance(stats, dict):
                count = stats.get("count", 0)
                by_type_summary[ctype] += count
                total_embeddings += count

        print(f"\nTotal embeddings generated: {total_embeddings}")
        print(f"\nBy type:")
        for ctype, count in sorted(by_type_summary.items()):
            print(f"   {ctype}: {count}")

    if failed:
        print(f"\nFailed:")
        for repo, ctype, status, error in failed:
            print(f"   {repo} ({ctype}): {error}")

    if skipped:
        print(f"\nSkipped:")
        for repo, ctype, status, reason in skipped:
            print(f"   {repo} ({ctype}): {reason}")

    print(f"\nOutput location: s3://{S3_BUCKET}/{s3_output_prefix}")
    print(f"\nNext Step:")
    print(f"   python core/VectorDB/build_indices.py")


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced embedding generation with entity + temporal + correlation context (OPTIMIZED)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python generate_embeddings.py --batch
        python generate_embeddings.py --provider openai --batch
                """,
    )
    parser.add_argument("input_file", nargs="?", help="Path to chunks JSON file")
    parser.add_argument(
        "--output-dir",
        default="../../data/Embeddings/",
        help="Output directory (legacy, now uses S3)",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "sentence-transformers", "cohere", "huggingface"],
    )
    parser.add_argument("--model", help="Model name")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument(
        "--cache-dir",
        default="../../data/Embeddings/embeddings_cache",
        help="Cache directory (legacy, now uses temp)",
    )
    parser.add_argument("--batch", action="store_true", help="Process all chunks files")

    args = parser.parse_args()

    if args.batch:
        batch_generate(args)
        return

    # S3 paths
    s3_chunks_prefix = f"{S3_BASE_PATH}/{REPO_OWNER}/{REPO_NAME}/chunks/"
    s3_output_prefix = f"{S3_EMBEDDINGS_PATH}/{REPO_OWNER}/{REPO_NAME}/"

    # List chunk files from S3
    print("📥 Listing files from S3...")
    try:
        response = s3_manager.s3.list_objects_v2(
            Bucket=S3_BUCKET, Prefix=s3_chunks_prefix
        )
    except Exception as e:
        print(f"Error listing S3 objects: {e}")
        sys.exit(1)

    if "Contents" not in response:
        try:
            embeddings_response = s3_manager.s3.list_objects_v2(
                Bucket=S3_BUCKET, Prefix=s3_output_prefix, MaxKeys=10
            )
            if "Contents" in embeddings_response and any(
                ".npy" in obj["Key"] for obj in embeddings_response["Contents"]
            ):
                print(f"✅ Embeddings already exist for {REPO_OWNER}/{REPO_NAME}")
                print(f"   Location: s3://{S3_BUCKET}/{s3_output_prefix}")
                print(
                    f"\n   No processed chunks found at: s3://{S3_BUCKET}/{s3_chunks_prefix}"
                )
                print(f"   This is expected if embeddings were already generated.")
                print(f"\n   To regenerate embeddings:")
                print(f"   1. Run: python main/DataProcessing/process_data.py")
                print(
                    f"   2. Then: python main/GenerateEmbedding/generate_embedding.py"
                )
                sys.exit(0)
        except:
            pass

        print(f"Error: No JSON files found at s3://{S3_BUCKET}/{s3_chunks_prefix}")
        print(f"\nTo generate embeddings, you need:")
        print(
            f"  1. Run data processing first: python main/DataProcessing/process_data.py"
        )
        print(
            f"  2. Then generate embeddings: python main/GenerateEmbedding/generate_embedding.py"
        )
        sys.exit(1)

    # Filter for chunk files
    chunks_files = []
    for obj in response["Contents"]:
        key = obj["Key"]
        filename = key.split("/")[-1]
        if filename.endswith("_chunks.json") and not any(
            skip in filename for skip in ["strategy", "entities", "aggregated"]
        ):
            chunks_files.append(key)

    if not chunks_files:
        print(
            f"Error: No valid chunk files found at s3://{S3_BUCKET}/{s3_chunks_prefix}"
        )
        sys.exit(1)

    print(f"Found {len(chunks_files)} JSON files to embed:")
    for s3_key in chunks_files:
        print("  ", s3_key.split("/")[-1])

    provider = args.provider
    model = args.model

    temp_cache_dir = tempfile.mkdtemp(prefix="embeddings_cache_")

    if not provider:
        print("Auto-detecting embedding provider...")
        provider, default_model = auto_detect_provider()
        if provider == "openai":
            print(f"Detected OpenAI API key")
        elif provider == "cohere":
            print(f"Detected Cohere API key")
        else:
            print(f"No API keys found - using free Sentence-Transformers")
        if not model:
            model = default_model
        print(f"   Provider: {provider}")
        print(f"   Model: {model}\n")
    else:
        default_models = {
            "openai": "text-embedding-3-small",
            "sentence-transformers": "all-MiniLM-L6-v2",
            "cohere": "embed-english-v3.0",
            "huggingface": "sentence-transformers/all-MiniLM-L6-v2",
        }
        if not model:
            model = default_models[provider]

    print(f"{'='*70}")
    print(f"ENHANCED EMBEDDING GENERATION - STEP 3 (OPTIMIZED)")
    print(f"{'='*70}\n")

    # OPTIMIZATION: Download all chunk files in parallel
    print(f"📥 Downloading {len(chunks_files)} chunk files in parallel...")
    download_futures = [
        executor.submit(download_json_parallel, s3_key) for s3_key in chunks_files
    ]

    all_chunks = []
    for future in concurrent.futures.as_completed(download_futures):
        s3_key, data, error = future.result()
        if error:
            print(f"   ⚠️  Error downloading {s3_key.split('/')[-1]}: {error}")
            continue

        if isinstance(data, list):
            all_chunks.extend(data)
        else:
            print(f"   Warning: Skipping {s3_key.split('/')[-1]} - JSON is not a list")

    print(f"✅ Downloaded successfully\n")

    chunks = all_chunks
    print(f"Total merged chunks: {len(chunks)}\n")

    source_type = detect_source_type(chunks)
    if len(chunks_files) == 1:
        file_name = chunks_files[0].split("/")[-1].replace(".json", "")
    else:
        file_name = "combined"

    if not chunks:
        print(f"Error: No chunks found in file")
        sys.exit(1)

    print(f"   File: {file_name}")
    print(f"   Source: {source_type}")
    print(f"   Total chunks: {len(chunks)}")

    chunk_types = {}
    for chunk in chunks:
        ct = chunk.get("type", "unknown")
        chunk_types[ct] = chunk_types.get(ct, 0) + 1

    print(f"\n   Chunk types:")
    for ct, count in sorted(chunk_types.items()):
        print(f"      {ct}: {count}")

    print("\nComputing repository metrics (lines, functions, structure)...")
    repo_metrics = compute_repo_metrics(chunks)
    metrics_chunk = {
        "chunk_id": f"repo_metrics_{int(datetime.now(timezone.utc).timestamp())}",
        "type": "repo_metrics",
        "source": "computed",
        "content": (
            "Repository metrics: "
            f"total_lines={repo_metrics['total_lines']}, "
            f"total_functions={repo_metrics['total_functions']}, "
            f"total_files={repo_metrics['total_files']}. "
            "By repo: "
            + ", ".join(
                f"{r}({s['files']} files)" for r, s in repo_metrics["by_repo"].items()
            )
        ),
        "metadata": {
            "computed_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "metrics": repo_metrics,
        },
        "full_chunk": {"metrics": repo_metrics},
        "skip_embedding": False,
    }
    chunks = [metrics_chunk] + chunks

    print(f"\nPreparing enhanced chunks for embedding...")
    print(f"   Extracting main content")
    print(f"   Formatting entity context")
    print(f"   Adding temporal context")
    if source_type == "gmail":
        print(f"   Including GitHub correlation data")

    prepared_chunks, prep_stats = prepare_chunks_for_embedding(chunks)

    print(f"\n   Preparation complete:")
    print(f"      Total chunks: {prep_stats['total']}")
    print(f"      Will embed: {prep_stats['processed']}")
    print(f"      Skipped: {prep_stats['skipped']}")
    if prep_stats["raw_data_refs"] > 0:
        print(f"        Raw data refs: {prep_stats['raw_data_refs']} (too large)")
    if prep_stats["empty_content"] > 0:
        print(f"        Empty content: {prep_stats['empty_content']}")

    print(f"\n   By retrieval priority:")
    for priority in sorted(prep_stats["by_priority"].keys()):
        count = prep_stats["by_priority"][priority]
        print(f"      Priority {priority}: {count} chunks")

    if prep_stats["processed"] == 0:
        print(f"\nError: No chunks to embed!")
        sys.exit(1)

    if prepared_chunks:
        sample = prepared_chunks[0]
        print(f"\n   Sample enhanced chunk:")
        print(f"      ID: {sample.get('chunk_id', 'N/A')}")
        print(f"      Type: {sample.get('type', 'N/A')}")
        print(f"      Content length: {len(sample.get('content', ''))} chars")
        print(f"      Preview: {sample.get('content', '')[:150]}...\n")

    try:
        generator = EmbeddingGenerator(
            provider=provider,
            model=model,
            batch_size=args.batch_size,
            cache_dir=Path(temp_cache_dir),
        )
    except Exception as e:
        print(f"\nError initializing embedding generator: {e}")
        print(f"\nInstallation guide:")
        if provider == "openai":
            print(f"   1. pip install openai python-dotenv")
            print(f"   2. Create .env file with: OPENAI_API_KEY=your-key")
        elif provider == "sentence-transformers":
            print(f"   pip install sentence-transformers")
        elif provider == "cohere":
            print(f"   1. pip install cohere python-dotenv")
            print(f"   2. Create .env file with: COHERE_API_KEY=your-key")
        try:
            import shutil

            shutil.rmtree(temp_cache_dir, ignore_errors=True)
        except:
            pass
        sys.exit(1)

    print("\nGenerating embeddings by chunk type...")

    chunks_by_type = defaultdict(list)
    for prepared_chunk in prepared_chunks:
        chunk_type = prepared_chunk.get("type", "unknown")
        chunks_by_type[chunk_type].append(prepared_chunk)

    type_results = {}
    all_chunks_for_combined = []

    print(f"\n   Found {len(chunks_by_type)} chunk types:")
    for chunk_type in sorted(chunks_by_type.keys()):
        print(f"      {chunk_type}: {len(chunks_by_type[chunk_type])} chunks")

    print("\n   Generating embeddings for each type...\n")

    for chunk_type, type_chunks in sorted(chunks_by_type.items()):
        if chunk_type == "repo_metrics":
            all_chunks_for_combined.extend(type_chunks)
            continue

        print(f"   Processing {chunk_type}...")
        try:
            type_result = generator.generate_embeddings(type_chunks)

            print(f"      📤 Uploading to S3...")
            s3_type_output_path = f"{s3_output_prefix}{chunk_type}/{chunk_type}"
            save_embeddings_to_s3_fast(generator, type_result, s3_type_output_path)

            type_results[chunk_type] = {
                "s3_path": s3_type_output_path,
                "config": type_result["config"],
                "stats": type_result["statistics"],
                "count": len(type_chunks),
            }

            print(
                f"      ✅ Saved -> s3://{S3_BUCKET}/{s3_type_output_path}.npy + .json"
            )
            print(f"        Embeddings: {type_result['statistics'].get('count', 0)}")

            all_chunks_for_combined.extend(type_chunks)

        except Exception as e:
            print(f"      ✗ Error: {e}")
            import traceback

            traceback.print_exc()

    if all_chunks_for_combined:
        print(f"\n   Generating combined 'all' index...")
        try:
            print(f"      Total chunks: {len(all_chunks_for_combined)}")

            combined_result = generator.generate_embeddings(all_chunks_for_combined)

            print(f"      📤 Uploading combined index to S3...")
            s3_all_output_path = f"{s3_output_prefix}all/all"
            save_embeddings_to_s3_fast(generator, combined_result, s3_all_output_path)

            type_results["all"] = {
                "s3_path": s3_all_output_path,
                "config": combined_result["config"],
                "stats": combined_result["statistics"],
                "count": len(all_chunks_for_combined),
            }

            print(
                f"      ✅ Saved -> s3://{S3_BUCKET}/{s3_all_output_path}.npy + .json"
            )
            print(
                f"        Embeddings: {combined_result['statistics'].get('count', 0)}"
            )

        except Exception as e:
            print(f"      ✗ Failed to generate combined index: {e}")
            import traceback

            traceback.print_exc()

    try:
        import shutil

        shutil.rmtree(temp_cache_dir, ignore_errors=True)
    except:
        pass

    print(f"\n{'='*70}")
    print("EMBEDDING GENERATION COMPLETE")
    print(f"{'='*70}")

    print(f"\nConfiguration:")
    print(f"   Source: {source_type}")
    print(f"   Provider: {provider}")
    print(f"   Model: {model}")
    if type_results:
        first_result = next(iter(type_results.values()))
        print(f"   Dimension: {first_result['config']['dimension']}")

    print(f"\nGenerated Embeddings by Type:")
    total_embeddings = 0
    for chunk_type in sorted(type_results.keys()):
        result_info = type_results[chunk_type]
        embeddings_count = result_info["stats"].get("count", 0)
        total_embeddings += embeddings_count
        s3_path = result_info["s3_path"]
        print(f"   {chunk_type}: {embeddings_count} embeddings")
        print(
            f"      Vectors: s3://{S3_BUCKET}/{s3_path}.npy ({get_s3_size_cached(f'{s3_path}.npy')})"
        )
        print(
            f"      Metadata: s3://{S3_BUCKET}/{s3_path}.json ({get_s3_size_cached(f'{s3_path}.json')})"
        )

    print(f"\n   Total embeddings: {total_embeddings}")

    if provider in ["openai", "cohere"]:
        estimate_cost(
            provider,
            model,
            len(prepared_chunks),
            type_results.get("all", {}).get("stats", {}),
        )

    print(f"\n{'='*70}\n")
    print(f"Output structure in S3:")
    print(f"   s3://{S3_BUCKET}/{s3_output_prefix}")
    for chunk_type in sorted(type_results.keys()):
        print(f"      {chunk_type}/")
        print(f"         {chunk_type}.npy")
        print(f"         {chunk_type}.json")
    print(f"\nReady for vector DB indexing!")
    print(f"   Next: python core/VectorDB/build_indices.py\n")


if __name__ == "__main__":
    main()
