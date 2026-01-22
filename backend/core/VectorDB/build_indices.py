"""
Build Multi-Index VectorDB (Step 4)
Creates ONE folder per embedding type inside: data/VectorDB/{owner}/{repo_name}/<type>
Each folder contains:
   - faiss.index
   - metadata.pkl
   - config.json
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

# Add backend directory to sys.path to resolve utils imports
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


STATE_FILE = Path(
    Path(__file__).resolve().parents[2]
    / "data"
    / "Admin"
    / "state"
    / "runtime_state.json"
)


def load_current_repo_from_state():
    """Load current repo from runtime_state.json with better error handling"""
    if not STATE_FILE.exists():
        raise RuntimeError(f"❌ State file not found: {STATE_FILE}")
    
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    curr_repo = state.get("curr_repo")
    if not curr_repo:
        raise RuntimeError("❌ curr_repo missing in runtime_state.json")

    owner = curr_repo.get("owner")
    name = curr_repo.get("name")
    
    if not owner or not name:
        raise RuntimeError("❌ curr_repo.owner or curr_repo.name missing in runtime_state.json")

    return owner, name

REPO_OWNER, REPO_NAME = load_current_repo_from_state()
FULL_REPO_NAME = f"{REPO_OWNER}/{REPO_NAME}"

print(f"\n{'='*70}")
print(f"BUILDING VECTORDB FOR REPO: {REPO_OWNER}/{REPO_NAME}")
print(f"{'='*70}\n")

# Use absolute paths from script location (not relative to CWD)
backend_dir = Path(__file__).resolve().parents[2]
EMBEDDINGS_DIR = backend_dir / "data" / "Embeddings" / REPO_OWNER / REPO_NAME
VECTORDB_ROOT = backend_dir / "data" / "VectorDB" / REPO_OWNER / REPO_NAME
PROCESSED_DATA_DIR = backend_dir / "data" / "DataProcessing" / REPO_OWNER / REPO_NAME

VECTORDB_ROOT.mkdir(parents=True, exist_ok=True)


def load_embeddings(base_path: Path):
    """
    Load vectors + metadata and convert to FLAT legacy format used by chatbot.
    """
    npy_path = base_path.with_suffix(".npy")
    json_path = base_path.with_suffix(".json")

    if not npy_path.exists() or not json_path.exists():
        raise FileNotFoundError(f"Missing .npy or .json files at {base_path}")

    vectors = np.load(npy_path).astype("float32")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "items" in data:
        items = data["items"]
    elif (
        isinstance(data, dict)
        and "metadata" in data
        and isinstance(data["metadata"], list)
    ):
        items = data["metadata"]
    else:
        raise ValueError("Embedding JSON missing metadata or items field")

    if len(items) != len(vectors):
        raise ValueError(
            f"❌ Mismatch: {len(vectors)} vectors vs {len(items)} metadata records"
        )

    flat_metadata = []
    for i, item in enumerate(items):
        chunk_id = item.get("chunk_id") or item.get("id") or str(i)

        if "metadata" in item and isinstance(item["metadata"], dict):
            md = item["metadata"].copy()
            # Merge top-level fields that might not be in nested metadata
            for key in ["repo_name", "repo_owner", "source", "type", "chunk_type"]:
                if key in item and key not in md:
                    md[key] = item[key]
        else:
            md = item.copy()

        md.pop("id", None)
        md.pop("metadata", None)
        md.pop("vector", None)  # Remove vector data from metadata

        # set canonical id field
        md["chunk_id"] = chunk_id
        flat_metadata.append(md)

    return flat_metadata, vectors


def build_faiss_index(vectors: np.ndarray):
    """FAISS L2 index"""
    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    return index


def save_index_and_metadata(index_name: str, index, metadata):
    """Save FAISS index with metadata in the new format"""
    from utils.metadata_normalizer import MetadataNormalizer
    
    index_dir = VECTORDB_ROOT / index_name
    index_dir.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(index_dir / "faiss.index"))

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

    with open(index_dir / "metadata.pkl", "wb") as f:
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
    with open(index_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(
        f"   ✓ Stored {index_name} → faiss.index + metadata.pkl + config.json ({len(metadata)} vectors)"
    )


def build_graph_structure():
    """
    Load graph_data.json and build a NetworkX graph object.
    """
    graph_file = PROCESSED_DATA_DIR / "graph_data.json"

    if not graph_file.exists():
        print(
            f"   ⚠️ No graph_data.json found at {graph_file}. Skipping Graph Structure."
        )
        return

    print(f"\n🕸️  Building NetworkX Graph Structure...")
    try:
        with open(graph_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        G = nx.DiGraph()

        for node in data.get("nodes", []):
            G.add_node(
                node["id"], **node.get("properties", {}), label=node.get("label")
            )

        for edge in data.get("edges", []):
            G.add_edge(edge["source"], edge["target"], type=edge.get("type"))

        output_path = VECTORDB_ROOT / "graph_structure.pkl"
        with open(output_path, "wb") as f:
            pickle.dump(G, f)

        print(
            f"   ✓ Graph Saved: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
        )
        print(f"   ✓ Location: {output_path}")

    except Exception as e:
        print(f"   ❌ Failed to build graph structure: {e}")


def main():
    skip_dirs = {"embeddings_cache"}

    # Check if embeddings directory exists
    if not EMBEDDINGS_DIR.exists():
        print(f"❌ Embeddings directory not found: {EMBEDDINGS_DIR}")
        print(f"\nPlease run the embedding generation step first:")
        print(f"   python main/GenerateEmbedding/generate_embedding.py")
        return

    # 🟢 FIX: Removed the .npy exists check here.
    # We will validate the file existence inside the loop.
    type_dirs = [
        d for d in EMBEDDINGS_DIR.iterdir() if d.is_dir() and d.name not in skip_dirs
    ]

    if not type_dirs:
        print("❌ No folders found in Embeddings/. Expected: Embeddings/<type>/<type>.npy")
        print(f"\nEmbeddings directory path: {EMBEDDINGS_DIR}")
        print(f"Contents: {list(EMBEDDINGS_DIR.iterdir()) if EMBEDDINGS_DIR.exists() else 'directory does not exist'}")
        return

    print(f"📦 Found {len(type_dirs)} embedding types:")
    for d in type_dirs:
        print("   •", d.name)

    print()

    built_indices = []
    all_metadata = []
    all_vectors = []

    for type_dir in type_dirs:
        folder_name = type_dir.name

        # 🟢 Handle 'graph' -> 'graph_nodes' mapping
        if folder_name == "graph":
            index_name = "graph_nodes"
            base_path = type_dir / "graph_nodes"
        else:
            index_name = folder_name
            base_path = type_dir / index_name

        print(f"🔹 Building index: {index_name}")

        # Check for existence here
        if (
            not base_path.with_suffix(".npy").exists()
            or not base_path.with_suffix(".json").exists()
        ):
            print(f"   ⚠️  Missing .npy or .json at {base_path} — skipping")
            continue

        try:
            metadata, vectors = load_embeddings(base_path)
            print(f"   Loaded {len(vectors)} vectors (dim: {vectors.shape[1]})")
            
            # CRITICAL: Filter metadata and vectors to only include current repo
            # Since embeddings are in repo-specific directory, assume they belong to current repo
            # if repo_name is missing or empty
            filtered_metadata = []
            filtered_indices = []
            skipped_count = 0
            fixed_count = 0
            
            # Import repo normalizer for flexible matching
            from utils.repo_normalizer import normalize_repo_name, normalize_repo_owner, repo_matches, extract_repo_parts
            
            # Normalize current repo info
            normalized_current_owner, normalized_current_repo = extract_repo_parts(FULL_REPO_NAME)
            if not normalized_current_owner:
                normalized_current_owner = normalize_repo_owner(REPO_OWNER)
            if not normalized_current_repo:
                normalized_current_repo = normalize_repo_name(REPO_NAME)
            
            for i, m in enumerate(metadata):
                # Get repo_name - check multiple possible locations
                chunk_repo_raw = m.get("repo_name") or m.get("repository") or m.get("repo") or None
                chunk_owner_raw = m.get("repo_owner") or m.get("owner") or None
                
                # If repo_name is empty/missing, assume it's for current repo (embeddings are in repo dir)
                # Since embeddings are in Embeddings/{REPO_OWNER}/{REPO_NAME}/, they belong to current repo
                if not chunk_repo_raw or str(chunk_repo_raw).strip() == "" or str(chunk_repo_raw).strip() == "None":
                    # Embeddings are in Embeddings/{REPO_OWNER}/{REPO_NAME}/, so assume current repo
                    m["repo_name"] = REPO_NAME
                    m["repo_owner"] = REPO_OWNER
                    filtered_metadata.append(m)
                    filtered_indices.append(i)
                    fixed_count += 1
                    continue
                
                # Normalize chunk repo info
                normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(chunk_repo_raw)
                if not normalized_chunk_owner and chunk_owner_raw:
                    normalized_chunk_owner = normalize_repo_owner(chunk_owner_raw)
                if not normalized_chunk_repo:
                    normalized_chunk_repo = normalize_repo_name(chunk_repo_raw)
                
                # FLEXIBLE matching: Use repo normalizer for format variations
                matches_repo = repo_matches(
                    normalized_current_owner, normalized_current_repo,
                    normalized_chunk_owner, normalized_chunk_repo
                )
                
                if matches_repo:
                    # Ensure repo_name is set correctly
                    m["repo_name"] = REPO_NAME
                    m["repo_owner"] = REPO_OWNER
                    filtered_metadata.append(m)
                    filtered_indices.append(i)
                else:
                    skipped_count += 1
                    if skipped_count <= 3:  # Print first 3 warnings
                        print(f"      ⚠️  Skipping chunk with repo: '{chunk_owner}/{chunk_repo}' (expected: '{REPO_OWNER}/{REPO_NAME}')")
            
            if fixed_count > 0:
                print(f"   ✓ Fixed repo_name for {fixed_count} embeddings (assumed current repo)")
                # Filter vectors to match filtered metadata
                vectors = vectors[filtered_indices]
                metadata = filtered_metadata
            
            if skipped_count > 0:
                print(f"   ⚠️  Filtered out {skipped_count} embeddings from other repositories")
                # Filter vectors to match filtered metadata (if not already filtered)
                if fixed_count == 0:
                    vectors = vectors[filtered_indices]
                    metadata = filtered_metadata
            
            if fixed_count > 0 or skipped_count > 0:
                print(f"   ✓ Using {len(metadata)} embeddings for {REPO_OWNER}/{REPO_NAME}")
            
            if len(metadata) == 0:
                print(f"   ⚠️  No embeddings found for current repo - skipping {index_name}")
                continue

            if index_name.lower() == "issue":
                for m in metadata:
                    if "issue_number" not in m:
                        entities = m.get("entities", {})
                        if (
                            isinstance(entities, dict)
                            and entities.get("issue_number") is not None
                        ):
                            try:
                                m["issue_number"] = int(entities["issue_number"])
                            except Exception:
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

        except Exception as e:
            print(f"   ❌ Failed to load embeddings: {e}")
            continue

        try:
            index = build_faiss_index(vectors)
        except Exception as e:
            print(f"   ❌ Failed to build FAISS index: {e}")
            continue

        save_index_and_metadata(index_name, index, metadata)
        built_indices.append(index_name)

        if index_name != "all" and index_name != "graph_nodes":
            for m in metadata:
                m["source_index"] = index_name
            all_metadata.extend(metadata)
            all_vectors.append(vectors)

    if all_vectors:
        print(f"\n🔹 Building combined 'all' index...")
        try:
            combined_vectors = np.vstack(all_vectors)
            all_index = build_faiss_index(combined_vectors)
            save_index_and_metadata("all", all_index, all_metadata)
            built_indices.append("all")
        except Exception as e:
            print(f"   ❌ Failed to build combined index: {e}")

    build_graph_structure()

    print(f"\n{'='*70}")
    print("🎉 Multi-Index VectorDB Build Complete!")
    print(f"{'='*70}")
    print(f"📁 Location: {VECTORDB_ROOT}")
    print(f"✅ Built {len(built_indices)} indices:")
    for idx in built_indices:
        print(f"   • {idx}")
    print()


if __name__ == "__main__":
    main()
