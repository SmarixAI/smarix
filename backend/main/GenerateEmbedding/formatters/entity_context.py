from typing import Dict, Any

def format_entity_context(entities: Dict[str, Any], chunk_type: str) -> str:
    if not entities:
        return ""
    parts = []
    if entities.get('author'):
        parts.append(f"by {entities['author']}")
    if entities.get('issue_number'):
        parts.append(f"issue #{entities['issue_number']}")
    elif entities.get('pr_number'):
        parts.append(f"PR #{entities['pr_number']}")

    # Bidirectional linking for issues
    if entities.get('linked_prs') and isinstance(entities['linked_prs'], list):
        linked_prs = entities['linked_prs']
        if linked_prs:
            parts.append(f"linked to PRs: {', '.join(f'#{pr}' for pr in linked_prs[:3])}")

    # Resolution status
    if entities.get('is_truly_resolved'):
        parts.append("truly resolved")
    elif entities.get('resolution_status'):
        parts.append(f"status: {entities['resolution_status']}")

    # Bidirectional linking for PRs
    if entities.get('linked_issues') and isinstance(entities['linked_issues'], list):
        linked_issues = entities['linked_issues']
        if linked_issues:
            parts.append(f"closes issues: {', '.join(f'#{issue}' for issue in linked_issues[:3])}")

    # PR status
    if entities.get('pr_status'):
        parts.append(f"pr: {entities['pr_status']}")

    if entities.get('is_merged'):
        parts.append("merged")

    if entities.get('labels') and isinstance(entities['labels'], list):
        labels = [l for l in entities['labels'] if l]
        if labels:
            parts.append(f"labeled: {', '.join(labels[:3])}")
    if entities.get('reviewers') and isinstance(entities['reviewers'], list):
        reviewers = [r for r in entities['reviewers'] if r]
        if reviewers:
            parts.append(f"reviewed by {', '.join(reviewers[:2])}")
    if entities.get('base_branch') or entities.get('head_branch'):
        base = entities.get('base_branch', '')
        head = entities.get('head_branch', '')
        if head and base:
            parts.append(f"from {head} to {base}")
        elif head:
            parts.append(f"branch {head}")
    if entities.get('path'):
        parts.append(f"file: {entities['path']}")
    if entities.get('from'):
        parts.append(f"from {entities['from']}")
    if entities.get('subject'):
        parts.append(f"subject: {entities['subject']}")
    return " | ".join(parts) if parts else ""
