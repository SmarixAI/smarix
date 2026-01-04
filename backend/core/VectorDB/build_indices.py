"""
Build Multi-Index VectorDB (Step 4)
Creates ONE folder per embedding type inside: data/VectorDB/multi_index/<type>
Each folder contains:
   - faiss.index
   - metadata.pkl
   - config.json
"""

import os
import json
import numpy as np
from pathlib import Path
import faiss
import pickle
from collections import defaultdict
import re


STATE_FILE = Path(
    "/Users/vishalkeshari/Desktop/smarix/backend/data/Admin/state/runtime_state.json"
)

def load_current_repo_from_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = json.load(f)

    curr_repo = state.get("curr_repo")
    if not curr_repo:
        raise RuntimeError("curr_repo missing in runtime_state.json")

    return curr_repo["owner"], curr_repo["name"]

REPO_OWNER, REPO_NAME = load_current_repo_from_state()

EMBEDDINGS_DIR = Path("../../data/Embeddings") / REPO_OWNER / REPO_NAME
VECTORDB_ROOT = Path("../../data/VectorDB") / REPO_OWNER / REPO_NAME

VECTORDB_ROOT.mkdir(parents=True, exist_ok=True)






def load_embeddings(base_path: Path):
    """
    Load vectors + metadata and convert to FLAT legacy format used by chatbot.
    Fixed: Handles flat list format used by your embedding generator.
    """
    npy_path = base_path.with_suffix(".npy")
    json_path = base_path.with_suffix(".json")

    if not npy_path.exists() or not json_path.exists():
        raise FileNotFoundError(f"Missing .npy or .json files at {base_path}")

    vectors = np.load(npy_path).astype("float32")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 🔥 FIXED: Handle your actual JSON format (flat list of dicts)
    if isinstance(data, list):
        items = data
    # Case A — ChatGPT format: {"items": [...]}
    elif isinstance(data, dict) and "items" in data:
        items = data["items"]
    # Case B — OpenAI/local format: {"embeddings": [...], "metadata": [...]}
    elif isinstance(data, dict) and "metadata" in data and isinstance(data["metadata"], list):
        items = data["metadata"]
    else:
        # Debug info
        print(f"DEBUG JSON structure for {base_path}:")
        print(f"  Type: {type(data)}")
        if isinstance(data, dict):
            print(f"  Keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"  List length: {len(data)}")
            if data:
                print(f"  First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'not dict'}")
        raise ValueError("Embedding JSON missing metadata or items field")

    if len(items) != len(vectors):
        raise ValueError(f"❌ Mismatch: {len(vectors)} vectors vs {len(items)} metadata records")

    # 🔥 convert into FLAT format expected by MultiIndexVectorStore
    flat_metadata = []
    for i, item in enumerate(items):
        # get id
        chunk_id = item.get("chunk_id") or item.get("id") or str(i)

        # nested metadata case: {"id":..., "metadata":{...}}
        if "metadata" in item and isinstance(item["metadata"], dict):
            md = item["metadata"].copy()
        else:
            md = item.copy()

        # remove nested keys that should not exist
        md.pop("id", None)
        md.pop("metadata", None)

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
    index_dir = VECTORDB_ROOT / index_name
    index_dir.mkdir(parents=True, exist_ok=True)

    # --- Save FAISS index ---
    faiss.write_index(index, str(index_dir / "faiss.index"))

    # --- Save metadata in .pkl (new format: dict with config) ---
    # ---- ENRICH metadata before saving ----
    for m in metadata:
        m["chunk_type"] = m.get("chunk_type") or m.get("type")
        m["file_path"] = m.get("file_path") or m.get("path") or m.get("repo_file_path")
        m["repo_name"] = m.get("repo_name") or m.get("repository") or m.get("repo")
        m["language"] = m.get("language") or m.get("entities", {}).get("language")
        m["pr_number"] = m.get("pr_number") or m.get("metadata", {}).get("pr_number")
        m["issue_number"] = m.get("issue_number") or m.get("metadata", {}).get("issue_number")

    with open(index_dir / "metadata.pkl", "wb") as f:
        pickle.dump({
            'metadata': metadata,
            'chunk_ids': [m.get('chunk_id', str(i)) for i, m in enumerate(metadata)],
            'dimension': index.d,
            'index_type': 'flat',
            'metric': 'l2'
        }, f)

    # --- Save config ---
    config = {
        "index_name": index_name,
        "dimension": index.d,
        "vector_dimension": index.d,
        "index_type": "flat",
        "metric": "l2",
        "total_records": len(metadata),
        "index_file": "faiss.index",
        "metadata_file": "metadata.pkl"
    }
    with open(index_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"   ✓ Stored {index_name} → faiss.index + metadata.pkl + config.json ({len(metadata)} vectors)")


def main():
    """
    Build indices from type-specific embedding files.
    Expects: Embeddings/<type>/<type>.npy + <type>.json
    """

    # Skip cache directories
    skip_dirs = {"embeddings_cache"}

    # List subfolders inside Embeddings directory
    type_dirs = [
        d for d in EMBEDDINGS_DIR.iterdir()
        if d.is_dir() and (d / f"{d.name}.npy").exists()
    ]

    if not type_dirs:
        print("❌ No folders found in Embeddings/. Expected: Embeddings/<type>/<type>.npy")
        return

    print(f"📦 Found {len(type_dirs)} embedding types:")
    for d in type_dirs:
        print("   •", d.name)

    print()

    # Track successful builds
    built_indices = []
    all_metadata = []
    all_vectors = []

    for type_dir in type_dirs:
        index_name = type_dir.name
        base_path = type_dir / index_name   # e.g., code/code.npy + code/code.json

        print(f"🔹 Building index: {index_name}")

        if not base_path.with_suffix(".npy").exists() or not base_path.with_suffix(".json").exists():
            print(f"   ⚠️  Missing .npy or .json — skipping {index_name}")
            continue

        try:
            metadata, vectors = load_embeddings(base_path)
            print(f"   Loaded {len(vectors)} vectors (dim: {vectors.shape[1]})")

            # --------------------------------------------
            # ENRICH METADATA FOR ISSUE INDEX
            # --------------------------------------------
            if index_name.lower() == "issue":
                for m in metadata:
                    # 1) Prefer top-level issue_number if already present
                    if "issue_number" not in m:
                        # 2) Try to pull from nested entities
                        entities = m.get("entities", {})
                        if isinstance(entities, dict) and entities.get("issue_number") is not None:
                            try:
                                m["issue_number"] = int(entities["issue_number"])
                            except Exception:
                                m["issue_number"] = str(entities["issue_number"])

                    # 3) Fallback: parse from content text
                    content = m.get("content", "") or ""
                    if content and "issue_number" not in m:
                        match = re.search(r'issue\s*#\s*(\d+)', content, re.IGNORECASE)
                        if match:
                            m["issue_number"] = int(match.group(1))

                    # 4) Title extraction
                    if content:
                        lines = content.split("\n")
                        for line in lines:
                            line = line.strip()
                            if line.lower().startswith("issue:"):
                                m["title"] = line.replace("Issue:", "").strip()
                                break

                    m["chunk_type"] = "issue"
                    m["type"] = "issue"

                # Debug issue_number presence
                print("\n   🔍 DEBUG — Checking issue_number values for ISSUE index")
                missing = [m.get("chunk_id", "UNKNOWN_ID") for m in metadata if "issue_number" not in m]
                print(f"   ➤ Total issue chunks: {len(metadata)}")
                print(f"   ➤ Missing issue_number: {len(missing)}")

            # --------------------------------------------
            # ENRICH METADATA FOR PR INDEX
            # --------------------------------------------
            if index_name.lower() == "pr":
                for m in metadata:
                    content = m.get("content", "") or ""

                    # PR number
                    match = re.search(r'pr\s*#(\d+)', content, re.IGNORECASE)
                    if match:
                        m["pr_number"] = int(match.group(1))

                    # title
                    lines = content.split("\n")
                    for line in lines:
                        line = line.strip()
                        if line.lower().startswith("pull request:"):
                            m["title"] = line.replace("Pull Request:", "").strip()
                            break

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

        # Save type-specific index
        save_index_and_metadata(index_name, index, metadata)

        built_indices.append(index_name)

        # Collect for "all" index
        if index_name != "all":
            for m in metadata:
                m['source_index'] = index_name

            all_metadata.extend(metadata)
            all_vectors.append(vectors)

    # Build combined "all" index
    if all_vectors:
        print(f"\n🔹 Building combined 'all' index...")

        try:
            combined_vectors = np.vstack(all_vectors)
            print(f"   Combined {len(combined_vectors)} vectors from {len(built_indices)} types")

            all_index = build_faiss_index(combined_vectors)
            save_index_and_metadata("all", all_index, all_metadata)

            built_indices.append("all")

        except Exception as e:
            print(f"   ❌ Failed to build combined index: {e}")

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
