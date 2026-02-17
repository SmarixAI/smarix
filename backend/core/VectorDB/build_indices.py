"""
Build Multi-Index VectorDB (Step 4) - S3 OPTIMIZED
Creates ONE folder per embedding type inside: s3://bucket/VectorDB/{owner}/{repo_name}/<type>
Each folder contains:
   - faiss.index
   - metadata.pkl
   - config.json
WITH PARALLEL S3 OPERATIONS FOR 3-5x SPEED IMPROVEMENT
"""

import os
import sys
import json
import numpy as np
from pathlib import Path
import faiss
import pickle
import networkx as nx
from collections import defaultdict
import re
import tempfile
import concurrent.futures
from functools import lru_cache
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

# Add backend directory to sys.path to resolve utils imports
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from core.VectorDB.keyword_index_builder import build_keyword_index
from utils.s3 import s3_manager

# S3 Configuration
S3_BUCKET = "smarix-data-apsouth1"
S3_BASE_PATH = "DataProcessing"
S3_EMBEDDINGS_PATH = "Embeddings"
S3_VECTORDB_PATH = "VectorDB"

# Thread pool for parallel S3 operations
executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)


def load_current_repo_from_state():
    """Load current repo from S3 runtime_state.json"""
    state_s3_key = "Admin/state/runtime_state.json"

    try:
        state = s3_manager.download_json(state_s3_key)
    except Exception as e:
        print(f"❌ Failed to load state from S3: {e}")
        print(f"\n💡 Make sure AWS credentials are configured:")
        print(f"   Option 1: Set environment variables:")
        print(f"      export AWS_ACCESS_KEY_ID=your_access_key")
        print(f"      export AWS_SECRET_ACCESS_KEY=your_secret_key")
        print(f"\n   Option 2: Add to .env file:")
        print(f"      AWS_ACCESS_KEY_ID=your_access_key")
        print(f"      AWS_SECRET_ACCESS_KEY=your_secret_key")
        print(f"\n   Option 3: Configure AWS CLI:")
        print(f"      aws configure")
        raise RuntimeError(
            f"❌ State file not found in S3: s3://{S3_BUCKET}/{state_s3_key}"
        )

    curr_repo = state.get("curr_repo")
    if not curr_repo:
        raise RuntimeError("❌ curr_repo missing in runtime_state.json")

    owner = curr_repo.get("owner")
    name = curr_repo.get("name")

    if not owner or not name:
        raise RuntimeError(
            "❌ curr_repo.owner or curr_repo.name missing in runtime_state.json"
        )

    return owner, name

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


REPO_OWNER, REPO_NAME = load_current_repo_from_state()
FULL_REPO_NAME = f"{REPO_OWNER}/{REPO_NAME}"

print(f"\n{'='*70}")
print(f"BUILDING VECTORDB FOR REPO: {REPO_OWNER}/{REPO_NAME} (S3 OPTIMIZED)")
print(f"{'='*70}\n")

# S3 paths
S3_EMBEDDINGS_PREFIX = f"{S3_EMBEDDINGS_PATH}/{REPO_OWNER}/{REPO_NAME}/"
S3_VECTORDB_PREFIX = f"{S3_VECTORDB_PATH}/{REPO_OWNER}/{REPO_NAME}/"
S3_PROCESSED_PREFIX = f"{S3_BASE_PATH}/{REPO_OWNER}/{REPO_NAME}/"


def download_file_parallel(s3_key):
    """Download file from S3 in parallel"""
    try:
        filename = s3_key.split('/')[-1]
        
        # Get file size first for progress indication
        file_size_mb = 0
        file_size_bytes = 0
        try:
            head_response = s3_manager.s3.head_object(Bucket=S3_BUCKET, Key=s3_key)
            file_size_bytes = head_response.get('ContentLength', 0)
            file_size_mb = file_size_bytes / (1024 * 1024)
            if file_size_mb > 0.1:  # Show progress for files > 100KB
                print(f"         Downloading {filename} ({file_size_mb:.1f} MB)...")
        except Exception as e:
            print(f"         Warning: Could not get file size for {filename}: {e}")
        
        # Set timeout to 5 minutes for large files
        timeout_seconds = 300 if file_size_mb > 10 else 60
        
        try:
            # Download file
            response = s3_manager.s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
            
            # Read in chunks for large files to show progress
            if file_size_mb > 10:
                content = b""
                chunk_size = 10 * 1024 * 1024  # 10MB chunks
                total_read = 0
                last_progress = -1
                while True:
                    chunk = response["Body"].read(chunk_size)
                    if not chunk:
                        break
                    content += chunk
                    total_read += len(chunk)
                    if file_size_bytes > 0:
                        progress = int((total_read / file_size_bytes) * 100)
                        # Print every 25% progress
                        if progress >= last_progress + 25:
                            print(f"         Progress: {progress}% ({total_read / (1024*1024):.1f} MB / {file_size_mb:.1f} MB)")
                            last_progress = progress
            else:
                content = response["Body"].read()
            
            if file_size_mb > 0.1:
                print(f"         ✓ Downloaded {filename}")
            
            return s3_key, content, None
        except TimeoutError:
            return s3_key, None, f"Download timeout after {timeout_seconds}s"
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"         ✗ Error downloading {s3_key.split('/')[-1]}: {error_msg}")
        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            print(f"         💡 Tip: File might be very large. Check S3 connection and file size.")
        traceback.print_exc()
        return s3_key, None, error_msg


