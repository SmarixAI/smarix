from typing import Dict, Any

def format_correlation_context(chunk: Dict[str, Any]) -> str:
    if not chunk.get('is_git_related'):
        return ""
    correlated = chunk.get('correlated_entities', {})
    parts = []
    if correlated.get('issue_numbers'):
        issues = correlated['issue_numbers'][:3]
        parts.append(f"related to issues: {', '.join(issues)}")
    if correlated.get('pr_numbers'):
        prs = correlated['pr_numbers'][:3]
        parts.append(f"related to PRs: {', '.join(prs)}")
    if correlated.get('authors'):
        authors = correlated['authors'][:2]
        parts.append(f"involves {', '.join(authors)}")
    if correlated.get('file_paths'):
        files = correlated['file_paths'][:2]
        parts.append(f"about files: {', '.join(files)}")
    return " | ".join(parts) if parts else ""
