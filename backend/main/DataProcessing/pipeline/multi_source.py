from typing import Dict, Any, List, Optional, Set, Tuple
from chunking.base_chunker import DataChunker
from state.repo_state import REPO_OWNER


def process_multi_source_data(
    data: Dict[str, Any],
    repo_name: str,
    chunker: DataChunker,
    git_entities: Optional[Dict[str, Set[str]]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Set[str]], Optional[Dict[str, Any]]]:
    """
    Process data with intelligent chunking, correlation, and code analysis.
    Returns:
      - all_chunks
      - extracted_entities (git only)
      - tech_stack (git only)
    """

    all_chunks: List[Dict[str, Any]] = []
    entities: Dict[str, Set[str]] = {}
    tech_stack: Optional[Dict[str, Any]] = None

    source = data.get("source", "unknown")

    # --------------------------------------------------
    # Git source
    # --------------------------------------------------
    if source == "git":
        print("   📂 Processing Git data...")

        processed_chunks, entities, tech_stack = chunker.chunk_git_data(
            data, repo_name
        )
        all_chunks.extend(processed_chunks)

        # Raw fallback reference (edge-case safety)
        raw_reference = chunker.create_raw_data_reference(
            data=data,
            source="git",
            repo_name=repo_name,
            repo_owner=REPO_OWNER,
        )
        all_chunks.append(raw_reference)

        print(f"      ✓ Processed chunks: {len(processed_chunks)}")
        print(
            f"      ✓ Extracted entities: {sum(len(v) for v in entities.values())}"
        )
        print("      ✓ Raw reference added")

    # --------------------------------------------------
    # Gmail source
    # --------------------------------------------------
    elif source == "gmail":
        print("   📧 Processing Gmail data...")

        if git_entities:
            print(
                f"      ℹ️  Using {sum(len(v) for v in git_entities.values())} Git entities for correlation"
            )

        processed_chunks = chunker.chunk_gmail_data(
            data, repo_name, git_entities or {}
        )
        all_chunks.extend(processed_chunks)

        raw_reference = chunker.create_raw_data_reference(
            data=data,
            source="gmail",
            repo_name=repo_name,
            repo_owner=REPO_OWNER,
        )
        all_chunks.append(raw_reference)

        git_related = [c for c in processed_chunks if c.get("is_git_related")]
        high_correlation = [
            c for c in processed_chunks if c.get("correlation_score", 0) >= 3
        ]

        print(f"      ✓ Processed chunks: {len(processed_chunks)}")
        print(f"      ✓ Git-related emails: {len(git_related)}")
        print(f"      ✓ High-correlation emails: {len(high_correlation)}")
        print("      ✓ Raw reference added")

    # --------------------------------------------------
    # Auto-detect fallback (mixed or legacy data)
    # --------------------------------------------------
    else:
        if any(k in data for k in ("issues", "prs", "commits", "code_files")):
            print("   📂 Processing Git data (auto-detected)...")

            git_chunks, entities, tech_stack = chunker.chunk_git_data(
                data, repo_name
            )
            all_chunks.extend(git_chunks)

            all_chunks.append(
                chunker.create_raw_data_reference(
                    data=data,
                    source="git",
                    repo_name=repo_name,
                    repo_owner=REPO_OWNER,
                )
            )

        if "messages" in data:
            print("   📧 Processing Gmail data (auto-detected)...")

            mail_chunks = chunker.chunk_gmail_data(
                data, repo_name, git_entities or {}
            )
            all_chunks.extend(mail_chunks)

            all_chunks.append(
                chunker.create_raw_data_reference(
                    data=data,
                    source="gmail",
                    repo_name=repo_name,
                    repo_owner=REPO_OWNER,
                )
            )

    return all_chunks, entities, tech_stack