def upload_file_parallel(args):
    """Upload file to S3 in parallel"""
    file_path, s3_key = args
    try:
        with open(file_path, "rb") as f:
            s3_manager.s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=f.read())
        return s3_key, True, None
    except Exception as e:
        return s3_key, False, str(e)


def load_embeddings_from_s3(s3_npy_key, s3_json_key):
    """Load vectors + metadata from S3"""
    print(f"      Downloading embeddings from S3...")
    print(f"         Files: {s3_npy_key.split('/')[-1]}, {s3_json_key.split('/')[-1]}")

    download_tasks = [s3_npy_key, s3_json_key]
    futures = [executor.submit(download_file_parallel, key) for key in download_tasks]

    results = {}
    completed = 0
    for future in concurrent.futures.as_completed(futures):
        s3_key, content, error = future.result()
        completed += 1
        if error:
            raise FileNotFoundError(f"Failed to download {s3_key}: {error}")
        results[s3_key] = content
        print(f"         Progress: {completed}/{len(download_tasks)} files downloaded")
    
    print(f"      Processing downloaded files...")

    # Try loading with np.load first (handles .npy format properly)
    try:
        import io
        vectors = np.load(io.BytesIO(results[s3_npy_key]))
    except:
        # Fall back to raw float32 buffer if not in .npy format
        vectors = np.frombuffer(results[s3_npy_key], dtype=np.float32)
    
    data = json.loads(results[s3_json_key].decode("utf-8"))

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "items" in data:
        items = data["items"]
    elif isinstance(data, dict) and "metadata" in data and isinstance(data["metadata"], list):
        items = data["metadata"]
    else:
        raise ValueError("Embedding JSON missing metadata or items field")

    num_items = len(items)
    if num_items == 0:
        raise ValueError("No items found in metadata")

    # If vectors is 1D, reshape it
    if len(vectors.shape) == 1:
        if len(vectors) % num_items != 0:
            raise ValueError(
                f"Cannot reshape {len(vectors)} values into {num_items} vectors evenly"
            )
        dim = len(vectors) // num_items
        vectors = vectors.reshape(num_items, dim)

    if len(items) != len(vectors):
        raise ValueError(
            f"Mismatch: {len(vectors)} vectors vs {len(items)} metadata records"
        )

    flat_metadata = []
    for i, item in enumerate(items):
        chunk_id = item.get("chunk_id") or item.get("id") or str(i)

        if "metadata" in item and isinstance(item["metadata"], dict):
            md = item["metadata"].copy()

            # 🔥 CRITICAL: preserve PR-specific fields
            for key in [
                "merged_by",
                "pr_status",
                "is_merged",
                "base_branch",
                "head_branch",
                "author",
                "reviewers"
            ]:
                if key in item.get("metadata", {}) and key not in md:
                    md[key] = item["metadata"][key]


            # 🔥 CRITICAL: merge ALL top-level metadata fields
            for k, v in item.items():
                if k not in ["vector", "id", "metadata", "content"]:
                    if k not in md:
                        md[k] = v

            # 🔥 OPTIONAL but recommended: merge raw_data
            raw_data = item.get("raw_data", {})
            if isinstance(raw_data, dict):
                for k, v in raw_data.items():
                    if k not in md:
                        md[k] = v

            # Merge top-level fields that might not be in nested metadata
            for key in ["repo_name", "repo_owner", "source", "type", "chunk_type"]:
                if key in item and key not in md:
                    md[key] = item[key]
        else:
            md = item.copy()

        md.pop("id", None)
        md.pop("metadata", None)
        md.pop("vector", None)
        md["chunk_id"] = chunk_id
        flat_metadata.append(md)

    return flat_metadata, vectors

