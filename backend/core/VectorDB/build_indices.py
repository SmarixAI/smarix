"""
Build Multi-Index VectorDB (Step 4)
Creates ONE folder per embedding type inside: data/VectorDB/{owner}/{repo_name}/<type>
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
import networkx as nx
from collections import defaultdict
import re


STATE_FILE = Path(
    Path(__file__).resolve().parents[2]
    / "data"
    / "Admin"
    / "state"
    / "runtime_state.json"
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
PROCESSED_DATA_DIR = Path("../../data/DataProcessing") / REPO_OWNER / REPO_NAME

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
        else:
            md = item.copy()

        md.pop("id", None)
        md.pop("metadata", None)
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

    faiss.write_index(index, str(index_dir / "faiss.index"))

    for m in metadata:
        m["chunk_type"] = m.get("chunk_type") or m.get("type")
        m["file_path"] = m.get("file_path") or m.get("path") or m.get("repo_file_path")
        m["repo_name"] = (
            m.get("repo_name") or m.get("repository") or m.get("repo") or REPO_NAME
        )
        m["language"] = m.get("language") or m.get("entities", {}).get("language")
        m["pr_number"] = m.get("pr_number") or m.get("metadata", {}).get("pr_number")
        m["issue_number"] = m.get("issue_number") or m.get("metadata", {}).get(
            "issue_number"
        )

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

    # 🟢 FIX: Removed the .npy exists check here.
    # We will validate the file existence inside the loop.
    type_dirs = [
        d for d in EMBEDDINGS_DIR.iterdir() if d.is_dir() and d.name not in skip_dirs
    ]

    if not type_dirs:
        print("❌ No folders found in Embeddings/")
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
            print(f"   Loaded {len(vectors)} vectors")

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
