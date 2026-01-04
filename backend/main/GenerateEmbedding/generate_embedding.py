"""
Enterprise-Grade Embedding Generation (Step 3)
Optimized for GitHub-first → Gmail correlation with rich metadata
Supports hybrid embedding: content + entities + temporal context
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

_backend_dir = Path(__file__).resolve().parents[2]
_backend_dir_str = str(_backend_dir)
if _backend_dir_str not in sys.path:
    sys.path.insert(0, _backend_dir_str)

from core.GenerateEmbedding.generator import EmbeddingGenerator

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


def auto_detect_provider():
    if os.getenv('OPENAI_API_KEY'):
        return 'openai', 'text-embedding-3-small'
    elif os.getenv('COHERE_API_KEY'):
        return 'cohere', 'embed-english-v3.0'
    else:
        return 'sentence-transformers', 'all-MiniLM-L6-v2'


def find_latest_chunks_file():
    processed_dir = Path("../../data/DataProcessing") / REPO_OWNER / REPO_NAME / "chunks"
    if not processed_dir.exists():
        return None
    chunks_files = list(processed_dir.glob("*_chunks.json"))
    if not chunks_files:
        return None
    latest = max(chunks_files, key=lambda p: p.stat().st_mtime)
    return str(latest)


def format_temporal_context(temporal: Dict[str, Any]) -> str:
    if not temporal:
        return ""
    parts = []
    if temporal.get('created_at'):
        try:
            created = datetime.fromisoformat(temporal['created_at'].replace('Z', '+00:00'))
            parts.append(f"created {created.strftime('%B %d, %Y')}")
        except:
            parts.append(f"created {temporal['created_at']}")
    if temporal.get('updated_at'):
        try:
            updated = datetime.fromisoformat(temporal['updated_at'].replace('Z', '+00:00'))
            parts.append(f"updated {updated.strftime('%B %d, %Y')}")
        except:
            pass
    if temporal.get('closed_at'):
        parts.append("closed")
    elif temporal.get('merged_at'):
        parts.append("merged")
    return ", ".join(parts) if parts else ""


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


def extract_commit_data(chunk: Dict[str, Any]) -> Tuple[str, List[str], Dict[str, str]]:
    commit_message = ""
    files_modified = []
    author_info = {}
    content = chunk.get('content', {})
    if isinstance(content, dict):
        commit_message = content.get('message', '')
        files_modified = content.get('files_modified', [])
    if not commit_message:
        raw_data = chunk.get('raw_data', {})
        if isinstance(raw_data, dict):
            commit_obj = raw_data.get('commit', {})
            if isinstance(commit_obj, dict):
                commit_message = commit_obj.get('message', '')
                author_data = commit_obj.get('author', {})
                if isinstance(author_data, dict):
                    author_info['name'] = author_data.get('name', '')
                    author_info['email'] = author_data.get('email', '')
                    author_info['date'] = author_data.get('date', '')
            if 'files' in raw_data and isinstance(raw_data['files'], list):
                files_modified = [
                    f.get('filename', '')
                    for f in raw_data['files']
                    if isinstance(f, dict) and f.get('filename')
                ]
    if not commit_message and not author_info:
        entities = chunk.get('entities', {})
        if isinstance(entities, dict):
            author_info['name'] = entities.get('author', '')
            author_info['sha'] = entities.get('sha', '') or entities.get('sha_short', '')
    if not commit_message:
        search_hints = chunk.get('search_hints', {})
        if isinstance(search_hints, dict):
            hint_text = search_hints.get('text', '')
            if hint_text and 'commit' in hint_text.lower():
                commit_message = hint_text[:500]
    return commit_message, files_modified, author_info


def extract_main_content(chunk: Dict[str, Any]) -> str:
    """
    Extract comprehensive content from chunks including ALL metadata,
    comments, reviews, file changes, and patches - NO TRUNCATION.
    Optimized for developer onboarding - includes everything needed to understand
    issues, PRs, commits, and codebase context.
    """
    chunk_type = chunk.get('type', 'unknown')
    content = chunk.get('content', {})
    if not isinstance(content, dict):
        return str(content) if content else ""

    text_parts = []

    if chunk_type == 'issue':
        # Title
        if content.get('title'):
            text_parts.append(f"Issue: {content['title']}")

        # Body - COMPLETE
        if content.get('body'):
            text_parts.append(content['body'])

        # State
        if content.get('state'):
            text_parts.append(f"State: {content['state']}")

        # Labels
        if content.get('labels') and isinstance(content['labels'], list):
            labels = [l for l in content['labels'] if l]
            if labels:
                text_parts.append(f"Labels: {', '.join(labels)}")

        # ALL Comments - COMPLETE
        comments = chunk.get('comments', [])
        if comments and isinstance(comments, list):
            comment_texts = []
            for idx, comment in enumerate(comments):
                if isinstance(comment, dict):
                    author = comment.get('author', 'unknown')
                    body = comment.get('body', '')
                    created = comment.get('created_at', '')
                    updated = comment.get('updated_at', '')
                    comment_id = comment.get('id', '')

                    if body:
                        comment_str = f"Comment #{idx + 1} by {author}"
                        if comment_id:
                            comment_str += f" [ID: {comment_id}]"
                        if created:
                            try:
                                created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                                comment_str += f" on {created_dt.strftime('%Y-%m-%d %H:%M')}"
                            except:
                                pass
                        if updated and updated != created:
                            try:
                                updated_dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                                comment_str += f" (edited {updated_dt.strftime('%Y-%m-%d %H:%M')})"
                            except:
                                pass
                        comment_str += f":\n{body}"
                        comment_texts.append(comment_str)

            if comment_texts:
                text_parts.append(f"\n\n=== COMMENTS ({len(comment_texts)}) ===\n" + "\n\n".join(comment_texts))

        # Entity metadata
        entities = chunk.get('entities', {})
        if entities:
            linked_prs = entities.get('linked_prs', [])
            resolution_status = entities.get('resolution_status', '')
            is_truly_resolved = entities.get('is_truly_resolved', False)
            assignees = entities.get('assignees', [])
            milestone = entities.get('milestone', '')

            metadata_parts = []
            if linked_prs:
                metadata_parts.append(f"Linked PRs: {', '.join(f'#{pr}' for pr in linked_prs)}")
            if assignees:
                metadata_parts.append(f"Assignees: {', '.join(assignees)}")
            if milestone:
                metadata_parts.append(f"Milestone: {milestone}")
            if is_truly_resolved:
                metadata_parts.append(f"Resolution: Resolved by merged PR ({resolution_status})")
            elif resolution_status:
                metadata_parts.append(f"Resolution: {resolution_status}")

            if metadata_parts:
                text_parts.append(f"\n=== METADATA ===\n" + "\n".join(metadata_parts))

        # Referenced issues from raw_data
        raw_data = chunk.get('raw_data', {})
        if raw_data and isinstance(raw_data, dict):
            if raw_data.get('referenced_issues'):
                refs = raw_data['referenced_issues']
                if refs:
                    text_parts.append(f"\nReferenced Issues: {', '.join(f'#{r}' for r in refs)}")


    elif chunk_type == "pr":

        # TITLE - Extract PR title

        if content.get("title"):
            text_parts.append(f"Pull Request: {content['title']}")

        # BODY - COMPLETE PR description

        if content.get("body"):
            text_parts.append(content["body"])

        # STATE AND MERGE STATUS - Comprehensive state info

        state = content.get("state")

        merged = content.get("merged", False)

        mergeable = content.get("mergeable")

        mergeable_state = content.get("mergeable_state")

        # FIX: Check temporal.merged_at as well for accurate merged status

        temporal = chunk.get("temporal") or {}

        if temporal.get("merged_at") and not merged:
            merged = True

        state_info = f"State: {state}"

        if merged:

            state_info += " (MERGED)"

        elif state == "closed":

            state_info += " (CLOSED WITHOUT MERGE)"

        if mergeable is not None:
            state_info += f" | Mergeable: {mergeable}"

        if mergeable_state:
            state_info += f" | Merge State: {mergeable_state}"

        text_parts.append(state_info)

        # PR STATISTICS - Commits, files, lines changed, review comments

        commits_count = content.get("commits_count", 0)

        changed_files_count = content.get("changed_files_count", 0)

        additions = content.get("additions", 0)

        deletions = content.get("deletions", 0)

        review_comments_count = content.get("review_comments_count", 0)

        stats = [

            f"{commits_count} commits",

            f"{changed_files_count} files changed",

            f"+{additions}/-{deletions} lines",

            f"{review_comments_count} review comments"

        ]

        text_parts.append(f"\n═══ CHANGES SUMMARY ═══\n" + " | ".join(stats))

        # FILE CHANGES - ALL files with COMPLETE patches

        file_changes = chunk.get("file_changes")

        # FIX: If file_changes is empty, check raw_data

        if not file_changes:

            raw_data = chunk.get("raw_data") or {}

            if raw_data.get("changed_files"):

                file_changes = raw_data["changed_files"]

            elif raw_data.get("files"):

                file_changes = raw_data["files"]

        if file_changes and isinstance(file_changes, list):

            text_parts.append(f"\n═══ FILES MODIFIED ({len(file_changes)}) ═══")

            # Summary list of all files

            files_summary = []

            for fc in file_changes:

                if isinstance(fc, dict):

                    filename = fc.get("filename")

                    status = fc.get("status")

                    adds = fc.get("additions", 0)

                    dels = fc.get("deletions", 0)

                    if filename:
                        files_summary.append(f"• {filename} ({status}) [+{adds}/-{dels}]")

            if files_summary:
                text_parts.append("\n".join(files_summary))

            # DETAILED PATCHES - Complete patch content for ALL files

            text_parts.append(f"\n═══ CODE CHANGES: DETAILED PATCHES ═══")

            for fc in file_changes:

                if isinstance(fc, dict):

                    filename = fc.get("filename")

                    patch = fc.get("patch")

                    status = fc.get("status")

                    adds = fc.get("additions", 0)

                    dels = fc.get("deletions", 0)

                    blob_url = fc.get("blob_url")

                    raw_url = fc.get("raw_url")

                    previous_filename = fc.get("previous_filename")

                    if filename:

                        file_header = f"\n{'─' * 60}\n📄 {filename}"

                        if status:
                            file_header += f" [{status.upper()}]"

                        if previous_filename:
                            file_header += f" (renamed from {previous_filename})"

                        file_header += f" [+{adds}/-{dels}]"

                        if raw_url:
                            file_header += f"\n🔗 {raw_url}"

                        file_header += f"\n{'─' * 60}"

                        text_parts.append(file_header)

                        # Include COMPLETE patch - no truncation

                        if patch:
                            text_parts.append(patch)

                        else:
                            text_parts.append("⚠ No patch available (binary file or too large)")

        # REVIEWS - ALL review comments with COMPLETE text

        reviews = chunk.get("reviews")

        # FIX: If reviews is empty, check raw_data

        if not reviews:

            raw_data = chunk.get("raw_data") or {}

            if raw_data.get("reviews"):
                reviews = raw_data["reviews"]

        if reviews and isinstance(reviews, list):

            text_parts.append(f"\n═══ REVIEWS ({len(reviews)}) ═══")

            for idx, review in enumerate(reviews):

                if isinstance(review, dict):

                    author = review.get("author", "unknown")

                    state = review.get("state")

                    body = review.get("body")

                    submitted_at = review.get("submitted_at")

                    commit_id = review.get("commit_id")

                    review_id = review.get("id")

                    review_header = f"\nReview #{idx + 1} by {author}"

                    if review_id:
                        review_header += f" (ID: {review_id})"

                    if state:
                        review_header += f" - {state.upper()}"

                    if submitted_at:

                        try:

                            review_dt = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))

                            review_header += f" on {review_dt.strftime('%Y-%m-%d %H:%M')}"

                        except:

                            pass

                    if commit_id:
                        review_header += f" (commit: {commit_id[:7]})"

                    text_parts.append(review_header)

                    if body:

                        text_parts.append(f"{body}")

                    else:

                        text_parts.append("(No comment provided)")

        # ENTITY METADATA - Linked issues, branches, merged by, reviewers

        entities = chunk.get("entities")

        if entities:

            linked_issues = entities.get("linked_issues")

            pr_status = entities.get("pr_status")

            is_merged = entities.get("is_merged", False)

            base_branch = entities.get("base_branch")

            head_branch = entities.get("head_branch")

            merged_by = entities.get("merged_by")

            reviewers = entities.get("reviewers")

            metadata_parts = []

            if head_branch and base_branch:
                metadata_parts.append(f"Branch: {head_branch} → {base_branch}")

            if linked_issues:
                metadata_parts.append(f"Closes Issues: {', '.join([f'#{issue}' for issue in linked_issues])}")

            if merged_by:
                metadata_parts.append(f"Merged By: {merged_by}")

            if reviewers:
                metadata_parts.append(f"Reviewers: {', '.join(reviewers)}")

            if pr_status:
                metadata_parts.append(f"Status: {pr_status}")

            if metadata_parts:
                text_parts.append(f"\n═══ METADATA ═══\n" + "\n".join(metadata_parts))

        # TEMPORAL INFO - Timeline of events

        temporal = chunk.get("temporal")

        if temporal:

            created = temporal.get("created_at")

            updated = temporal.get("updated_at")

            merged_at = temporal.get("merged_at")

            closed_at = temporal.get("closed_at")

            timeline = []

            if created:

                try:

                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))

                    timeline.append(f"Created: {dt.strftime('%Y-%m-%d %H:%M')}")

                except:

                    timeline.append(f"Created: {created}")

            if updated:

                try:

                    dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))

                    timeline.append(f"Updated: {dt.strftime('%Y-%m-%d %H:%M')}")

                except:

                    pass

            if merged_at:

                try:

                    dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))

                    timeline.append(f"Merged: {dt.strftime('%Y-%m-%d %H:%M')}")

                except:

                    timeline.append(f"Merged: {merged_at}")

            if closed_at and not merged_at:

                try:

                    dt = datetime.fromisoformat(closed_at.replace("Z", "+00:00"))

                    timeline.append(f"Closed: {dt.strftime('%Y-%m-%d %H:%M')}")

                except:

                    timeline.append(f"Closed: {closed_at}")

            if timeline:
                text_parts.append(f"\n═══ TIMELINE ═══\n" + " | ".join(timeline))

        # RAW DATA - Additional info like linked commits, URLs

        raw_data = chunk.get("raw_data")

        if raw_data and isinstance(raw_data, dict):

            if raw_data.get("linked_commits"):

                commits = raw_data["linked_commits"]

                if commits:
                    text_parts.append(f"Linked Commits: {', '.join(commits[:10])}")

            if raw_data.get("html_url"):
                text_parts.append(f"🔗 URL: {raw_data['html_url']}")

    elif chunk_type == 'commit':
        commit_message, files_modified, author_info = extract_commit_data(chunk)

        # Author & Committer info
        author_name = author_info.get('name', '')
        author_email = author_info.get('email', '')
        sha = author_info.get('sha', '')
        date = author_info.get('date', '')

        if author_name:
            author_str = f"Author: {author_name}"
            if author_email:
                author_str += f" <{author_email}>"
            text_parts.append(author_str)

        if sha:
            text_parts.append(f"Commit: {sha}")

        if date:
            try:
                date_dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                text_parts.append(f"Date: {date_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                text_parts.append(f"Date: {date}")

        # Commit message - COMPLETE
        if commit_message:
            text_parts.append(f"\n=== COMMIT MESSAGE ===\n{commit_message.strip()}")

        # Stats
        content_obj = chunk.get('content', {})
        if isinstance(content_obj, dict):
            stats = content_obj.get('stats', {})
            if stats:
                total_files = stats.get('total_files', 0)
                additions = stats.get('additions', 0)
                deletions = stats.get('deletions', 0)
                text_parts.append(f"\n=== CHANGES ===\n{total_files} files | +{additions}/-{deletions} lines")

        # ALL Modified files
        files = chunk.get('files', [])
        if files and isinstance(files, list):
            text_parts.append(f"\n=== FILES MODIFIED ({len(files)}) ===")

            for f in files:
                if isinstance(f, dict):
                    filename = f.get('filename', '')
                    status = f.get('status', '')
                    adds = f.get('additions', 0)
                    dels = f.get('deletions', 0)
                    patch = f.get('patch', '')

                    if filename:
                        file_info = f"\n{filename} ({status}) [+{adds}/-{dels}]"
                        text_parts.append(file_info)

                        if patch:
                            text_parts.append(f"Patch:\n{patch}\n")

    elif chunk_type == 'code':
        path = chunk.get('entities', {}).get('path', 'code file')
        language = chunk.get('entities', {}).get('language', '')

        text_parts.append(f"=== CODE FILE ===\nPath: {path}")
        if language:
            text_parts.append(f"Language: {language}")

        # COMPLETE code content
        if content.get('content'):
            code_content = content['content']
            text_parts.append(f"\n{'=' * 60}\n{code_content}\n{'=' * 60}")

        # Analysis if available
        if content.get('analysis'):
            analysis = content['analysis']
            text_parts.append(f"\n=== CODE ANALYSIS ===\n{json.dumps(analysis, indent=2)}")

    elif chunk_type == 'documentation':
        path = chunk.get('entities', {}).get('path', 'documentation')
        text_parts.append(f"=== DOCUMENTATION ===\nPath: {path}")

        # Headers
        if content.get('headers') and isinstance(content['headers'], list):
            headers = content['headers']
            if headers:
                text_parts.append(f"\nTable of Contents:\n" + "\n".join(f"  • {h}" for h in headers))

        # COMPLETE documentation content
        if content.get('content'):
            doc_content = content['content']
            text_parts.append(f"\n{'=' * 60}\n{doc_content}\n{'=' * 60}")

    elif chunk_type == 'email':
        subject = content.get('subject', '')
        from_email = chunk.get('entities', {}).get('from', '')
        to_emails = chunk.get('entities', {}).get('to', '')
        date = chunk.get('temporal', {}).get('date', '')

        text_parts.append(f"=== EMAIL ===")
        if subject:
            text_parts.append(f"Subject: {subject}")
        if from_email:
            text_parts.append(f"From: {from_email}")
        if to_emails:
            text_parts.append(f"To: {to_emails}")
        if date:
            text_parts.append(f"Date: {date}")

        # COMPLETE email body
        email_body = content.get('snippet') or content.get('body_text', '')
        if email_body:
            text_parts.append(f"\n{email_body}")

        if content.get('has_attachments'):
            att_count = content.get('attachment_count', 0)
            text_parts.append(f"\nAttachments: {att_count}")

    elif chunk_type == 'email_attachment':
        filename = chunk.get('entities', {}).get('filename', 'attachment')
        mime_type = chunk.get('entities', {}).get('mime_type', '')
        size = chunk.get('entities', {}).get('size', 0)
        text_parts.append(f"=== EMAIL ATTACHMENT ===\nFilename: {filename}")
        if mime_type:
            text_parts.append(f"Type: {mime_type}")
        if size:
            size_kb = size / 1024
            text_parts.append(f"Size: {size_kb:.2f} KB")

    elif chunk_type in ['onboarding', 'offboarding']:
        text_parts.append(f"=== {chunk_type.upper()} INFORMATION ===")
        if content:
            content_str = json.dumps(content, indent=2)
            text_parts.append(content_str)

    elif chunk_type == 'workflow':
        name = chunk.get('entities', {}).get('name', 'workflow')
        text_parts.append(f"=== WORKFLOW: {name} ===")
        if content:
            workflow_str = json.dumps(content, indent=2)
            text_parts.append(workflow_str)

    elif chunk_type == 'analyzed_file':
        path = chunk.get('entities', {}).get('path', 'analyzed file')
        text_parts.append(f"=== ANALYZED FILE: {path} ===")
        if content:
            analyzed_str = json.dumps(content, indent=2)
            text_parts.append(analyzed_str)

    elif chunk_type == 'repository_overview':
        text_parts.append("=== REPOSITORY OVERVIEW ===")

        techstack = chunk.get('techstack', {})
        if techstack:
            languages = techstack.get('languages', {})
            if languages:
                primary = languages.get('primary', 'unknown')
                all_langs = languages.get('all', {})
                text_parts.append(f"\nPrimary Language: {primary}")
                if all_langs:
                    top_langs = sorted(all_langs.items(), key=lambda x: x[1], reverse=True)
                    text_parts.append(
                        f"All Languages: {', '.join(f'{lang} ({count} files)' for lang, count in top_langs)}")

            frameworks = techstack.get('frameworks', {})
            if frameworks:
                detected = frameworks.get('detected', [])
                if detected:
                    text_parts.append(f"\nFrameworks: {', '.join(detected)}")

            tools = techstack.get('tools', {})
            if tools:
                detected = tools.get('detected', [])
                if detected:
                    text_parts.append(f"Development Tools: {', '.join(detected)}")

            metrics = techstack.get('metrics', {})
            if metrics:
                text_parts.append(f"\n=== CODE METRICS ===")
                text_parts.append(f"Total Files: {metrics.get('total_files', 0)}")
                text_parts.append(f"Code Lines: {metrics.get('total_code_lines', 0):,}")
                text_parts.append(f"Comment Lines: {metrics.get('total_comment_lines', 0):,}")
                text_parts.append(f"Blank Lines: {metrics.get('total_blank_lines', 0):,}")

                funcs = techstack.get('functions_and_classes', {}).get('total_functions', 0)
                classes = techstack.get('functions_and_classes', {}).get('total_classes', 0)
                text_parts.append(f"Functions: {funcs:,} | Classes: {classes:,}")

        summary = chunk.get('summary', {})
        if summary:
            text_parts.append(f"\n=== ACTIVITY SUMMARY ===")
            text_parts.append(f"Issues: {summary.get('total_issues', 0):,}")
            text_parts.append(f"Pull Requests: {summary.get('total_prs', 0):,}")
            text_parts.append(f"Commits: {summary.get('total_commits', 0):,}")

    elif chunk_type == 'raw_data_reference':
        metadata = chunk.get('metadata', {})
        source = metadata.get('source', 'unknown')
        data_keys = metadata.get('data_keys', [])
        text_parts.append(f"=== RAW DATA REFERENCE: {source} ===")
        if data_keys:
            text_parts.append(f"Contains: {', '.join(data_keys)}")
        summary = metadata.get('summary', {})
        if summary:
            summary_str = json.dumps(summary, indent=2)
            text_parts.append(f"\n{summary_str}")

    else:
        # Unknown types - complete content
        if content:
            text_parts.append(f"=== {chunk_type.upper()} ===")
            text_parts.append(json.dumps(content, indent=2))

    result = "\n\n".join(text_parts) if text_parts else ""
    return result

def _count_lines_and_functions_in_code(content: str, language_hint: str = "") -> Tuple[int, int]:
    if not content:
        return 0, 0
    lines = content.splitlines()
    non_empty_lines = [l for l in lines if l.strip() != ""]
    line_count = len(non_empty_lines)
    func_count = 0
    func_count += len(re.findall(r'^\s*def\s+\w+\s*\(', content, flags=re.MULTILINE))
    func_count += len(re.findall(r'^\s*(?:function\s+\w+|\w+\s*:\s*function\s*\(|(?:const|let|var)\s+\w+\s*=\s*\(.*?\)\s*=>)', content, flags=re.MULTILINE))
    func_count += len(re.findall(r'^\s*\w+\s*\(.*?\)\s*\{', content, flags=re.MULTILINE))
    func_count += len(re.findall(r'^\s*(?:public|private|protected|static|final|\w+)\s+\w+\s+\w+\s*\(.*?\)\s*\{', content, flags=re.MULTILINE))
    func_count += len(re.findall(r'^\s*func\s+\w+\s*\(', content, flags=re.MULTILINE))
    func_count = min(func_count, line_count)
    return line_count, func_count


def compute_repo_metrics(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = {
        'total_lines': 0,
        'total_functions': 0,
        'total_files': 0,
        'by_repo': {},
        'repo_structure': {},
        'total_chunks_by_type': {},
    }
    for chunk in chunks:
        ctype = chunk.get('type', 'unknown')
        metrics['total_chunks_by_type'][ctype] = metrics['total_chunks_by_type'].get(ctype, 0) + 1
        if ctype != 'code':
            continue
        repo = chunk.get('repo_name') or chunk.get('metadata', {}).get('repo_name') or chunk.get('source_repo') or 'unknown_repo'
        entities = chunk.get('entities', {}) or {}
        path = entities.get('path') or chunk.get('path') or 'unknown_path'
        language = entities.get('language', '') or ''
        content = None
        c = chunk.get('content')
        if isinstance(c, dict):
            content = c.get('content') or ''
        else:
            content = c or ''
        lines, funcs = _count_lines_and_functions_in_code(content, language)
        metrics['total_lines'] += lines
        metrics['total_functions'] += funcs
        metrics['total_files'] += 1
        repo_stats = metrics['by_repo'].setdefault(repo, {'lines': 0, 'functions': 0, 'files': 0, 'sample_paths': []})
        repo_stats['lines'] += lines
        repo_stats['functions'] += funcs
        repo_stats['files'] += 1
        if len(repo_stats['sample_paths']) < 10:
            repo_stats['sample_paths'].append(path)
        top = path.split('/', 1)[0] if path else ''
        repo_struct = metrics['repo_structure'].setdefault(repo, {'top_level_dirs': {}, 'files': []})
        if top:
            repo_struct['top_level_dirs'][top] = repo_struct['top_level_dirs'].get(top, 0) + 1
        if len(repo_struct['files']) < 10:
            repo_struct['files'].append(path)
    return metrics


def load_and_inject_aggregated_tech_summary(processed_dir: Path, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tech_file = processed_dir / "aggregated_tech_stack_summary.json"
    if not tech_file.exists():
        return chunks
    try:
        with open(tech_file, 'r', encoding='utf-8') as f:
            tech_summary = json.load(f)
    except Exception:
        return chunks
    readable = []
    if isinstance(tech_summary, dict):
        digest = tech_summary.get('digest') or tech_summary.get('summary') or None
        if digest:
            readable.append(str(digest)[:3000])
        languages = tech_summary.get('languages') or tech_summary.get('language_breakdown') or {}
        if languages:
            parts = [f"{lang}: {count}" for lang, count in (languages.items() if isinstance(languages, dict) else [])][:50]
            if parts:
                readable.append("Languages: " + ", ".join(parts[:20]))
        libs = tech_summary.get('top_libraries') or tech_summary.get('libraries') or []
        if libs and isinstance(libs, list):
            readable.append("Top libraries: " + ", ".join(libs[:20]))
        notable = {}
        for k in ['total_files', 'total_lines', 'repo_count', 'most_used_frameworks']:
            if k in tech_summary:
                notable[k] = tech_summary[k]
        if notable:
            readable.append("Notable: " + json.dumps
            (notable)[:1000])
    summarized_text = "\n\n".join(readable) if readable else json.dumps(tech_summary)[:3000]
    tech_chunk = {
        'chunk_id': f"tech_summary_{int(datetime.now(timezone.utc).timestamp())}",
        'type': 'tech_stack_summary',
        'source': 'aggregated_tech_stack_summary',
        'content': summarized_text,
        'metadata': {
            'origin_file': str(tech_file),
            'raw_summary': tech_summary
        },
        'full_chunk': {'raw': tech_summary},
        'skip_embedding': False,
    }
    return [tech_chunk] + chunks


def prepare_enhanced_chunk_for_embedding(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare chunk for embedding with ALL metadata fields properly extracted.
    Ensures merged PRs, reviews, comments & patches are captured, and metadata is
    flattened for enriched-text embeddings.
    """
    chunk_id = chunk.get("chunk_id", "unknown")
    chunk_type = chunk.get("chunk_type") or chunk.get("type") or "unknown"
    source = chunk.get("source", "unknown")

    # 🔥 AUTO-EXTRACT file path, filename, directory & language from content (handles dict/string)
    # Try multiple content fields when chunk['content'] is a dict (common case)
    raw_content = chunk.get("content", "")
    content_text = ""
    if isinstance(raw_content, dict):
        # prefer common fields that hold the textual payload
        for candidate in ("content", "body", "snippet", "text", "code", "raw"):
            if raw_content.get(candidate):
                content_text = raw_content.get(candidate)
                break
        # fallback to a compact JSON representation
        if not content_text:
            try:
                content_text = json.dumps(raw_content)
            except Exception:
                content_text = ""
    elif isinstance(raw_content, str):
        content_text = raw_content

    if content_text:
        # Look for common header patterns, case-insensitive
        m_path = re.search(r"(?:Path|file|File):\s*([^\n]+)", content_text, flags=re.IGNORECASE)
        if m_path:
            extracted_path = m_path.group(1).strip().strip('`')
            chunk.setdefault("entities", {})["path"] = extracted_path
            # top-level convenience field
            chunk["file_path"] = extracted_path

            # Also populate filename and directory
            try:
                p = Path(extracted_path)
                fname = p.name
                fdir = str(p.parent) if str(p.parent) not in (".", "") else ""
                chunk.setdefault("entities", {})["filename"] = fname
                chunk.setdefault("entities", {})["directory"] = fdir
            except Exception:
                pass

        # language can be declared in header or inferred from extension
        m_lang = re.search(r"Language:\s*([^\n]+)", content_text, flags=re.IGNORECASE)
        if m_lang:
            lang_val = m_lang.group(1).strip().lower()
            chunk.setdefault("entities", {})["language"] = lang_val
            chunk["language"] = lang_val
        else:
            # try to infer from extracted_path if present and language missing
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

    # --- derive file path/filename/directory/language for metadata ---
    file_path_val = entities.get('path') or chunk.get('path') or chunk.get('repo_file_path') or chunk.get('file_path')
    derived_filename = None
    derived_directory = None
    if file_path_val:
        try:
            p = Path(file_path_val)
            derived_filename = p.name
            derived_directory = str(p.parent) if str(p.parent) not in ('.', '') else ''
        except Exception:
            derived_filename = None
            derived_directory = None

    # --- Metadata object used in RAG + vector DB ---
    storage_metadata = {
        "chunk_id": chunk_id,
        "chunk_type": chunk_type,   # <-- CRITICAL for retriever & embedding
        "type": chunk_type,
        "source": source,
        "repo_name": chunk.get("repo_name"),
        "file_path": file_path_val,
        "language": entities.get("language") or chunk.get("language"),
        "filename": entities.get("filename") or derived_filename,
        "directory": entities.get("directory") or derived_directory,
        "retrieval_priority": chunk.get("retrieval_priority", 3),

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

    # promote file_path & language to top-level for retriever
    prepared["file_path"] = prepared["metadata"].get("file_path")
    prepared["language"] = prepared["metadata"].get("language")

    # --- TOP-LEVEL promotion (for EmbeddingGenerator._create_enriched_text) ---
    for field in [
        "chunk_type", "category", "importance_score", "file_path",
        "function_name", "class_name", "semantic_tags", "keywords",
        "language"
    ]:
        if field in chunk:                       # if raw chunk carried these
            prepared[field] = chunk[field]
        if field in storage_metadata:            # if computed during metadata build
            prepared[field] = storage_metadata[field]

    return prepared




def prepare_chunks_for_embedding(chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
   
    
    prepared_chunks = []
    stats = {
        'total': len(chunks),
        'processed': 0,
        'skipped': 0,
        'raw_data_refs': 0,
        'empty_content': 0,
        'by_type': {},
        'by_priority': {}
    }
    for chunk in chunks:
        # 🔥 Intercept raw-data chunks and convert them to real chunks
        from core.GenerateEmbedding.raw_data_extraction import convert_raw_to_chunks

        if chunk.get("is_raw_data", False):
            generated = convert_raw_to_chunks(chunk)  # produce code/issue/pr/commit chunks
            # Instead of embedding the raw container, embed the generated chunks
            print(f"RAW → GENERATED: {len(generated)} new chunks from {chunk.get('source')}")

            for g in generated:
                prepared_chunks.append(prepare_enhanced_chunk_for_embedding(g))
                stats['processed'] += 1
                ctype = g.get('type', 'unknown')
                stats['by_type'][ctype] = stats['by_type'].get(ctype, 0) + 1
            stats['raw_data_refs'] += 1
            continue

        prepared = prepare_enhanced_chunk_for_embedding(chunk)
        chunk_type = prepared['type']

        if chunk_type == "issue":
           print("DEBUG:", prepared["metadata"])


        stats['by_type'][chunk_type] = stats['by_type'].get(chunk_type, 0) + 1
        if prepared.get('skip_embedding'):
            stats['skipped'] += 1
            if chunk.get('is_raw_data'):
                stats['raw_data_refs'] += 1
            else:
                stats['empty_content'] += 1
            continue
        prepared_chunks.append(prepared)
        stats['processed'] += 1
        priority = prepared['metadata'].get('retrieval_priority', 3)
        stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
    return prepared_chunks, stats


def detect_source_type(chunks):
    if not chunks:
        return 'unknown'
    first_chunk = chunks[0]
    source = first_chunk.get('source', None)
    if source:
        return source
    chunk_type = first_chunk.get('type', '')
    if chunk_type in ['email', 'email_attachment']:
        return 'gmail'
    elif chunk_type in ['issue', 'pr', 'commit', 'code', 'documentation']:
        return 'git'
    return 'unknown'


def _get_size(file_path: Path) -> str:
    try:
        size = file_path.stat().st_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} KB"
        else:
            return f"{size/(1024*1024):.1f} MB"
    except:
        return "unknown"


def estimate_cost(provider: str, model: str, num_chunks: int, stats: dict):
    avg_tokens_per_chunk = 800
    total_tokens = num_chunks * avg_tokens_per_chunk
    costs = {
        'openai': {
            'text-embedding-3-small': 0.02 / 1_000_000,
            'text-embedding-3-large': 0.13 / 1_000_000,
            'text-embedding-ada-002': 0.10 / 1_000_000
        },
        'cohere': {
            'embed-english-v3.0': 0.10 / 1_000_000,
            'embed-multilingual-v3.0': 0.10 / 1_000_000
        }
    }
    cost_per_token = costs.get(provider, {}).get(model, 0)
    estimated_cost = total_tokens * cost_per_token
    if estimated_cost > 0:
        print(f"\nEstimated Cost:")
        print(f"   Tokens: ~{total_tokens:,}")
        print(f"   Cost: ~${estimated_cost:.3f}")


def batch_generate(args):
    processed_dir = Path("../../data/DataProcessing") / REPO_OWNER / REPO_NAME / "chunks"
    base_output_dir = Path(str(args.output_dir))
    output_dir = base_output_dir / REPO_OWNER / REPO_NAME

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    if not processed_dir.exists():
        print(f"Error: Processed directory not found: {processed_dir}")
        return

    # Pick up type-specific files only
    chunks_files = [
        f for f in processed_dir.glob("*_chunks.json")
        if not any(skip in f.name for skip in ['strategy', 'entities', '_git_chunks', '_gmail_chunks', 'aggregated'])
    ]

    if not chunks_files:
        print(f"Error: No chunks files found in {processed_dir}")
        return

    print(f"Found {len(chunks_files)} type-specific chunks files\n")

    # Group by repository and type with BETTER parsing
    by_repo = defaultdict(dict)
    for f in chunks_files:
        # Extract from filename: owner_repo_TYPE_chunks.json
        parts = f.stem.split('_')

        # Find the position of "chunks" to identify type
        if 'chunks' in parts:
            chunks_idx = parts.index('chunks')
            if chunks_idx > 0:
                # Type is the word RIGHT BEFORE "chunks"
                chunk_type = parts[chunks_idx - 1]
                # Repo name is everything BEFORE the type
                repo_name = '_'.join(parts[:chunks_idx - 1])

                # VALIDATION: Skip if chunk_type is empty or invalid
                if not chunk_type or chunk_type in ['git', 'gmail', 'unknown']:
                    print(f"   ⚠️  Skipping invalid chunk type '{chunk_type}' from {f.name}")
                    continue

                by_repo[repo_name][chunk_type] = f
            else:
                print(f"   ⚠️  Could not parse filename: {f.name}")
        else:
            print(f"   ⚠️  Invalid filename format (missing 'chunks'): {f.name}")

    if not by_repo:
        print(f"Error: No valid chunk files found after parsing")
        return

    print(f"Repositories found: {len(by_repo)}\n")
    for repo_name, types in by_repo.items():
        print(f"   {repo_name}:")
        for chunk_type, file in types.items():
            print(f"      {chunk_type}: {file.name}")
    print()

    provider = args.provider
    model = args.model

    if not provider:
        provider, default_model = auto_detect_provider()
        if not model:
            model = default_model
        print(f"Using provider: {provider} ({model})\n")

    try:
        generator = EmbeddingGenerator(
            provider=provider,
            model=model,
            batch_size=args.batch_size,
            cache_dir=Path(str(args.cache_dir))
        )
    except Exception as e:
        print(f"Error initializing generator: {e}")
        return

    results = []

    # Process each type-specific file
    for repo_name, type_files in by_repo.items():
        print(f"\n{'=' * 70}")
        print(f"Processing repository: {repo_name}")
        print(f"{'=' * 70}")

        # Collect all chunks for combined index
        all_chunks_for_repo = []

        for chunk_type, chunks_file in type_files.items():
            print(f"\n   Type: {chunk_type}")
            print(f"   File: {chunks_file.name}")

            try:
                # Load chunks
                with open(chunks_file, 'r', encoding='utf-8') as f:
                    chunks = json.load(f)

                if not chunks:
                    print(f"      Warning: Empty file, skipping...")
                    continue

                print(f"      Raw chunks: {len(chunks)}")

                # Prepare chunks for embedding
                prepared_chunks, prep_stats = prepare_chunks_for_embedding(chunks)

                print(f"      Enhanced chunks: {prep_stats['processed']}")
                print(f"      Skipped: {prep_stats['skipped']}")

                if prep_stats['processed'] == 0:
                    print(f"      Warning: No chunks to embed, skipping...")
                    results.append((repo_name, chunk_type, "Skipped", "No embeddable chunks"))
                    continue

                # Generate embeddings
                print(f"      Generating embeddings...")
                result = generator.generate_embeddings(prepared_chunks)

                # Create type-specific directory
                type_dir = output_dir / chunk_type
                type_dir.mkdir(parents=True, exist_ok=True)

                # Save embeddings
                output_path = type_dir / chunk_type
                generator.save_embeddings(result, str(output_path))

                print(f"      Saved -> {chunk_type}/{chunk_type}.npy + {chunk_type}.json")

                results.append((repo_name, chunk_type, "Success", result['statistics']))

                # Collect for combined index
                all_chunks_for_repo.extend(chunks)

            except Exception as e:
                print(f"      Error: {e}")
                import traceback
                traceback.print_exc()
                results.append((repo_name, chunk_type, "Failed", str(e)))

        # Generate combined "all" index for this repository
        if all_chunks_for_repo:
            print(f"\n   Generating combined 'all' index for {repo_name}...")

            try:
                print(f"      Total chunks: {len(all_chunks_for_repo)}")

                # Prepare all chunks
                prepared_all, prep_all_stats = prepare_chunks_for_embedding(all_chunks_for_repo)

                print(f"      Enhanced: {prep_all_stats['processed']}")

                if prep_all_stats['processed'] > 0:
                    # Generate combined embeddings
                    combined_result = generator.generate_embeddings(prepared_all)

                    # Save to "all" directory
                    all_dir = output_dir / "all"
                    all_dir.mkdir(parents=True, exist_ok=True)

                    combined_path = all_dir / "all"
                    generator.save_embeddings(combined_result, str(combined_path))

                    print(f"      Saved -> all/all.npy + all.json")

                    results.append((repo_name, "all", "Success", combined_result['statistics']))

            except Exception as e:
                print(f"      Failed to generate combined index: {e}")
                results.append((repo_name, "all", "Failed", str(e)))

    # Print summary
    print(f"\n{'=' * 70}")
    print("BATCH GENERATION SUMMARY")
    print(f"{'=' * 70}\n")

    successful = [r for r in results if r[2] == "Success"]
    skipped = [r for r in results if r[2] == "Skipped"]
    failed = [r for r in results if r[2] == "Failed"]

    print(f"Successful: {len(successful)}/{len(results)}")
    if skipped:
        print(f"Skipped: {len(skipped)}/{len(results)}")
    if failed:
        print(f"Failed: {len(failed)}/{len(results)}")

    if successful:
        # Group by type
        by_type_summary = defaultdict(int)
        total_embeddings = 0

        for repo, ctype, status, stats in successful:
            if isinstance(stats, dict):
                count = stats.get('count', 0)
                by_type_summary[ctype] += count
                total_embeddings += count

        print(f"\nTotal embeddings generated: {total_embeddings}")
        print(f"\nBy type:")
        for ctype, count in sorted(by_type_summary.items()):
            print(f"   {ctype}: {count}")

    if failed:
        print(f"\nFailed:")
        for repo, ctype, status, error in failed:
            print(f"   {repo} ({ctype}): {error}")

    if skipped:
        print(f"\nSkipped:")
        for repo, ctype, status, reason in skipped:
            print(f"   {repo} ({ctype}): {reason}")

    print(f"\nOutput directory: {output_dir}")
    print(f"\nNext Step:")
    print(f"   python core/VectorDB/build_indices.py")


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced embedding generation with entity + temporal + correlation context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        python generate_embeddings.py
        python generate_embeddings.py processed/repo_name_git_chunks.json
        python generate_embeddings.py --provider openai
        python generate_embeddings.py --batch
                """
    )
    parser.add_argument('input_file', nargs='?', help='Path to chunks JSON file')
    parser.add_argument('--output-dir', default='../../data/Embeddings/', help='Output directory')
    parser.add_argument('--provider', choices=['openai', 'sentence-transformers', 'cohere', 'huggingface'])
    parser.add_argument('--model', help='Model name')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--cache-dir', default='../../data/Embeddings/embeddings_cache', help='Cache directory')
    parser.add_argument('--batch', action='store_true', help='Process all chunks files')

    args = parser.parse_args()

    if args.batch:
        batch_generate(args)
        return

    processed_dir = Path("../../data/DataProcessing") / REPO_OWNER / REPO_NAME / "chunks"
    chunks_files = sorted(
        f for f in processed_dir.glob("*_chunks.json")
        if not any(skip in f.name for skip in ['strategy', 'entities', 'aggregated'])
    )

    if not chunks_files:
        print(f"Error: No JSON files found in {processed_dir}")
        sys.exit(1)

    print(f"Found {len(chunks_files)} JSON files to embed:")
    for f in chunks_files:
        print("  ", f.name)

    provider = args.provider
    model = args.model

    cache_dir = Path(str(args.cache_dir))
    cache_dir.mkdir(parents=True, exist_ok=True)

    base_output_dir = Path(str(args.output_dir))
    output_dir = base_output_dir / REPO_OWNER / REPO_NAME
    output_dir.mkdir(parents=True, exist_ok=True)


    if not provider:
        print("Auto-detecting embedding provider...")
        provider, default_model = auto_detect_provider()
        if provider == 'openai':
            print(f"Detected OpenAI API key")
        elif provider == 'cohere':
            print(f"Detected Cohere API key")
        else:
            print(f"No API keys found - using free Sentence-Transformers")
        if not model:
            model = default_model
        print(f"   Provider: {provider}")
        print(f"   Model: {model}\n")
    else:
        default_models = {
            'openai': 'text-embedding-3-small',
            'sentence-transformers': 'all-MiniLM-L6-v2',
            'cohere': 'embed-english-v3.0',
            'huggingface': 'sentence-transformers/all-MiniLM-L6-v2'
        }
        if not model:
            model = default_models[provider]

    print(f"{'='*70}")
    print(f"ENHANCED EMBEDDING GENERATION - STEP 3")
    print(f"{'='*70}\n")

    print(f"Loading chunks from: {len(chunks_files)} files")
    all_chunks = []
    for file_path in chunks_files:
        print(f"Loading chunks from {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_chunks.extend(data)
            else:
                print(f"Warning: Skipping {file_path.name} - JSON is not a list")
                continue

    chunks = all_chunks
    print(f"\nTotal merged chunks: {len(chunks)}\n")

    chunks = load_and_inject_aggregated_tech_summary(processed_dir, chunks)

    source_type = detect_source_type(chunks)
    if len(chunks_files) == 1:
        file_name = Path(chunks_files[0]).stem
    else:
        file_name = "combined"

    if not chunks:
        print(f"Error: No chunks found in file")
        sys.exit(1)

    print(f"   File: {file_name}")
    print(f"   Source: {source_type}")
    print(f"   Total chunks: {len(chunks)}")

    chunk_types = {}
    for chunk in chunks:
        ct = chunk.get('type', 'unknown')
        chunk_types[ct] = chunk_types.get(ct, 0) + 1

    print(f"\n   Chunk types:")
    for ct, count in sorted(chunk_types.items()):
        print(f"      {ct}: {count}")

    print("\nComputing repository metrics (lines, functions, structure)...")
    repo_metrics = compute_repo_metrics(chunks)
    metrics_chunk = {
        'chunk_id': f"repo_metrics_{int(datetime.now(timezone.utc).timestamp())}",
        'type': 'repo_metrics',
        'source': 'computed',
        'content': ("Repository metrics: "
                    f"total_lines={repo_metrics['total_lines']}, "
                    f"total_functions={repo_metrics['total_functions']}, "
                    f"total_files={repo_metrics['total_files']}. "
                    "By repo: " + ", ".join(f"{r}({s['files']} files)" for r, s in repo_metrics['by_repo'].items())),
        'metadata': {
            'computed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'metrics': repo_metrics
        },
        'full_chunk': {'metrics': repo_metrics},
        'skip_embedding': False
    }
    chunks = [metrics_chunk] + chunks

    print(f"\nPreparing enhanced chunks for embedding...")
    print(f"   Extracting main content")
    print(f"   Formatting entity context")
    print(f"   Adding temporal context")
    if source_type == 'gmail':
        print(f"   Including GitHub correlation data")

    prepared_chunks, prep_stats = prepare_chunks_for_embedding(chunks)

    print(f"\n   Preparation complete:")
    print(f"      Total chunks: {prep_stats['total']}")
    print(f"      Will embed: {prep_stats['processed']}")
    print(f"      Skipped: {prep_stats['skipped']}")
    if prep_stats['raw_data_refs'] > 0:
        print(f"        Raw data refs: {prep_stats['raw_data_refs']} (too large)")
    if prep_stats['empty_content'] > 0:
        print(f"        Empty content: {prep_stats['empty_content']}")

    print(f"\n   By retrieval priority:")
    for priority in sorted(prep_stats['by_priority'].keys()):
        count = prep_stats['by_priority'][priority]
        print(f"      Priority {priority}: {count} chunks")

    if prep_stats['processed'] == 0:
        print(f"\nError: No chunks to embed!")
        sys.exit(1)

    if prepared_chunks:
        sample = prepared_chunks[0]
        print(f"\n   Sample enhanced chunk:")
        print(f"      ID: {sample.get('chunk_id', 'N/A')}")
        print(f"      Type: {sample.get('type', 'N/A')}")
        print(f"      Content length: {len(sample.get('content', ''))} chars")
        print(f"      Preview: {sample.get('content', '')[:150]}...\n")

    try:
        generator = EmbeddingGenerator(
            provider=provider,
            model=model,
            batch_size=args.batch_size,
            cache_dir=cache_dir
        )
    except Exception as e:
        print(f"\nError initializing embedding generator: {e}")
        print(f"\nInstallation guide:")
        if provider == 'openai':
            print(f"   1. pip install openai python-dotenv")
            print(f"   2. Create .env file with: OPENAI_API_KEY=your-key")
        elif provider == 'sentence-transformers':
            print(f"   pip install sentence-transformers")
        elif provider == 'cohere':
            print(f"   1. pip install cohere python-dotenv")
            print(f"   2. Create .env file with: COHERE_API_KEY=your-key")
        sys.exit(1)

    print("\nGenerating embeddings...")
    try:
        result = generator.generate_embeddings(prepared_chunks)
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        sys.exit(1)

    output_name = f"{file_name}_embeddings"
    output_path = output_dir / output_name
    generator.save_embeddings(result, str(output_path))

    print(f"\n{'='*70}")
    print("EMBEDDING GENERATION COMPLETE")
    print(f"{'='*70}")

    config = result['config']
    stats = result['statistics']

    print(f"\nConfiguration:")
    print(f"   Source: {source_type}")
    print(f"   Provider: {config['provider']}")
    print(f"   Model: {config['model']}")
    print(f"   Dimension: {config['dimension']}")
    #print(f"   Embedded: {config['embedded_chunks']}/{config['total_chunks']}")
    if config.get('skipped_chunks', 0) > 0:
        print(f"   Skipped: {config['skipped_chunks']} (empty/raw data)")

    print(f"\nEmbedding Statistics:")
    print(f"   Total embeddings: {stats.get('count', 0)}")
    print(f"   Mean norm: {stats.get('mean_norm', 0):.2f}")
    print(f"   Sparsity: {stats.get('sparsity', 0):.2%}")

    print(f"\nOutput:")
    print(f"   Vectors: {output_path}.npy ({_get_size(output_path.with_suffix('.npy'))})")
    print(f"   Metadata: {output_path}.json ({_get_size(output_path.with_suffix('.json'))})")

    if provider in ['openai', 'cohere']:
        estimate_cost(provider, model, len(prepared_chunks), stats)

    print(f"\n{'='*70}\n")
    print(f"Ready for vector DB indexing!")
    print(f"   Next: python core/VectorDB/build_indices.py\n")


if __name__ == "__main__":
    main()