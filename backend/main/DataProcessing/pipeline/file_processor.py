import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from chunking.base_chunker import DataChunker
from state.repo_state import REPO_OWNER, REPO_NAME

def process_file(
    input_file: str,
    output_dir: str,
    chunker: "DataChunker",
    git_entities: Optional[Dict[str, Set[str]]] = None,
) -> Dict[str, Any]:
    """
    Load JSON, Chunk with dual indexing, Save SPLIT BY TYPE
    Only processes data for the current repo specified in runtime_state.json
    """
    print("=" * 70)
    print("ENTERPRISE-GRADE MULTI-SOURCE PROCESSING WITH GRAPH EXTRACTION")
    print("=" * 70)

    # Validate input file path matches current repo
    input_path = Path(input_file).resolve()
    
    # Check if the file path matches the expected repo structure
    # Expected structure: .../DataCollectionFromGit/{owner}/{repo}/{repo}.json
    path_parts = list(input_path.parts)
    
    # Find DataCollectionFromGit in the path
    try:
        git_dir_idx = path_parts.index('DataCollectionFromGit')
        if git_dir_idx >= 0 and len(path_parts) >= git_dir_idx + 4:
            file_owner = path_parts[git_dir_idx + 1]
            file_repo = path_parts[git_dir_idx + 2]
            file_name = path_parts[git_dir_idx + 3]
            
            # Validate owner and repo match
            if file_owner != REPO_OWNER or file_repo != REPO_NAME:
                print(f"⚠️  WARNING: File path indicates different repo: {file_owner}/{file_repo}")
                print(f"   Expected: {REPO_OWNER}/{REPO_NAME}")
                print(f"   File: {input_file}")
                print(f"   Skipping this file to prevent cross-repo contamination")
                return {
                    'output_files': [],
                    'chunk_count': 0,
                    'processed_count': 0,
                    'raw_count': 0,
                    'repo_name': REPO_NAME,
                    'source': 'unknown',
                    'entities': {},
                    'techstack': None
                }
            
            # Also validate filename matches repo name
            if file_name != f"{REPO_NAME}.json":
                print(f"⚠️  WARNING: Filename mismatch: {file_name} (expected: {REPO_NAME}.json)")
    except (ValueError, IndexError):
        # If we can't parse the path structure, log a warning but continue
        # (some files might be in different locations)
        print(f"⚠️  WARNING: Could not validate file path structure for: {input_file}")
        print(f"   Proceeding with caution - will filter chunks by repo_name")

    print(f"Loading {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    repo_name = REPO_NAME
    repo_owner = REPO_OWNER
    source = data.get('source', 'unknown')
    
    # Auto-detect source if not explicitly set
    if source == 'unknown':
        if "issues" in data or "prs" in data or "commits" in data:
            source = 'git'
            print(f"   ℹ️  Auto-detected source as 'git' based on data content")
        elif "messages" in data:
            source = 'gmail'
            print(f"   ℹ️  Auto-detected source as 'gmail' based on data content")

    print(f"Source: {source}")
    print(f"File: {repo_name}")
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
    chunks, entities, tech_stack = process_multi_source_data(data, repo_name, chunker, git_entities)

    # CRITICAL: Filter chunks to ensure they only belong to the current repo
    # Also ensure all chunks have the correct repo_name set
    expected_repo_full = f"{repo_owner}/{repo_name}"
    filtered_chunks = []
    skipped_count = 0
    fixed_count = 0
    
    for chunk in chunks:
        chunk_repo = chunk.get('repo_name', '').strip()
        chunk_owner = chunk.get('repo_owner', '').strip()

        
        
        # FLEXIBLE matching: Use repo normalizer for format variations
        matches_repo = False
        
        # Check full format first: "owner/repo"
        # Use flexible repo matching with normalizer
        from utils.repo_normalizer import repo_matches, normalize_repo_name, normalize_repo_owner, extract_repo_parts
        
        # Normalize current repo
        normalized_current_owner, normalized_current_repo = extract_repo_parts(expected_repo_full)
        if not normalized_current_owner:
            normalized_current_owner = normalize_repo_owner(repo_owner)
        if not normalized_current_repo:
            normalized_current_repo = normalize_repo_name(repo_name)
        
        # Normalize chunk repo
        # Build chunk full name once
        if chunk_owner and chunk_repo:
            chunk_repo_full = f"{chunk_owner}/{chunk_repo}"
        else:
            chunk_repo_full = chunk_repo  # fallback

        normalized_chunk_owner, normalized_chunk_repo = extract_repo_parts(chunk_repo_full)

        if not normalized_chunk_owner:
            normalized_chunk_owner = normalize_repo_owner(chunk_owner)

        if not normalized_chunk_repo:
            normalized_chunk_repo = normalize_repo_name(chunk_repo)

        
        # Use flexible matching
        matches_repo = repo_matches(
            normalized_current_owner, normalized_current_repo,
            normalized_chunk_owner, normalized_chunk_repo
        )
        
        if matches_repo:
            # Ensure repo_name is set correctly (use just repo_name, not full format)
            if chunk.get('repo_name') != repo_name:
                chunk['repo_name'] = repo_name
                fixed_count += 1
            # Ensure repo_owner is set
            if chunk.get('repo_owner') != repo_owner:
                chunk['repo_owner'] = repo_owner
                fixed_count += 1
            filtered_chunks.append(chunk)
        else:
            skipped_count += 1
            if skipped_count <= 5:  # Only print first 5 warnings
                print(f"   ⚠️  Skipping chunk with mismatched repo: '{chunk_owner}/{chunk_repo}' (expected: '{repo_owner}/{repo_name}')")
                print(f"      Chunk ID: {chunk.get('chunk_id', 'unknown')}, Type: {chunk.get('type', 'unknown')}")
    
    if skipped_count > 0:
        print(f"   ⚠️  Filtered out {skipped_count} chunks from other repositories")
    if fixed_count > 0:
        print(f"   ✓ Fixed repo_name for {fixed_count} chunks")
    
    chunks = filtered_chunks  # Use filtered chunks from now on

    processed_chunks = [c for c in chunks if not c.get("is_raw_data", False)]
    raw_chunks = [c for c in chunks if c.get("is_raw_data", False)]

    print(f"Total chunks (after filtering): {len(chunks)}")
    print(f" - Processed chunks: {len(processed_chunks)}")
    print(f" - Raw data references: {len(raw_chunks)}")

    print("\nSaving chunks split by type...")

    # Create repo-specific directory
    repo_output_dir = Path(output_dir) / repo_owner / repo_name
    repo_output_dir.mkdir(parents=True, exist_ok=True)

    # Optional subfolders
    chunks_dir = repo_output_dir / "chunks"
    chunks_dir.mkdir(exist_ok=True)

    # GROUP CHUNKS BY TYPE
    from collections import defaultdict

    chunks_by_type = defaultdict(list)

    for chunk in chunks:
        # Double-check repo_name before grouping
        chunk_repo = chunk.get('repo_name', '')
        if chunk_repo != repo_name and chunk_repo != expected_repo_full:
            continue  # Skip chunks that don't match
        chunk_type = chunk.get('type', 'unknown')
        chunks_by_type[chunk_type].append(chunk)

    saved_files = []

    # SAVE EACH TYPE TO ITS OWN FILE
    for chunk_type, type_chunks in chunks_by_type.items():
        if not type_chunks:
            continue

        output_file = chunks_dir / f"{chunk_type}_chunks.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(type_chunks, f, indent=2, ensure_ascii=False)

        print(
            f"   Saved {len(type_chunks)} {chunk_type} chunks -> {Path(output_file).name}"
        )
        saved_files.append(output_file)

    # ALSO SAVE COMBINED FILE (optional, for backward compatibility)
    combined_file = chunks_dir / "combined_chunks.json"
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"   Saved {len(chunks)} combined chunks -> {Path(combined_file).name}")
    saved_files.append(combined_file)

    # --- NEW: SAVE GRAPH DATA ---
    graph_has_data = len(chunker.graph_extractor.nodes) > 0

    if source == "git" or graph_has_data:
        # Extract graph data from the chunker's state
        graph_data = chunker.graph_extractor.get_graph_data()
        graph_file = repo_output_dir / "graph_data.json"

        with open(graph_file, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        print(
            f"   🕸️  Graph Data Saved: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges -> {graph_file.name}"
        )
        saved_files.append(graph_file)
    # ----------------------------

    # Save entities
    if entities and source == "git":
        entities_file = repo_output_dir / "entities.json"
        entities_serializable = {k: list(v) for k, v in entities.items()}
        with open(entities_file, "w", encoding="utf-8") as f:
            json.dump(entities_serializable, f, indent=2, ensure_ascii=False)
        print(f"   Entities saved: {entities_file}")

    # Save tech stack
    if tech_stack and source == "git":
        techstack_file = repo_output_dir / "techstack.json"
        
        # Format tech stack data with repositories and summary structure
        from collections import Counter
        
        # Create repository key (use repo_name or owner/repo_name format)
        repo_key = f"{repo_owner}_{repo_name}" if repo_owner else repo_name
        
        # Aggregate summary data
        all_languages = Counter(tech_stack.get("languages", {}).get("all", {}))
        all_frameworks = Counter()
        all_tools = Counter()
        
        # Count frameworks
        for fw in tech_stack.get("frameworks", {}).get("detected", []):
            all_frameworks[fw] = 1
        
        # Count tools
        for tool in tech_stack.get("tools", {}).get("detected", []):
            all_tools[tool] = 1
        
        # Build the formatted tech stack structure
        formatted_tech_stack = {
            "repositories": {
                repo_key: tech_stack
            },
            "summary": {
                "total_repositories": 1,
                "languages": dict(all_languages),
                "frameworks": dict(all_frameworks),
                "tools": dict(all_tools),
                "total_code_lines": tech_stack.get("metrics", {}).get("total_code_lines", 0),
                "total_functions": tech_stack.get("functions_and_classes", {}).get("total_functions", 0),
                "total_classes": tech_stack.get("functions_and_classes", {}).get("total_classes", 0)
            }
        }
        
        with open(techstack_file, 'w', encoding='utf-8') as f:
            json.dump(formatted_tech_stack, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Tech stack analysis saved: {techstack_file}")
        print(f"      - Languages: {len(tech_stack.get('languages', {}).get('all', {}))}")
        print(f"      - Frameworks: {len(tech_stack.get('frameworks', {}).get('detected', []))}")
        print(f"      - Tools: {len(tech_stack.get('tools', {}).get('detected', []))}")
    elif source == 'git' and not tech_stack:
        print(f"   ⚠️  Warning: Tech stack is None or empty for git source. Skipping techstack.json generation.")
        print(f"      This may indicate no code files were analyzed.")
    elif tech_stack and source != 'git':
        print(f"   ⚠️  Warning: Tech stack exists but source is '{source}' (not 'git'). Skipping techstack.json generation.")

    # Save retrieval strategy
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
        "edge_case_handling": "Raw data preserved for queries requiring full context or missing from processed chunks",
        "techstack_integration": "Overview chunk contains comprehensive tech stack, code metrics, and structure analysis",
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

    strategy_file = repo_output_dir / "retrieval_strategy.json"
    with open(strategy_file, "w", encoding="utf-8") as f:
        json.dump(strategy, f, indent=2, ensure_ascii=False)
    print(f"   Retrieval strategy: {strategy_file}")

    print("=" * 70)
    print("DONE")
    print("=" * 70)

    return {
        "output_files": saved_files,
        "chunk_count": len(chunks),
        "processed_count": len(processed_chunks),
        "raw_count": len(raw_chunks),
        "repo_name": repo_name,
        "source": source,
        "entities": entities,
        "techstack": tech_stack,
    }

