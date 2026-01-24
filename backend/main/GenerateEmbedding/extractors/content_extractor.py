from typing import Dict, Any, Tuple, List
import json
from datetime import datetime
from backend.main.GenerateEmbedding.extractors.commit_extractor import extract_commit_data


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
