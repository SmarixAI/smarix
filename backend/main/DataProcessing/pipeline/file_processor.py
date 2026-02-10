import json
from typing import Dict, Any, Optional, Set
from ..chunking.base_chunker import DataChunker
from ..state.repo_state import REPO_OWNER, REPO_NAME
from .multi_source import process_multi_source_data

# Import S3Manager
from utils.s3 import s3_manager

# S3 config
S3_BUCKET = "smarix-data-apsouth1"


def process_file(
    input_data: Dict[str, Any],
    chunker: "DataChunker",
    git_entities: Optional[Dict[str, Set[str]]] = None,
) -> Dict[str, Any]:
    """
    Process JSON data (from S3), chunk with dual indexing, save to S3 (SPLIT BY TYPE)
    Only processes data for the current repo specified in runtime_state.json
    """
    print("=" * 70)
    print("ENTERPRISE-GRADE MULTI-SOURCE PROCESSING WITH GRAPH EXTRACTION")
    print("=" * 70)

    # Data already loaded from S3
    data = input_data
    print(f"Loading data from S3 (in-memory)")

    # Auto-detect source if not explicitly set
    source = data.get("source", "unknown")
    if source == "unknown":
        if "issues" in data or "prs" in data or "commits" in data:
            source = "git"
            print(f"   ℹ️  Auto-detected source as 'git' based on data content")
        elif "messages" in data:
            source = "gmail"
            print(f"   ℹ️  Auto-detected source as 'gmail' based on data content")

    repo_name = REPO_NAME
    repo_owner = REPO_OWNER

    print(f"Source: {source}")
    print(f"Processing for repo: {repo_owner}/{repo_name}")

    if source == "git":
        print(f"Issues: {len(data.get('issues', []))}")
        print(f"PRs: {len(data.get('prs', []))}")
        print(f"Commits: {len(data.get('commits', []))}")
        print(f"Code files: {len(data.get('code_files', []))}")
        print(f"Docs: {len(data.get('documentation', []))}")
    elif source == "gmail":
        total_messages = data.get("total_messages", len(data.get("messages", [])))
        messages_with_attachments = sum(
            1 for m in data.get("messages", []) if m.get("has_attachments")
        )
        print(f"Total messages: {total_messages}")
        print(f"Messages with attachments: {messages_with_attachments}")

    print("Processing...")
    chunks, entities, tech_stack = process_multi_source_data(
        data, repo_name, chunker, git_entities
    )

    # CRITICAL: Filter chunks to ensure they only belong to the current repo
    expected_repo_full = f"{repo_owner}/{repo_name}"
    filtered_chunks = []
    skipped_count = 0
    fixed_count = 0

    for chunk in chunks:
        chunk_repo = chunk.get("repo_name", "").strip()
        chunk_owner = chunk.get("repo_owner", "").strip()

        # Use flexible repo matching with normalizer
        from backend.utils.repo_normalizer import (
            repo_matches,
            normalize_repo_name,
            normalize_repo_owner,
            extract_repo_parts,
        )

        # Normalize current repo
        normalized_current_owner, normalized_current_repo = extract_repo_parts(
            expected_repo_full
        )
        if not normalized_current_owner:
            normalized_current_owner = normalize_repo_owner(repo_owner)
        if not normalized_current_repo:
            normalized_current_repo = normalize_repo_name(repo_name)

        # Normalize chunk repo
        if chunk_owner and chunk_repo:
            chunk_repo_full = f"{chunk_owner}/{chunk_repo}"
        else:
            chunk_repo_full = chunk_repo

        normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(
            chunk_repo_full
        )

        if not normalized_chunk_owner:
            normalized_chunk_owner = normalize_repo_owner(chunk_owner)

        if not normalized_chunk_repo:
            normalized_chunk_repo = normalize_repo_name(chunk_repo)

        # Use flexible matching
        matches_repo = repo_matches(
            normalized_current_owner,
            normalized_current_repo,
            normalized_chunk_owner,
            normalized_chunk_repo,
        )

        if matches_repo:
            if chunk.get("repo_name") != repo_name:
                chunk["repo_name"] = repo_name
                fixed_count += 1
            if chunk.get("repo_owner") != repo_owner:
                chunk["repo_owner"] = repo_owner
                fixed_count += 1
            filtered_chunks.append(chunk)
        else:
            skipped_count += 1
            if skipped_count <= 5:
                print(
                    f"   ⚠️  Skipping chunk with mismatched repo: '{chunk_owner}/{chunk_repo}' (expected: '{repo_owner}/{repo_name}')"
                )
                print(
                    f"      Chunk ID: {chunk.get('chunk_id', 'unknown')}, Type: {chunk.get('type', 'unknown')}"
                )

    if skipped_count > 0:
        print(f"   ⚠️  Filtered out {skipped_count} chunks from other repositories")
    if fixed_count > 0:
        print(f"   ✓ Fixed repo_name for {fixed_count} chunks")

    chunks = filtered_chunks

    processed_chunks = [c for c in chunks if not c.get("is_raw_data", False)]
    raw_chunks = [c for c in chunks if c.get("is_raw_data", False)]

    print(f"Total chunks (after filtering): {len(chunks)}")
    print(f" - Processed chunks: {len(processed_chunks)}")
    print(f" - Raw data references: {len(raw_chunks)}")

    print("\nSaving chunks split by type to S3...")

    # S3 output paths
    s3_output_prefix = f"DataProcessing/{repo_owner}/{repo_name}"

    # GROUP CHUNKS BY TYPE
    from collections import defaultdict

    chunks_by_type = defaultdict(list)

    for chunk in chunks:
        chunk_repo = chunk.get("repo_name", "")
        if chunk_repo != repo_name and chunk_repo != expected_repo_full:
            continue
        chunk_type = chunk.get("type", "unknown")
        chunks_by_type[chunk_type].append(chunk)

    saved_files = []

    # SAVE EACH TYPE TO S3
    for chunk_type, type_chunks in chunks_by_type.items():
        if not type_chunks:
            continue

        s3_key = f"{s3_output_prefix}/chunks/{chunk_type}_chunks.json"
        s3_manager.upload_json(type_chunks, s3_key, public_read=False)

        print(
            f"   Saved {len(type_chunks)} {chunk_type} chunks -> s3://{S3_BUCKET}/{s3_key}"
        )
        saved_files.append(s3_key)

    # ALSO SAVE COMBINED FILE
    combined_s3_key = f"{s3_output_prefix}/chunks/combined_chunks.json"
    s3_manager.upload_json(chunks, combined_s3_key, public_read=False)
    print(
        f"   Saved {len(chunks)} combined chunks -> s3://{S3_BUCKET}/{combined_s3_key}"
    )
    saved_files.append(combined_s3_key)

    # --- SAVE GRAPH DATA TO S3 ---
    graph_has_data = len(chunker.graph_extractor.nodes) > 0

    if source == "git" or graph_has_data:
        graph_data = chunker.graph_extractor.get_graph_data()
        graph_s3_key = f"{s3_output_prefix}/graph_data.json"

        s3_manager.upload_json(graph_data, graph_s3_key, public_read=False)

        print(
            f"   🕸️  Graph Data Saved: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges -> s3://{S3_BUCKET}/{graph_s3_key}"
        )
        saved_files.append(graph_s3_key)

    # Save entities to S3
    if entities and source == "git":
        entities_s3_key = f"{s3_output_prefix}/entities.json"
        entities_serializable = {k: list(v) for k, v in entities.items()}
        s3_manager.upload_json(
            entities_serializable, entities_s3_key, public_read=False
        )
        print(f"   Entities saved -> s3://{S3_BUCKET}/{entities_s3_key}")
        saved_files.append(entities_s3_key)

    # Save tech stack to S3
    if tech_stack and source == "git":
        techstack_s3_key = f"{s3_output_prefix}/techstack.json"

        from collections import Counter

        repo_key = f"{repo_owner}_{repo_name}" if repo_owner else repo_name

        all_languages = Counter(tech_stack.get("languages", {}).get("all", {}))
        all_frameworks = Counter()
        all_tools = Counter()

        for fw in tech_stack.get("frameworks", {}).get("detected", []):
            all_frameworks[fw] = 1

        for tool in tech_stack.get("tools", {}).get("detected", []):
            all_tools[tool] = 1

        formatted_tech_stack = {
            "repositories": {repo_key: tech_stack},
            "summary": {
                "total_repositories": 1,
                "languages": dict(all_languages),
                "frameworks": dict(all_frameworks),
                "tools": dict(all_tools),
                "total_code_lines": tech_stack.get("metrics", {}).get(
                    "total_code_lines", 0
                ),
                "total_functions": tech_stack.get("functions_and_classes", {}).get(
                    "total_functions", 0
                ),
                "total_classes": tech_stack.get("functions_and_classes", {}).get(
                    "total_classes", 0
                ),
            },
        }

        s3_manager.upload_json(
            formatted_tech_stack, techstack_s3_key, public_read=False
        )
        print(f"   ✅ Tech stack analysis saved -> s3://{S3_BUCKET}/{techstack_s3_key}")
        print(
            f"      - Languages: {len(tech_stack.get('languages', {}).get('all', {}))}"
        )
        print(
            f"      - Frameworks: {len(tech_stack.get('frameworks', {}).get('detected', []))}"
        )
        print(f"      - Tools: {len(tech_stack.get('tools', {}).get('detected', []))}")
        saved_files.append(techstack_s3_key)
    elif source == "git" and not tech_stack:
        print(f"   ⚠️  Warning: Tech stack is None or empty for git source.")
    elif tech_stack and source != "git":
        print(f"   ⚠️  Warning: Tech stack exists but source is '{source}' (not 'git').")

    # Save retrieval strategy to S3
    strategy = {
        "repository": {
            "owner": REPO_OWNER,
            "name": REPO_NAME,
            "full_name": f"{REPO_OWNER}/{REPO_NAME}",
            "url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}",
        },
        "source": source,
        "chatbot_flow": [
            "1. User query received",
            "2. Search repository overview for tech stack/metrics queries",
            "3. Search GitHub chunks (priority 0-2) using hybrid search (semantic + keyword)",
            "4. Extract entities from GitHub results (issues, PRs, authors, etc.)",
            "5. Search Gmail chunks using GitHub entities as correlation hints",
            "6. Merge and rank results based on relevance and correlation",
            "7. If insufficient results, fallback to raw data references (priority 4)",
            "8. Generate response using combined context with tech stack awareness",
        ],
        "retrieval_priorities": {
            "0": "Repository overview (tech stack, metrics, structure)",
            "1": "GitHub issues, PRs, docs, high-correlation emails",
            "2": "GitHub commits, code, Git-related emails",
            "3": "General emails, attachments",
            "4": "Raw data (fallback for edge cases)",
        },
        "chunk_counts": {
            "total": len(chunks),
            "processed": len(processed_chunks),
            "raw_references": len(raw_chunks),
            "by_type": {k: len(v) for k, v in chunks_by_type.items()},
        },
        "graph_stats": {
            "nodes_count": len(chunker.graph_extractor.nodes) if source == "git" else 0,
            "edges_count": len(chunker.graph_extractor.edges) if source == "git" else 0,
        },
        "correlation_strategy": "Entity-based linking (authors, issue/PR numbers, commits, file paths)",
        "edge_case_handling": "Raw data preserved for queries requiring full context",
        "techstack_integration": "Overview chunk contains comprehensive tech stack",
    }

    if tech_stack:
        strategy["techstack_summary"] = {
            "primary_language": tech_stack["languages"]["primary"],
            "total_languages": tech_stack["languages"]["count"],
            "frameworks_detected": len(tech_stack["frameworks"]["detected"]),
            "tools_detected": len(tech_stack["tools"]["detected"]),
            "total_files": tech_stack["metrics"]["total_files"],
            "total_code_lines": tech_stack["metrics"]["total_code_lines"],
            "total_functions": tech_stack["functions_and_classes"]["total_functions"],
            "total_classes": tech_stack["functions_and_classes"]["total_classes"],
        }

    if source == "gmail":
        git_related = [c for c in processed_chunks if c.get("is_git_related", False)]
        high_correlation = [
            c for c in processed_chunks if c.get("correlation_score", 0) >= 3
        ]
        strategy["chunk_counts"]["git_related_emails"] = len(git_related)
        strategy["chunk_counts"]["high_correlation_emails"] = len(high_correlation)

    strategy_s3_key = f"{s3_output_prefix}/retrieval_strategy.json"
    s3_manager.upload_json(strategy, strategy_s3_key, public_read=False)
    print(f"   Retrieval strategy saved -> s3://{S3_BUCKET}/{strategy_s3_key}")
    saved_files.append(strategy_s3_key)

    print("=" * 70)
    print("DONE")
    print("=" * 70)

    return {
        "output_files": saved_files,  # S3 keys
        "chunk_count": len(chunks),
        "processed_count": len(processed_chunks),
        "raw_count": len(raw_chunks),
        "repo_name": repo_name,
        "source": source,
        "entities": entities,
        "tech_stack": tech_stack,
    }
