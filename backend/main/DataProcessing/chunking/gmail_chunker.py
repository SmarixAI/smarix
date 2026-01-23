
from typing import List, Dict, Any, Set, Tuple

def chunk_gmail_data(
    self,
    data: Dict[str, Any],
    repo_name: str,
    repo_owner: str,
    git_entities: Dict[str, Set[str]],
) -> List[Dict[str, Any]]:
        """
        Chunk Gmail data with GitHub correlation analysis
        """
        chunks = []
        messages = data.get("messages", []) or []

        for idx, message in enumerate(messages):
            if not isinstance(message, dict):
                continue

            chunk_id = self.generate_chunk_id(message, f"{repo_name}_email", idx)

            # Extract email content
            subject = str(message.get("subject", "") or "").lower()
            snippet = str(message.get("snippet", "") or "").lower()
            payload_text = str(message.get("payload_text", "") or "").lower()
            payload_html = str(message.get("payload_html", "") or "").lower()

            full_text = f"{subject} {snippet} {payload_text} {payload_html}"

            # Correlation analysis with GitHub
            correlated = {
                "authors": [],
                "issue_numbers": [],
                "pr_numbers": [],
                "commit_shas": [],
                "file_paths": [],
                "branches": [],
                "labels": [],
                "emails": [],
                "keywords": [],
            }

            correlation_score = 0.0

            if git_entities:
                # Check author mentions (case-insensitive)
                for author in git_entities.get("authors", set()):
                    if author and author.lower() in full_text:
                        correlated["authors"].append(author)
                        correlation_score += 2

                # ✅ Check issue references
                for issue_num in git_entities.get("issue_numbers", set()):
                    issue_patterns = [
                        f"#{issue_num}",
                        f"issue {issue_num}",
                        f"issue#{issue_num}",
                        issue_num,
                    ]
                    if any(p in full_text for p in issue_patterns):
                        correlated["issue_numbers"].append(issue_num)
                        correlation_score += 3


                # ✅ Check PR references
                for pr_num in git_entities.get("pr_numbers", set()):
                    pr_patterns = [
                        f"#{pr_num}",
                        f"pr {pr_num}",
                        f"pr#{pr_num}",
                        f"pull request {pr_num}",
                        pr_num,
                    ]
                    if any(p in full_text for p in pr_patterns):
                        correlated["pr_numbers"].append(pr_num)
                        correlation_score += 3


                # Check commit SHAs (short or full)
                for sha in git_entities.get("commit_shas", set()):
                    if sha and sha.lower() in full_text:
                        correlated["commit_shas"].append(sha)
                        correlation_score += 2

                # Check file paths (case-insensitive)
                for path in git_entities.get("file_paths", set()):
                    if path and path.lower() in full_text:
                        correlated["file_paths"].append(path)
                        correlation_score += 1

                # Check branch names
                for branch in git_entities.get("branches", set()):
                    if branch and branch.lower() in full_text:
                        correlated["branches"].append(branch)
                        correlation_score += 1

                # Check keywords (small contribution)
                for keyword in git_entities.get("keywords", set()):
                    if keyword and keyword.lower() in full_text:
                        correlated["keywords"].append(keyword)
                        correlation_score += 0.1

                # Check emails
                for email in git_entities.get("emails", set()):
                    if email and email.lower() in full_text:
                        correlated["emails"].append(email)
                        correlation_score += 2

            # Determine if GitHub-related (heuristic)
            is_git_related = correlation_score > 0 or any(
                marker in full_text
                for marker in [
                    "github",
                    "pull request",
                    "pr #",
                    "issue #",
                    "commit",
                    "merge",
                    "branch",
                    "repository",
                    "repo",
                ]
            )

            # Extract structured data
            from_email = message.get("from", "")
            to_emails = message.get("to", "")

            attachments = message.get("attachments", []) or []

            chunk = {
                "chunk_id": chunk_id,
                "type": "email",
                "source": "gmail",
                "repo_name": repo_name,
                "repo_owner": repo_owner,
                "retrieval_priority": (
                    1 if correlation_score > 3 else (2 if is_git_related else 3)
                ),
                # Correlation data
                "is_git_related": is_git_related,
                "correlation_score": correlation_score,
                "correlated_entities": correlated,
                # Entity linking
                "entities": {
                    "message_id": message.get("id"),
                    "from": from_email,
                    "to": to_emails,
                    "subject": message.get("subject", ""),
                },
                "temporal": {
                    "date": message.get("date"),
                },
                # Content
                "content": {
                    "subject": message.get("subject", ""),
                    "snippet": message.get("snippet", ""),
                    "body_text": message.get("payload_text", ""),
                    "body_html": message.get("payload_html", ""),
                    "has_attachments": message.get("has_attachments", False),
                    "attachment_count": len(attachments),
                },
                # Search hints
                "search_hints": {
                    "text": full_text,
                    "keywords": (
                        list(set(correlated["keywords"]))
                        if correlation_score > 0
                        else []
                    )
                },
                "raw_data": {
                    "id": message.get("id"),
                    "subject": message.get("subject"),
                    "from": from_email,
                    "to": to_emails,
                    "date": message.get("date"),
                    "snippet": message.get("snippet"),
                    "payload_text": message.get("payload_text"),
                    "payload_html": message.get("payload_html"),
                    "has_attachments": message.get("has_attachments", False),
                    "attachments": attachments,
                },
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            # Chunk attachments separately
            if isinstance(attachments, list) and attachments:
                for att_idx, attachment in enumerate(attachments):
                    if not isinstance(attachment, dict):
                        continue

                    att_chunk_id = f"{chunk_id}_attachment_{att_idx}"

                    # Check if attachment name correlates with GitHub
                    att_filename = str(attachment.get("filename", "") or "").lower()
                    att_correlation_score = 0.0

                    if git_entities:
                        for path in git_entities.get("file_paths", set()):
                            if path and path.lower() in att_filename:
                                att_correlation_score += 2

                    att_chunk = {
                        "chunk_id": att_chunk_id,
                        "type": "email_attachment",
                        "source": "gmail",
                        "repo_name": repo_name,
                        "repo_owner": repo_owner,
                        "retrieval_priority": 3,
                        "parent_message_id": message.get("id"),
                        "parent_chunk_id": chunk_id,
                        "is_git_related": is_git_related or att_correlation_score > 0,
                        "correlation_score": att_correlation_score,
                        "entities": {
                            "filename": attachment.get("filename"),
                            "mime_type": attachment.get("mime_type"),
                            "size": attachment.get("size"),
                        },
                        "content": attachment,
                        "search_hints": {
                            "text": att_filename,
                            "keywords": list(git_entities.get("keywords", [])),
                        },
                        "raw_data": attachment,
                    }

                    chunks.append(att_chunk)
                    self.chunk_registry[att_chunk_id] = att_chunk

        return chunks
