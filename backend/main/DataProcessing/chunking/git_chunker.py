import json
import re
from typing import List, Dict, Any, Set, Tuple
from backend.utils.path_normalizer import (
    normalize_path,
    extract_filename,
    extract_directory,
)



def chunk_git_data(
    self, data: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, Set[str]], Dict[str, Any]]:
        """Chunk Git data with enhanced metadata, entity extraction, bidirectional linking, and code analysis"""

        repo_owner = self.repo_owner
        reponame = self.repo_name

        chunks = []
        entities = self.extract_git_entities(data)
        techstack = self.analyze_repository_code(data)

        # 🔒 Freeze global keywords to avoid cross-chunk pollution
        global_keywords = list(entities["keywords"])

        self.git_keywords.update(global_keywords)


        # Repository overview chunk
        repo_overview = {
            'chunk_id': f"{reponame}_overview",
            'type': 'repository_overview',
            'source': 'git',
            'repo_name': reponame,
            'repo_owner': repo_owner,  # Add owner for strict filtering
            'retrieval_priority': 0,
            'techstack': techstack,
            'summary': {
                'total_issues': len(data.get('issues', [])),
                'total_prs': len(data.get('prs', [])),
                'total_commits': len(data.get('commits', [])),
                'total_code_files': len(data.get('code_files', [])),
                'total_documentation': len(data.get('documentation', [])),
                'total_workflows': len(data.get('workflows', [])),
                'entities_summary': {
                    'unique_authors': len(entities['authors']),
                    'unique_issues': len(entities['issue_numbers']),
                    'unique_prs': len(entities['pr_numbers']),
                    'unique_commits': len(entities['commit_shas']),
                    'unique_files': len(entities['file_paths'])
                }
            },
            "search_hints": {
                "text": f"{reponame} repository overview tech stack languages frameworks tools structure metrics",
                "keywords": [
                    "overview",
                    "summary",
                    "tech",
                    "stack",
                    "structure",
                    "metrics",
                    "statistics",
                ],
            },
            "raw_data": {"repo_name": reponame, "techstack": techstack},
        }
        chunks.append(repo_overview)
        self.chunk_registry[repo_overview["chunk_id"]] = repo_overview

        # ------------------------------------
        # Build issue knowledge lookup map
        # ------------------------------------
        issue_knowledge_map = {}

        for item in data.get("knowledge_data", []):
            if not isinstance(item, dict):
                continue

            if item.get("event_type") == "issue":
                meta = item.get("metadata", {})
                number = meta.get("number")

                if number is not None:
                    issue_knowledge_map[number] = item


        # CHUNK ISSUES - ONE CHUNK PER ISSUE
        issues = data.get("issues", [])
        print(f"   Processing {len(issues)} issues...")

        for idx, issue in enumerate(issues):
            issue_number = issue.get("number")
            if issue_number is None:
                continue
            knowledge = issue_knowledge_map.get(issue_number, {})

            if not isinstance(issue, dict):
                continue

            chunk_id = self.generate_chunk_id(issue, f"{reponame}_issue", idx)

            # Extract comments
            comments = []
            if "comments" in issue and isinstance(issue["comments"], list):
                comments = [
                    {
                        "author": (
                            c.get("user", {}).get("login")
                            if isinstance(c.get("user"), dict)
                            else None
                        ),
                        "body": c.get("body", ""),
                        "created_at": c.get("created_at", ""),
                        "updated_at": c.get("updated_at", ""),
                    }
                    for c in issue["comments"]
                    if isinstance(c, dict)
                ]
            
            # Fallback: merge comments from knowledge_data if issue comments are missing
            if not comments and isinstance(knowledge.get("comments"), list):
                comments = knowledge["comments"]

            # Bidirectional linking
            linked_prs = issue.get("linked_prs", [])
            is_truly_resolved = issue.get("is_truly_resolved", False)
            resolution_status = issue.get("resolution_status", "unknown")
            body_text = (
                issue.get("body")
                or knowledge.get("description")
                or ""
            )

            # Extract labels properly
            labels = []
            if "labels" in issue:
                if isinstance(issue["labels"], list):
                    labels = [
                        l.get("name") if isinstance(l, dict) else str(l)
                        for l in issue["labels"]
                        if l
                    ]

            # Extract assignees properly
            assignees = []
            if "assignees" in issue:
                if isinstance(issue["assignees"], list):
                    assignees = [
                        a.get("login") if isinstance(a, dict) else str(a)
                        for a in issue["assignees"]
                        if a
                    ]

            chunk = {
                'chunk_id': chunk_id,
                'type': 'issue',
                'source': 'git',
                'repo_name': reponame,  # Ensure this matches current repo
                'repo_owner': repo_owner,  # Add owner for consistency
                'retrieval_priority': 1,
                'entities': {
                    'issue_number': issue.get('number'),
                    'author': (
                        issue.get('user', {}).get('login')
                        if isinstance(issue.get('user'), dict)
                        else None
                    ) or knowledge.get("author"),
                    'labels': labels,
                    'assignees': assignees,
                    'milestone': issue.get('milestone', {}).get('title') if isinstance(issue.get('milestone'),
                                                                                       dict) else None,
                    'linked_prs': linked_prs,
                    'is_truly_resolved': is_truly_resolved,
                    'resolution_status': resolution_status
                },
                "temporal": {
                    "created_at": issue.get("created_at"),
                    "updated_at": issue.get("updated_at"),
                    "closed_at": issue.get("closed_at"),
                },
                "content": {
                    "title": (
                        issue.get("title")
                        or knowledge.get("title")
                        or ""
                    ),
                    "body": body_text,
                    "state": issue.get("state", ""),
                    "comments_count": len(comments),
                    "labels": labels,
                },
                "comments": comments,
                "search_hints": {
                    "text": f"{knowledge.get('title', '')} {body_text}",
                    "keywords": global_keywords,
                    "linked_prs": [f"#{pr}" for pr in linked_prs],
                },
                "raw_data": issue,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            if issue.get("number"):
                self.entity_map[f"issue_{issue['number']}"].add(chunk_id)

            self.graph_extractor.process_issue(issue, linked_prs)

        # CHUNK PRS - ONE CHUNK PER PR
        prs = data.get("prs", [])
        print(f"   Processing {len(prs)} PRs...")

        for idx, pr in enumerate(prs):
            if not isinstance(pr, dict):
                continue

            chunk_id = self.generate_chunk_id(pr, f"{reponame}_pr", idx)

            # Extract reviews
            reviews = []
            if "review_comments" in pr and isinstance(pr["review_comments"], list):
                reviews = [
                    {
                        "author": (
                            r.get("user", {}).get("login")
                            if isinstance(r.get("user"), dict)
                            else None
                        ),
                        "body": r.get("body", ""),
                        "state": r.get("state", ""),
                        "submitted_at": r.get("submitted_at", ""),
                        "commit_id": r.get("commit_id", ""),
                    }
                    for r in pr["review_comments"]
                    if isinstance(r, dict)
                ]
            # Also check for 'reviews' key (some APIs use this)
            elif "reviews" in pr and isinstance(pr["reviews"], list):
                reviews = [
                    {
                        "author": (
                            r.get("user", {}).get("login")
                            if isinstance(r.get("user"), dict)
                            else None
                        ),
                        "body": r.get("body", ""),
                        "state": r.get("state", ""),
                        "submitted_at": r.get("submitted_at", ""),
                        "commit_id": r.get("commit_id", ""),
                    }
                    for r in pr["reviews"]
                    if isinstance(r, dict)
                ]

            # Extract file changes with FULL details including patches
            file_changes = []

            # Check multiple possible keys for file changes
            files_data = pr.get("changed_files") or pr.get("files") or []

            if isinstance(files_data, list):
                for f in files_data:
                    if isinstance(f, dict):
                        file_change = {
                            "filename": f.get("filename", ""),
                            "status": f.get(
                                "status", ""
                            ),  # added, modified, removed, renamed
                            "additions": f.get("additions", 0),
                            "deletions": f.get("deletions", 0),
                            "changes": f.get("changes", 0),
                            "patch": f.get(
                                "patch", ""
                            ),  # The actual diff/patch content
                            "previous_filename": f.get(
                                "previous_filename", ""
                            ),  # For renamed files
                            "blob_url": f.get("blob_url", ""),
                            "raw_url": f.get("raw_url", ""),
                            "contents_url": f.get("contents_url", ""),
                        }

                        # Only add if we have a filename
                        if file_change["filename"]:
                            file_changes.append(file_change)

            # Bidirectional linking
            linked_issues = pr.get("linked_issues", [])

            # PROPERLY DETERMINE PR STATUS - merged vs closed
            is_merged = pr.get("merged", False) or pr.get("is_merged", False)
            state = pr.get("state", "unknown")

            # Determine the actual PR status
            if is_merged:
                pr_status = "merged"
            elif state == "closed" and not is_merged:
                pr_status = "closed"
            elif state == "open":
                pr_status = "open"
            else:
                pr_status = state or "unknown"

            body_text = pr.get("body", "") or ""

            # Extract reviewers list
            reviewers = []
            for r in reviews:
                if r.get("author"):
                    reviewers.append(r["author"])
            reviewers = list(set(reviewers))  # Remove duplicates

            # Get merge information
            merged_by = None
            if pr.get("merged_by"):
                if isinstance(pr["merged_by"], dict):
                    merged_by = pr["merged_by"].get("login")
                else:
                    merged_by = str(pr["merged_by"])

            chunk = {
                'chunk_id': chunk_id,
                'type': 'pr',
                'source': 'git',
                'repo_name': reponame,
                'repo_owner': repo_owner,  # Add owner for strict filtering
                'retrieval_priority': 1,
                'entities': {
                    'pr_number': pr.get('number'),
                    'author': pr.get('user', {}).get('login') if isinstance(pr.get('user'), dict) else None,
                    'reviewers': reviewers,
                    'merged_by': merged_by,
                    'base_branch': pr.get('base', {}).get('ref') if isinstance(pr.get('base'), dict) else None,
                    'head_branch': pr.get('head', {}).get('ref') if isinstance(pr.get('head'), dict) else None,
                    'linked_issues': linked_issues,
                    'pr_status': pr_status,
                    'is_merged': is_merged
                },
                "temporal": {
                    "created_at": pr.get("created_at"),
                    "updated_at": pr.get("updated_at"),
                    "merged_at": pr.get("merged_at"),
                    "closed_at": pr.get("closed_at"),
                },
                "content": {
                    "title": pr.get("title", ""),
                    "body": body_text,
                    "state": state,
                    "merged": is_merged,
                    "mergeable": pr.get("mergeable"),
                    "mergeable_state": pr.get("mergeable_state", ""),
                    "commits_count": (
                        pr.get("commits", 0)
                        if isinstance(pr.get("commits"), int)
                        else len(pr.get("commits", []))
                    ),
                    "changed_files_count": len(file_changes),
                    "additions": pr.get("additions", 0),
                    "deletions": pr.get("deletions", 0),
                    "review_comments_count": len(reviews),
                },
                "reviews": reviews,
                "file_changes": file_changes,
                "closes_issues": linked_issues,
                "search_hints": {
                    "text": f"{pr.get('title', '')} {body_text}",
                    "keywords": global_keywords,
                    "files_modified": [f["filename"] for f in file_changes],
                },
                "raw_data": pr,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            if pr.get("number"):
                self.entity_map[f"pr_{pr['number']}"].add(chunk_id)
            
            self.graph_extractor.process_pr(pr)

        # CHUNK COMMITS - ONE CHUNK PER COMMIT
        commits = data.get("commits", [])
        print(f"   Processing {len(commits)} commits...")

        for idx, commit in enumerate(commits):
            if not isinstance(commit, dict):
                continue

            chunk_id = self.generate_chunk_id(commit, f"{reponame}_commit", idx)

            commit_data = commit.get("commit", {}) or {}
            message = commit_data.get("message", "") or ""

            # Extract files with full details
            files_modified = []
            if "files" in commit and isinstance(commit["files"], list):
                for f in commit["files"]:
                    if isinstance(f, dict):
                        files_modified.append(
                            {
                                "filename": f.get("filename", ""),
                                "status": f.get("status", ""),
                                "additions": f.get("additions", 0),
                                "deletions": f.get("deletions", 0),
                                "changes": f.get("changes", 0),
                                "patch": f.get("patch", ""),
                            }
                        )

            # Extract author and committer info
            author_info = (
                commit_data.get("author", {})
                if isinstance(commit_data.get("author"), dict)
                else {}
            )
            committer_info = (
                commit_data.get("committer", {})
                if isinstance(commit_data.get("committer"), dict)
                else {}
            )

            chunk = {
                'chunk_id': chunk_id,
                'type': 'commit',
                'source': 'git',
                'repo_name': reponame,
                'repo_owner': repo_owner,  # Add owner for strict filtering
                'retrieval_priority': 2,
                'entities': {
                    'sha': commit.get('sha'),
                    'sha_short': (commit.get('sha') or '')[:7],
                    'author': author_info.get('name'),
                    'author_email': author_info.get('email'),
                    'committer': committer_info.get('name'),
                    'committer_email': committer_info.get('email')
                },
                "temporal": {
                    "date": author_info.get("date"),
                    "author_date": author_info.get("date"),
                    "committer_date": committer_info.get("date"),
                },
                "content": {
                    "message": message,
                    "files_modified": [
                        f["filename"] for f in files_modified if f.get("filename")
                    ],
                    "stats": {
                        "total_files": len(files_modified),
                        "additions": (
                            commit.get("stats", {}).get("additions", 0)
                            if isinstance(commit.get("stats"), dict)
                            else 0
                        ),
                        "deletions": (
                            commit.get("stats", {}).get("deletions", 0)
                            if isinstance(commit.get("stats"), dict)
                            else 0
                        ),
                    },
                },
                "files": files_modified,  # Full file details with patches
                "search_hints": {
                    "text": message,
                    "keywords": global_keywords,
                },
                "raw_data": commit,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            if commit.get("sha"):
                self.entity_map[f"commit_{commit['sha'][:7]}"].add(chunk_id)

        # CHUNK CODE FILES - ONE CHUNK PER FILE
        code_files = data.get("code_files", [])
        print(f"   Processing {len(code_files)} code files...")

        for idx, codefile in enumerate(code_files):
            if not isinstance(codefile, dict):
                continue

            chunk_id = self.generate_chunk_id(codefile, f"{reponame}_code", idx)

            path = codefile.get("path")
            language = codefile.get("language") or self.code_analyzer.detect_language(
                path
            )
            content = codefile.get("content", "") or ""
            size = codefile.get("size", 0)

            ast_analysis = codefile.get("analysis")
            if path:
                self.graph_extractor.process_analysis(path, ast_analysis, content)

            # Standardize metadata fields (add standard fields alongside existing for backward compat)
            
            # Normalize path using path normalizer
            normalized_path = normalize_path(path, '') if path else ''
            normalized_filename = extract_filename(normalized_path) if normalized_path else ''
            normalized_directory = extract_directory(normalized_path) if normalized_path else ''
            
            chunk = {
                'chunk_id': chunk_id,
                'type': 'code',  # Keep for backward compat
                'chunk_type': 'code',  # Standard field
                'source': 'git',
                'repo_name': reponame,
                'repo_owner': repo_owner,
                'retrieval_priority': 2,
                # Standard file path fields (normalized)
                'file_path': normalized_path,  # Standard field - normalized
                'language': language,  # Standard field (promoted from entities)
                'filename': normalized_filename,  # Standard field - normalized
                'directory': normalized_directory,  # Standard field - normalized
                # Keep entities for backward compat (also normalized)
                'entities': {
                    'path': normalized_path,
                    'language': language,
                    'directory': normalized_directory,
                    'filename': normalized_filename
                },
                "content": {"content": content, "size": size, "analysis": ast_analysis},
                "search_hints": {
                    "text": content[:1000],
                    "keywords": global_keywords,
                },
                "raw_data": codefile,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

            if path:
                self.entity_map[f"file_{normalized_path}"].add(chunk_id)

        # CHUNK DOCUMENTATION - ONE CHUNK PER DOC
        documentation = data.get("documentation", [])
        print(f"   Processing {len(documentation)} documentation files...")

        for idx, doc in enumerate(documentation):
            if not isinstance(doc, dict):
                continue

            chunk_id = self.generate_chunk_id(doc, f"{reponame}_doc", idx)

            content_text = doc.get("content", "") or ""

            # Standardize metadata fields
            
            
            doc_path_raw = doc.get('path', '')
            # Normalize path using path normalizer
            doc_path = normalize_path(doc_path_raw, '') if doc_path_raw else ''
            doc_filename = extract_filename(doc_path) if doc_path else ''
            doc_directory = extract_directory(doc_path) if doc_path else ''
            
            chunk = {
                'chunk_id': chunk_id,
                'type': 'documentation',  # Keep for backward compat
                'chunk_type': 'documentation',  # Standard field
                'source': 'git',
                'repo_name': reponame,
                'repo_owner': repo_owner,
                'retrieval_priority': 1,
                # Standard file path fields (normalized)
                'file_path': doc_path,  # Standard field - normalized
                'filename': doc_filename,  # Standard field - normalized
                'directory': doc_directory,  # Standard field - normalized
                # Keep entities for backward compat
                'entities': {
                    'path': doc_path,
                    'title': doc.get('title', '')
                },
                "content": {
                    "content": content_text,
                    "headers": re.findall(r"^#+\s+(.+)$", content_text, re.MULTILINE),
                },
                "search_hints": {
                    "text": content_text,
                    "keywords": global_keywords,
                },
                "raw_data": doc,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

        # CHUNK WORKFLOWS - ONE CHUNK PER WORKFLOW
        workflows = data.get("workflows", [])
        print(f"   Processing {len(workflows)} workflows...")

        for idx, workflow in enumerate(workflows):
            if not isinstance(workflow, dict):
                continue

            chunk_id = self.generate_chunk_id(workflow, f"{reponame}_workflow", idx)

            # Standardize metadata fields
            
            
            workflow_path_raw = workflow.get("path", "")
            # Normalize path using path normalizer
            workflow_path = normalize_path(workflow_path_raw, '') if workflow_path_raw else ''
            workflow_filename = extract_filename(workflow_path) if workflow_path else ''
            workflow_directory = extract_directory(workflow_path) if workflow_path else ''
            
            chunk = {
                "chunk_id": chunk_id,
                "type": "workflow",  # Keep for backward compat
                "chunk_type": "workflow",  # Standard field
                "source": "git",
                "repo_name": reponame,
                "repo_owner": repo_owner,  # Add owner for consistency
                "retrieval_priority": 2,
                # Standard file path fields (normalized)
                "file_path": workflow_path,  # Standard field - normalized
                "filename": workflow_filename,  # Standard field - normalized
                "directory": workflow_directory,  # Standard field - normalized
                # Keep entities for backward compat
                "entities": {
                    "name": workflow.get("name", ""),
                    "path": workflow_path,
                },
                "content": workflow,
                "search_hints": {
                    "text": json.dumps(workflow),
                    "keywords": global_keywords,
                },
                "raw_data": workflow,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

        # CHUNK ANALYZED FILES - ONE CHUNK PER ANALYZED FILE
        analyzed_files = data.get("analyzed_files", [])
        print(f"   Processing {len(analyzed_files)} analyzed files...")

        for idx, analyzed in enumerate(analyzed_files):
            if not isinstance(analyzed, dict):
                continue

            chunk_id = self.generate_chunk_id(analyzed, f"{reponame}_analyzed", idx)

            # Standardize metadata fields
            
            
            analyzed_path_raw = analyzed.get('path', '')
            # Normalize path using path normalizer
            analyzed_path = normalize_path(analyzed_path_raw, '') if analyzed_path_raw else ''
            analyzed_filename = extract_filename(analyzed_path) if analyzed_path else ''
            analyzed_directory = extract_directory(analyzed_path) if analyzed_path else ''
            
            chunk = {
                'chunk_id': chunk_id,
                'type': 'analyzed_file',  # Keep for backward compat
                'chunk_type': 'analyzed_file',  # Standard field
                'source': 'git',
                'repo_name': reponame,
                'repo_owner': repo_owner,
                'retrieval_priority': 2,
                # Standard file path fields (normalized)
                'file_path': analyzed_path,  # Standard field - normalized
                'filename': analyzed_filename,  # Standard field - normalized
                'directory': analyzed_directory,  # Standard field - normalized
                # Keep entities for backward compat
                'entities': {
                    'path': analyzed_path
                },
                'content': analyzed,
                'search_hints': {
                    'text': json.dumps(analyzed),
                    "keywords": global_keywords
                },
                "raw_data": analyzed,
            }

            chunks.append(chunk)
            self.chunk_registry[chunk_id] = chunk

        # # CHUNK ONBOARDING (single document)
        # if "onboarding" in data and data["onboarding"]:
        #     chunk = {
        #         'chunk_id': f"{reponame}_onboarding_all",
        #         'type': 'onboarding',
        #         'source': 'git',
        #         'repo_owner': repo_owner,  # Add owner for strict filtering
        #         'repo_name': reponame,
        #         'retrieval_priority': 1,
        #         'content': data['onboarding'],
        #         'search_hints': {
        #             'text': json.dumps(data['onboarding']),
        #             "keywords": global_keywords
        #         },
        #         "raw_data": data["onboarding"],
        #     }
        #     chunks.append(chunk)
        #     self.chunk_registry[chunk["chunk_id"]] = chunk

        # # CHUNK OFFBOARDING (single document)
        # if "offboarding" in data and data["offboarding"]:
        #     chunk = {
        #         'chunk_id': f"{reponame}_offboarding_all",
        #         'type': 'offboarding',
        #         'source': 'git',
        #         'repo_owner': repo_owner,  # Add owner for strict filtering
        #         'repo_name': reponame,
        #         'retrieval_priority': 1,
        #         'content': data['offboarding'],
        #         'search_hints': {
        #             'text': json.dumps(data['offboarding']),
        #             "keywords": global_keywords
        #         },
        #         "raw_data": data["offboarding"],
        #     }
        #     chunks.append(chunk)
        #     self.chunk_registry[chunk["chunk_id"]] = chunk

        return chunks, entities, techstack