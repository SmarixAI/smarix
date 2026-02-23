from typing import Dict, Any, Tuple, List
import json
import re
import sys
from pathlib import Path

# Handle both relative and absolute imports
try:
    from ..formatters.entity_context import format_entity_context
    from ..formatters.temporal_context import format_temporal_context
    from ..formatters.correlation_context import format_correlation_context
    from ..extractors.content_extractor import extract_main_content
    from ..extractors.code_structure_extractor import extract_code_structure
    from ..config.state import load_current_repo_from_state
except ImportError:
    workspace_root = Path(__file__).resolve().parents[4]
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))
    from backend.main.GenerateEmbedding.formatters.entity_context import format_entity_context
    from backend.main.GenerateEmbedding.formatters.temporal_context import format_temporal_context
    from backend.main.GenerateEmbedding.formatters.correlation_context import format_correlation_context
    from backend.main.GenerateEmbedding.extractors.content_extractor import extract_main_content
    from backend.main.GenerateEmbedding.extractors.code_structure_extractor import extract_code_structure
    from backend.main.GenerateEmbedding.config.state import load_current_repo_from_state

REPO_OWNER, REPO_NAME = load_current_repo_from_state()


def prepare_enhanced_chunk_for_embedding(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare chunk for embedding with ALL metadata fields properly extracted.
    Ensures merged PRs, reviews, comments & patches are captured, and metadata is
    flattened for enriched-text embeddings.
    """
    chunk_id = chunk.get("chunk_id", "unknown")
    chunk_type = chunk.get("chunk_type") or chunk.get("type") or "unknown"
    source = chunk.get("source", "unknown")

    # 🔥 AUTO-EXTRACT file path, filename, directory & language from content
    raw_content = chunk.get("content", "")
    content_text = ""
    if isinstance(raw_content, dict):
        for candidate in ("content", "body", "snippet", "text", "code", "raw"):
            if raw_content.get(candidate):
                content_text = raw_content.get(candidate)
                break
        if not content_text:
            try:
                content_text = json.dumps(raw_content)
            except Exception:
                content_text = ""
    elif isinstance(raw_content, str):
        content_text = raw_content

    if content_text:
        m_path = re.search(r"(?:Path|file|File):\s*([^\n]+)", content_text, flags=re.IGNORECASE)
        if m_path:
            extracted_path = m_path.group(1).strip().strip('`')
            chunk.setdefault("entities", {})["path"] = extracted_path
            chunk["file_path"] = extracted_path
            try:
                p = Path(extracted_path)
                fname = p.name
                fdir = str(p.parent) if str(p.parent) not in (".", "") else ""
                chunk.setdefault("entities", {})["filename"] = fname
                chunk.setdefault("entities", {})["directory"] = fdir
            except Exception:
                pass

        m_lang = re.search(r"Language:\s*([^\n]+)", content_text, flags=re.IGNORECASE)
        if m_lang:
            lang_val = m_lang.group(1).strip().lower()
            chunk.setdefault("entities", {})["language"] = lang_val
            chunk["language"] = lang_val
        else:
            ep = chunk.setdefault("entities", {}).get("path") or chunk.get("file_path")
            if ep and not chunk.get("language") and ep.count('.'):
                try:
                    inferred = Path(ep).suffix.lstrip('.').lower()
                    if inferred:
                        chunk.setdefault("entities", {})["language"] = inferred
                        chunk["language"] = inferred
                except Exception:
                    pass

    entities = chunk.get("entities") or {}
    content = chunk.get("content", {})
    if isinstance(content, str):
        content = {"body": content}

    raw_data = chunk.get("raw_data", {})
    if isinstance(raw_data, str):
        raw_data = {}

    temporal = chunk.get("temporal") or {}

    # --- Correct merged detection ---
    is_actually_merged = bool(
        temporal.get("merged_at") or
        content.get("merged") or
        raw_data.get("is_merged") or
        raw_data.get("merged_at")
    )
    if is_actually_merged and not entities.get("is_merged"):
        entities["is_merged"] = True

    state = content.get("state") or raw_data.get("state")
    pr_status = entities.get("pr_status")
    if chunk_type == "pr" and is_actually_merged and pr_status != "merged":
        entities["pr_status"] = "merged"
        state = "closed"

    # --- Ensure file_changes, reviews & comments ---
    file_changes = chunk.get("file_changes") or raw_data.get("changed_files") or []
    chunk["file_changes"] = file_changes
    has_patches = any(fc.get("patch") for fc in file_changes if isinstance(fc, dict))

    reviews = chunk.get("reviews") or raw_data.get("reviews") or []
    chunk["reviews"] = reviews

    comments = chunk.get("comments") or raw_data.get("comments") or []
    chunk["comments"] = comments

    # --- Extract full final content (with patches & reviews) ---
    main_content = extract_main_content(chunk)
    if not main_content.strip():
        print(f"⚠ Warning: Empty content for chunk {chunk_id} (type={chunk_type})")
        return {
            "chunk_id": chunk_id,
            "type": chunk_type,
            "source": source,
            "content": "",
            "metadata": chunk,
            "skip_embedding": True,
        }

    # --- Build contextual prefix (entity / temporal / correlation) ---
    context_parts = []
    entity_context = format_entity_context(entities, chunk_type)
    if entity_context:
        context_parts.append(entity_context)
    temporal_context = format_temporal_context(temporal)
    if temporal_context:
        context_parts.append(temporal_context)
    correlation_context = format_correlation_context(chunk)
    if correlation_context:
        context_parts.append(correlation_context)

    final_content = f"{' | '.join(context_parts)}\n\n{main_content}" if context_parts else main_content

    # --- Derive file path/filename/directory/language for metadata ---
    from backend.utils.path_normalizer import normalize_path, extract_filename, extract_directory

    file_path_raw = entities.get('path') or chunk.get('path') or chunk.get('repo_file_path') or chunk.get('file_path')
    file_path_val = normalize_path(file_path_raw, '') if file_path_raw else ''
    derived_filename = None
    derived_directory = None
    if file_path_val:
        derived_filename = extract_filename(file_path_val) or ''
        derived_directory = extract_directory(file_path_val) or ''

    # ── NEW: Extract code structure for code chunks ──────────────────────────
    # Only runs for code chunks — zero cost for pr/issue/commit chunks
    code_structure = {
        "code_chunk_type": None,
        "function_name":   None,
        "class_name":      None,
        "has_docstring":   False,
    }
    if chunk_type == "code":
        resolved_lang = (
            entities.get("language")
            or chunk.get("language")
            or (Path(file_path_val).suffix.lstrip('.').lower() if file_path_val else None)
        )
        code_structure = extract_code_structure(content_text, resolved_lang)
    # ─────────────────────────────────────────────────────────────────────────

    # --- Metadata object used in RAG + vector DB ---
    chunk_repo = chunk.get("repo_name", "").strip()
    if not chunk_repo or chunk_repo != REPO_NAME:
        chunk_repo = REPO_NAME

    storage_metadata = {
        "chunk_id": chunk_id,
        "chunk_type": chunk_type,
        "type": chunk_type,
        "source": source,
        "repo_name": chunk_repo,
        "repo_owner": REPO_OWNER,
        "file_path": file_path_val,
        "language": entities.get("language") or chunk.get("language"),
        "filename": entities.get("filename") or derived_filename,
        "directory": entities.get("directory") or derived_directory,
        "retrieval_priority": chunk.get("retrieval_priority", 3),

        # ── NEW: Code structure fields (None for non-code chunks) ──
        "code_chunk_type": code_structure["code_chunk_type"],  # function|class|module|other
        "function_name":   code_structure["function_name"],
        "class_name":      code_structure["class_name"],
        "has_docstring":   code_structure["has_docstring"],
        "start_line":      chunk.get("start_line"),            # pass-through if chunker provides it
        "end_line":        chunk.get("end_line"),              # pass-through if chunker provides it
        # ──────────────────────────────────────────────────────────

        # Entity metadata
        "issue_number": entities.get("issue_number"),
        "pr_number": entities.get("pr_number"),
        "author": entities.get("author"),
        "reviewers": entities.get("reviewers"),
        "assignees": entities.get("assignees"),

        # PR metadata
        "state": state,
        "is_merged": is_actually_merged,
        "merged_by": entities.get("merged_by"),
        "base_branch": entities.get("base_branch"),
        "head_branch": entities.get("head_branch"),
        "pr_status": entities.get("pr_status"),

        # Issue metadata
        "is_truly_resolved": entities.get("is_truly_resolved", False),
        "resolution_status": entities.get("resolution_status"),
        "linked_prs": entities.get("linked_prs"),
        "linked_issues": entities.get("linked_issues"),

        # Temporal metadata
        "created_at": temporal.get("created_at"),
        "updated_at": temporal.get("updated_at"),
        "merged_at": temporal.get("merged_at"),
        "closed_at": temporal.get("closed_at"),

        # Stats & flags
        "has_comments": len(comments) > 0,
        "comment_count": len(comments),
        "has_reviews": len(reviews) > 0,
        "review_count": len(reviews),
        "has_file_changes": len(file_changes) > 0,
        "file_change_count": len(file_changes),
        "has_patches": has_patches,

        "additions": content.get("additions", 0),
        "deletions": content.get("deletions", 0),
        "changed_files_count": content.get("changed_files_count", 0),
        "commits_count": content.get("commits_count", 0),

        "is_git_related": chunk.get("is_git_related", False),
        "correlation_score": chunk.get("correlation_score", 0),
    }

    # Auto extract PR/Issue number from body if missing
    if chunk_type == "issue" and not storage_metadata.get("issue_number"):
        m = re.search(r"#(\d+)", final_content)
        if m:
            storage_metadata["issue_number"] = int(m.group(1))
    if chunk_type == "pr" and not storage_metadata.get("pr_number"):
        m = re.search(r"#(\d+)", final_content)
        if m:
            storage_metadata["pr_number"] = int(m.group(1))

    prepared = {
        "chunk_id": chunk_id,
        "type": chunk_type,
        "source": source,
        "content": final_content,
        "metadata": storage_metadata,
        "full_chunk": chunk,
        "skip_embedding": False,
    }

    # Promote file_path & language to top-level for retriever
    prepared["file_path"] = prepared["metadata"].get("file_path")
    prepared["language"] = prepared["metadata"].get("language")

    # --- TOP-LEVEL promotion (for EmbeddingGenerator._create_enriched_text) ---
    for field in [
        "chunk_type", "category", "importance_score", "file_path",
        "function_name", "class_name", "semantic_tags", "keywords",
        "language", "repo_name", "repo_owner", "source", "type", "retrieval_priority",
        # ── NEW fields also promoted to top-level ──
        "code_chunk_type", "has_docstring", "start_line", "end_line",
    ]:
        if field in chunk:
            prepared[field] = chunk[field]
        if field in storage_metadata:
            prepared[field] = storage_metadata[field]

    return prepared