def build_faiss_index(vectors: np.ndarray):
    """FAISS L2 index"""
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    return index


def save_index_and_metadata_to_s3(index_name: str, index, metadata):
    """Save FAISS index with metadata to S3"""
    from utils.metadata_normalizer import MetadataNormalizer

    print(f"      📤 Uploading {index_name} to S3...")

    # Normalize metadata using MetadataNormalizer for consistency
    for m in metadata:
        meta_norm = MetadataNormalizer(m)
        # Use normalizer to get standardized values, but preserve original fields for backward compat
        chunk_type = meta_norm.get_chunk_type()
        if chunk_type:
            m["chunk_type"] = chunk_type
            m["type"] = chunk_type  # Alias for backward compat

        file_path = meta_norm.get_file_path()
        if file_path:
            m["file_path"] = file_path

        # Ensure repo_name is set - fallback to current repo
        repo_name = meta_norm.get_repo_name()
        if not repo_name:
            repo_name = f"{REPO_OWNER}/{REPO_NAME}"
        m["repo_name"] = repo_name

        repo_owner = meta_norm.get_repo_owner()
        if not repo_owner:
            repo_owner = REPO_OWNER
        m["repo_owner"] = repo_owner

        language = meta_norm.get_language()
        if language:
            m["language"] = language

        pr_number = meta_norm.get_pr_number()
        if pr_number is not None:
            m["pr_number"] = pr_number

        issue_number = meta_norm.get_issue_number()
        if issue_number is not None:
            m["issue_number"] = issue_number

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save files locally first
        index_file = os.path.join(tmpdir, "faiss.index")
        metadata_file = os.path.join(tmpdir, "metadata.pkl")
        config_file = os.path.join(tmpdir, "config.json")

        # Write FAISS index
        faiss.write_index(index, index_file)

        # Write metadata pickle
        with open(metadata_file, "wb") as f:
            pickle.dump(
                {
                    "metadata": metadata,
                    "chunk_ids": [
                        m.get("chunk_id", str(i)) for i, m in enumerate(metadata)
                    ],
                    "dimension": index.d,
                    "index_type": "flat",
                    "metric": "l2",
                },
                f,
            )

        # Write config JSON
        config = {
            "index_name": index_name,
            "dimension": index.d,
            "vector_dimension": index.d,
            "index_type": "flat",
            "metric": "l2",
            "total_records": len(metadata),
            "index_file": "faiss.index",
            "metadata_file": "metadata.pkl",
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # Upload all three files in parallel
        s3_index_prefix = f"{S3_VECTORDB_PREFIX}{index_name}/"
        upload_tasks = [
            (index_file, f"{s3_index_prefix}faiss.index"),
            (metadata_file, f"{s3_index_prefix}metadata.pkl"),
        ]

        futures = [executor.submit(upload_file_parallel, task) for task in upload_tasks]

        # Upload config separately (JSON)
        s3_manager.upload_json(config, f"{s3_index_prefix}config.json")

        # Wait for parallel uploads
        for future in concurrent.futures.as_completed(futures):
            s3_key, success, error = future.result()
            if not success:
                print(f"      ⚠️  Upload warning for {s3_key}: {error}")

    print(
        f"   ✅ Stored {index_name} → s3://{S3_BUCKET}/{s3_index_prefix} ({len(metadata)} vectors)"
    )


def build_graph_structure():
    """
    Load graph_data.json from S3 and build a NetworkX graph object.
    """
    graph_s3_key = f"{S3_PROCESSED_PREFIX}graph_data.json"

    if not s3_manager.key_exists(graph_s3_key):
        print(
            f"   ⚠️ No graph_data.json found at s3://{S3_BUCKET}/{graph_s3_key}. Skipping Graph Structure."
        )
        return

    print(f"\n🕸️  Building NetworkX Graph Structure...")
    try:
        print(f"      📥 Downloading graph data from S3...")
        data = s3_manager.download_json(graph_s3_key)

        G = nx.DiGraph()

        for node in data.get("nodes", []):
            G.add_node(
                node["id"], **node.get("properties", {}), label=node.get("label")
            )

        for edge in data.get("edges", []):
            G.add_edge(edge["source"], edge["target"], type=edge.get("type"))

        # Save to temp file then upload to S3
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pkl") as tmp:
            pickle.dump(G, tmp)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as f:
                s3_manager.s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=f"{S3_VECTORDB_PREFIX}graph_structure.pkl",
                    Body=f.read(),
                )

            print(
                f"   ✅ Graph Saved: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
            )
            print(
                f"   ✅ Location: s3://{S3_BUCKET}/{S3_VECTORDB_PREFIX}graph_structure.pkl"
            )
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        print(f"   ❌ Failed to build graph structure: {e}")
        import traceback

        traceback.print_exc()

