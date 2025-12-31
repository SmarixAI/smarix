def convert_raw_to_chunks(raw_chunk):
    """
    Converts one raw_data_reference chunk into multiple atomic chunks
    (code, issues, PRs, commits, docs). This guarantees chatbot full visibility.
    """
    raw = raw_chunk.get("raw_data", {})
    repo = raw_chunk.get("metadata", {}).get("source", "unknown_repo")

    new_chunks = []

    # ------------------ CODE FILES ------------------
    files = raw.get("files") or raw.get("file_contents") or []
    for f in files[:5000]:  # prevent runaway
        if not isinstance(f, dict):
            continue
        filename = f.get("filename") or f.get("path")
        content = f.get("content")
        if not filename or not content:
            continue

        new_chunks.append({
            "chunk_id": f"raw_code::{filename}",
            "type": "code",
            "source": repo,
            "content": {"content": content},
            "entities": {"path": filename}
        })

    # ------------------ ISSUES ------------------
    issues = raw.get("issues") or raw.get("all_issues")
    if isinstance(issues, list):
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            body = issue.get("body") or ""
            title = issue.get("title") or ""
            new_chunks.append({
                "chunk_id": f"raw_issue::{issue.get('number')}",
                "type": "issue",
                "source": repo,
                "content": {"title": title, "body": body},
                "entities": {"issue_number": issue.get("number")}
            })

    # ------------------ PRs ------------------
    prs = raw.get("prs") or raw.get("all_prs")
    if isinstance(prs, list):
        for pr in prs:
            if not isinstance(pr, dict):
                continue
            new_chunks.append({
                "chunk_id": f"raw_pr::{pr.get('number')}",
                "type": "pr",
                "source": repo,
                "content": {"title": pr.get("title"), "body": pr.get("body")},
                "entities": {"pr_number": pr.get("number")}
            })

    # ------------------ COMMITS ------------------
    commits = raw.get("commits") or raw.get("all_commits")
    for c in commits[:5000] if isinstance(commits, list) else []:
        if not isinstance(c, dict):
            continue
        msg = c.get("message")
        sha = c.get("sha")
        if not msg or not sha:
            continue
        new_chunks.append({
            "chunk_id": f"raw_commit::{sha[:8]}",
            "type": "commit",
            "source": repo,
            "content": {"message": msg},
            "entities": {"sha_short": sha[:8]}
        })

    return new_chunks