def process_single_embedding_type(folder_name, normalized_current_owner, normalized_current_repo):
    """Process a single embedding type (can be called in parallel)"""
    try:
        # Handle 'graph' -> 'graph_nodes' mapping
        if folder_name == "graph":
            index_name = "graph_nodes"
            s3_base_name = "graph_nodes"
        else:
            index_name = folder_name
            s3_base_name = folder_name

        print(f"\n🔹 Processing: {index_name}")

        s3_npy_key = f"{S3_EMBEDDINGS_PREFIX}{folder_name}/{s3_base_name}.npy"
        s3_json_key = f"{S3_EMBEDDINGS_PREFIX}{folder_name}/{s3_base_name}.json"

        # Check for existence
        if not s3_manager.key_exists(s3_npy_key) or not s3_manager.key_exists(s3_json_key):
            print(f"   ⚠️  Missing files - skipping {index_name}")
            return None

        # Load embeddings
        metadata, vectors = load_embeddings_from_s3(s3_npy_key, s3_json_key)
        print(f"   ✓ Loaded {len(vectors)} vectors (dim: {vectors.shape[1]})")

        # Filter metadata (same logic as before)
        from utils.repo_normalizer import (
            normalize_repo_name,
            normalize_repo_owner,
            repo_matches,
            extract_repo_parts,
        )

        filtered_metadata = []
        filtered_indices = []
        skipped_count = 0
        fixed_count = 0

        for i, m in enumerate(metadata):
            chunk_repo_raw = m.get("repo_name") or m.get("repository") or m.get("repo") or None
            chunk_owner_raw = m.get("repo_owner") or m.get("owner") or None

            if not chunk_repo_raw or str(chunk_repo_raw).strip() in ["", "None"]:
                m["repo_name"] = REPO_NAME
                m["repo_owner"] = REPO_OWNER
                filtered_metadata.append(m)
                filtered_indices.append(i)
                fixed_count += 1
                continue

            normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(chunk_repo_raw)
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
                m["repo_name"] = REPO_NAME
                m["repo_owner"] = REPO_OWNER
                filtered_metadata.append(m)
                filtered_indices.append(i)
            else:
                skipped_count += 1

        if fixed_count > 0 or skipped_count > 0:
            vectors = vectors[filtered_indices]
            metadata = filtered_metadata
            if fixed_count > 0:
                print(f"   ✓ Fixed {fixed_count} embeddings")
            if skipped_count > 0:
                print(f"   ✓ Filtered {skipped_count} from other repos")

        if len(metadata) == 0:
            print(f"   ⚠️  No embeddings for current repo")
            return None

        # Enrich metadata for specific types
        if index_name.lower() == "issue":
            for m in metadata:
                if "issue_number" not in m:
                    entities = m.get("entities", {})
                    if isinstance(entities, dict) and entities.get("issue_number"):
                        try:
                            m["issue_number"] = int(entities["issue_number"])
                        except:
                            m["issue_number"] = str(entities["issue_number"])
                content = m.get("content", "") or ""
                if content and "issue_number" not in m:
                    match = re.search(r"issue\s*#\s*(\d+)", content, re.IGNORECASE)
                    if match:
                        m["issue_number"] = int(match.group(1))
                m["chunk_type"] = "issue"
                m["type"] = "issue"

        if index_name.lower() == "pr":
            for m in metadata:
                content = m.get("content", "") or ""
                match = re.search(r"pr\s*#(\d+)", content, re.IGNORECASE)
                if match:
                    m["pr_number"] = int(match.group(1))
                m["chunk_type"] = "pr"
                m["type"] = "pr"

            if index_name.lower() == "pr":
                for m in metadata:
                    # 🔒 Ensure merged_by is preserved
                    if "merged_by" not in m:
                        entities = m.get("entities", {})
                        if isinstance(entities, dict) and "merged_by" in entities:
                            m["merged_by"] = entities["merged_by"]

                    m["chunk_type"] = "pr"
                    m["type"] = "pr"


        # Build index
        index = build_faiss_index(vectors)
        
        # Save to S3
        save_index_and_metadata_to_s3(index_name, index, metadata)
        
        # Return data for "all" index
        return {
            "index_name": index_name,
            "metadata": metadata,
            "vectors": vectors,
            "success": True
        }
        
    except Exception as e:
        print(f"   ❌ Error processing {folder_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    skip_types = {"embeddings_cache"}

    print(f"📥 Listing embedding types from S3...")

    # List all objects in embeddings prefix
    try:
        response = s3_manager.s3.list_objects_v2(
            Bucket=S3_BUCKET, Prefix=S3_EMBEDDINGS_PREFIX, Delimiter="/"
        )
    except Exception as e:
        print(f"❌ Failed to list S3 objects: {e}")
        return

    if "CommonPrefixes" not in response:
        print(f"❌ No embedding types found at s3://{S3_BUCKET}/{S3_EMBEDDINGS_PREFIX}")
        print(f"\nPlease run the embedding generation step first:")
        print(f"   python main/GenerateEmbedding/generate_embedding.py --batch")
        return

    # Extract type directories
    type_dirs = []
    for prefix in response["CommonPrefixes"]:
        type_name = prefix["Prefix"].rstrip("/").split("/")[-1]
        if type_name not in skip_types:
            type_dirs.append(type_name)

    if not type_dirs:
        print(f"❌ No valid embedding types found")
        return

    print(f"📦 Found {len(type_dirs)} embedding types:")
    for d in type_dirs:
        print("   •", d)
    print()

    # Normalize current repo info
    from utils.repo_normalizer import extract_repo_parts, normalize_repo_owner, normalize_repo_name
    
    normalized_current_owner, normalized_current_repo = extract_repo_parts(FULL_REPO_NAME)
    if not normalized_current_owner:
        normalized_current_owner = normalize_repo_owner(REPO_OWNER)
    if not normalized_current_repo:
        normalized_current_repo = normalize_repo_name(REPO_NAME)

    # PARALLEL PROCESSING: Process all embedding types concurrently
    print(f"\n🚀 Processing {len(type_dirs)} types in parallel...\n")
    
    processing_executor = concurrent.futures.ThreadPoolExecutor(max_workers=min(len(type_dirs), 5))
    
    futures = {}
    for folder_name in type_dirs:
        future = processing_executor.submit(
            process_single_embedding_type,
            folder_name,
            normalized_current_owner,
            normalized_current_repo
        )
        futures[future] = folder_name
    
    # Collect results
    built_indices = []
    all_metadata = []
    all_vectors = []
    
    for future in concurrent.futures.as_completed(futures):
        folder_name = futures[future]
        try:
            result = future.result()
            if result and result.get("success"):
                index_name = result["index_name"]
                built_indices.append(index_name)
                
                # Collect for combined index
                if index_name != "all" and index_name != "graph_nodes":
                    metadata = result["metadata"]
                    for m in metadata:
                        m["source_index"] = index_name
                    all_metadata.extend(metadata)
                    all_vectors.append(result["vectors"])
                    
                print(f"✅ Completed: {index_name}")
        except Exception as e:
            print(f"❌ Failed: {folder_name} - {e}")
    
    processing_executor.shutdown(wait=True)

    # 🔎 Build keyword index once for full repo
    if all_metadata:
        print("\n🔎 Building keyword inverted index...")

        inverted_index, idf_scores = build_keyword_index(all_metadata)

        keyword_prefix = f"{S3_VECTORDB_PREFIX}keyword_index/"

        s3_manager.upload_json(
            inverted_index,
            f"{keyword_prefix}inverted_index.json"
        )

        s3_manager.upload_json(
            idf_scores,
            f"{keyword_prefix}idf_scores.json"
        )

        print(f"✅ Keyword index uploaded to s3://{S3_BUCKET}/{keyword_prefix}")


    # Build combined "all" index
    if all_vectors:
        print(f"\n🔹 Building combined 'all' index...")
        try:
            combined_vectors = np.vstack(all_vectors)
            all_index = build_faiss_index(combined_vectors)
            save_index_and_metadata_to_s3("all", all_index, all_metadata)
            built_indices.append("all")
        except Exception as e:
            print(f"   ❌ Failed to build combined index: {e}")

    # Build graph structure
    build_graph_structure()

    print(f"\n{'='*70}")
    print("🎉 Multi-Index VectorDB Build Complete!")
    print(f"{'='*70}")
    print(f"📁 Location: s3://{S3_BUCKET}/{S3_VECTORDB_PREFIX}")
    print(f"✅ Built {len(built_indices)} indices:")
    for idx in built_indices:
        print(f"   • {idx}")
    print()

if __name__ == "__main__":
    main()