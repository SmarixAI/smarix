"""
Context building utilities for retrieval results.
"""
from typing import List, Dict, Any
from pathlib import Path
import json
from ..query_type import QueryType
from utils.metadata_normalizer import MetadataNormalizer


class ContextBuilderMixin:
    """Mixin for building context from retrieval results."""
    
    def boost_by_metadata(self, results: List[Dict], keywords: List[str], query_type: str) -> List[Dict]:
        """Boost results based on metadata and keywords."""
        for result in results:
            metadata = result.get('metadata', {})
            score = result.get('score', 0)

            priority = metadata.get('retrieval_priority', 3)
            if priority == 1:
                score *= 1.3
            elif priority == 2:
                score *= 1.1

            # Try multiple fields for content
            meta_norm = MetadataNormalizer(metadata, result)
            full_content = (meta_norm.get_content() or '').lower()
            keyword_matches = sum(1 for k in keywords if k.lower() in full_content)
            if keyword_matches > 0:
                score *= (1.0 + 0.1 * min(keyword_matches, 5))

            chunk_type = meta_norm.get_chunk_type('')
            if query_type == QueryType.FLOW_ARCHITECTURE and chunk_type in ['documentation', 'analyzed_file']:
                score *= 1.2
            elif query_type == QueryType.TROUBLESHOOTING and chunk_type == 'issue':
                score *= 1.3
            elif query_type == QueryType.QUESTION_GENERATION and chunk_type in ['documentation', 'analyzed_file', 'code']:
                score *= 1.25
            elif query_type == QueryType.PR_ISSUE_TUTORIAL and chunk_type in ['pr', 'issue', 'code']:
                score *= 1.4
            elif query_type == QueryType.PR_ISSUE_CODING_QUESTION and chunk_type in ['pr', 'issue', 'code']:
                score *= 1.4
            elif query_type == QueryType.RANDOM_PR_GENERATOR and chunk_type == 'pr':
                score *= 2.0

            result['score'] = score

        return results
    
    def build_context_from_chunks(self, chunks: List[Dict], query_type: str) -> str:
        """Build context string from retrieved chunks."""

        # Special handling for direct lookup results (exact issue/PR match)
        if chunks and chunks[0].get('source') == 'direct_lookup':
            match_type = chunks[0].get('match_type', 'unknown')
            if match_type == 'exact_issue_match':
                print(f"✅ CONTEXT_BUILDER | Direct lookup detected - building direct issue context")
                return self._build_direct_lookup_issue_context(chunks[0], query_type)
            elif match_type == 'exact_pr_match':
                print(f"✅ CONTEXT_BUILDER | Direct lookup detected - building direct PR context")
                return self._build_direct_lookup_pr_context(chunks[0], query_type)

        # Special handling for FILE_LOOKUP queries with file-specific results
        if query_type == QueryType.FILE_LOOKUP and chunks:
            file_paths = set()
            for chunk in chunks:
                meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                file_path = meta_norm.get_file_path()
                if file_path:
                    file_paths.add(file_path)

            if len(file_paths) == 1:
                return self._build_file_specific_context(chunks, list(file_paths)[0])

        context_parts: List[str] = []

        # Determine max chunks
        if query_type == QueryType.FLOW_ARCHITECTURE:
            max_chunks = 15
        elif query_type in [QueryType.HOW_TO, QueryType.FILE_LOOKUP, QueryType.QUESTION_GENERATION]:
            max_chunks = 10
        elif query_type in [QueryType.PR_ISSUE_TUTORIAL, QueryType.PR_ISSUE_CODING_QUESTION]:
            max_chunks = 20
        elif query_type == QueryType.RANDOM_PR_GENERATOR:
            max_chunks = 30
        else:
            max_chunks = 8

        for i, chunk in enumerate(chunks[:max_chunks], 1):
            metadata = chunk.get('metadata', {})
            meta_norm = MetadataNormalizer(metadata, chunk)

            context_parts.append(f"## Source {i}")

            chunk_type = meta_norm.get_chunk_type('unknown')
            context_parts.append(f"Type: {chunk_type}")

            file_path = meta_norm.get_file_path()
            if file_path:
                context_parts.append(f"File: {file_path}")

            if metadata.get('line_start') and metadata.get('line_end'):
                context_parts.append(f"Lines: {metadata['line_start']}-{metadata['line_end']}")

            issue_number = meta_norm.get_issue_number()
            if issue_number is not None:
                context_parts.append(f"Issue: #{issue_number}")

            pr_number = meta_norm.get_pr_number()
            if pr_number is not None:
                context_parts.append(f"PR: #{pr_number}")

            if metadata.get('author'):
                context_parts.append(f"Author: {metadata['author']}")

            if metadata.get('title'):
                context_parts.append(f"Title: {metadata['title']}")

            # =========================
            # PR STRUCTURED RENDERING
            # =========================
            if chunk_type == "pr":

                entities = chunk.get("entities", {})
                temporal = chunk.get("temporal", {})
                
                raw = chunk.get("raw_data", {})
                file_changes = chunk.get("file_changes", [])

                content_raw = chunk.get("content", {})

                if isinstance(content_raw, dict):
                    content_info = content_raw
                else:
                    content_info = {}

                state = content_info.get("state") or entities.get("pr_status")
                created_at = temporal.get("created_at")
                merged_at = temporal.get("merged_at")
                closed_at = temporal.get("closed_at")
                merged_by = entities.get("merged_by")

                changed_files_count = raw.get("changed_files_count")
                additions = raw.get("additions")
                deletions = raw.get("deletions")

                print("FILE CHANGES COUNT:", len(file_changes))



                if state:
                    context_parts.append(f"State: {state}")
                if created_at:
                    context_parts.append(f"Created At: {created_at}")
                if merged_at:
                    context_parts.append(f"Merged At: {merged_at}")
                if closed_at:
                    context_parts.append(f"Closed At: {closed_at}")
                if merged_by:
                    context_parts.append(f"Merged By: {merged_by}")

                raw = chunk.get("raw_data", {})
                file_changes = chunk.get("file_changes", [])

                changed_files_count = raw.get("changed_files_count")
                additions = raw.get("additions")
                deletions = raw.get("deletions")

                if changed_files_count:
                    context_parts.append(f"\nFiles Changed: {changed_files_count}")

                if additions is not None and deletions is not None:
                    context_parts.append(f"Additions: {additions}, Deletions: {deletions}")

                if file_changes:
                    context_parts.append("\nModified Files Summary:")

                    # Show most impactful files first
                    sorted_files = sorted(
                        file_changes,
                        key=lambda f: (f.get("status") == "removed", f.get("deletions", 0)),
                        reverse=True
                    )

                    for file in sorted_files[:5]:
                        context_parts.append(
                            f"- {file.get('filename')} "
                            f"({file.get('status')}, +{file.get('additions', 0)} -{file.get('deletions', 0)})"
                        )

                # Detect architectural changes
                if file_changes:
                    if any(
                        f.get("filename") == "lib/api_service.dart" and f.get("status") == "removed"
                        for f in file_changes
                    ):
                        context_parts.append("\nMajor Change: Removed legacy api_service.dart")

                    if any("v3/" in f.get("filename", "") for f in file_changes):
                        context_parts.append("Major Change: Introduced new v3 modular architecture")

                # Description
                content_dict = chunk.get("content", {})
                body = ""
                if isinstance(content_dict, dict):
                    body = content_dict.get("body", "")
                elif isinstance(content_dict, str):
                    body = content_dict


                if body and body.strip():
                    context_parts.append(f"\nDescription:\n{body}")

            # =========================
            # NON-PR CONTENT RENDERING
            # =========================
            else:
                content = meta_norm.get_content() or chunk.get('content', '')
                if content:

                    if query_type == QueryType.FLOW_ARCHITECTURE:
                        max_length = 5000
                    elif query_type in [QueryType.HOW_TO, QueryType.FILE_LOOKUP, QueryType.CONCEPTUAL, QueryType.QUESTION_GENERATION]:
                        max_length = 3500
                    elif query_type in [QueryType.PR_ISSUE_TUTORIAL, QueryType.PR_ISSUE_CODING_QUESTION]:
                        max_length = 6000
                    elif query_type == QueryType.RANDOM_PR_GENERATOR:
                        max_length = 2000
                    elif query_type == QueryType.TROUBLESHOOTING:
                        max_length = 2500
                    else:
                        max_length = 2000

                    if len(content) <= max_length:
                        context_parts.append(f"\nContent:\n{content}")
                    else:
                        truncated = content[:max_length]
                        context_parts.append(
                            f"\nContent:\n{truncated}\n... (truncated)"
                        )

            context_parts.append("\n" + "=" * 60 + "\n")

        return "\n".join(context_parts)


    def _build_direct_lookup_issue_context(self, chunk: Dict, query_type: str) -> str:
        """
        Build context specifically for direct lookup issue data.
        This handles issue data retrieved via exact issue number match.
        """
        context_parts = []
        
        # Get the full issue data
        issue_data = chunk.get('content', {})
        
        if not issue_data:
            print("⚠️ CONTEXT_BUILDER | _build_direct_lookup_issue_context: No issue data available")
            return "No data available for this issue."
        
        # Extract key information
        entities = issue_data.get('entities', {})
        temporal = issue_data.get('temporal', {})
        raw = issue_data.get('raw_data', {})
        comments = issue_data.get('comments', [])
        content_info = issue_data.get('content', {})
        
        # Header
        issue_number = entities.get('issue_number', 'Unknown')
        repo_name = issue_data.get('repo_name', '')
        repo_owner = issue_data.get('repo_owner', '')
        
        print(f"✅ CONTEXT_BUILDER | Building context for issue #{issue_number}")
        
        context_parts.append(f"# Issue #{issue_number}")
        if repo_owner and repo_name:
            context_parts.append(f"Repository: {repo_owner}/{repo_name}")
        context_parts.append("")
        
        # Core metadata
        if isinstance(content_info, dict):
            title = content_info.get('title', '')
        else:
            title = ''
        
        if title:
            context_parts.append(f"**Title:** {title}")
        
        state = content_info.get('state') or entities.get('issue_status', '')
        if state:
            context_parts.append(f"**State:** {state}")
        
        # Temporal information
        created_at = temporal.get('created_at', '')
        if created_at:
            context_parts.append(f"**Created At:** {created_at}")
        
        updated_at = temporal.get('updated_at', '')
        if updated_at:
            context_parts.append(f"**Updated At:** {updated_at}")
        
        closed_at = temporal.get('closed_at', '')
        if closed_at:
            context_parts.append(f"**Closed At:** {closed_at}")
        
        # Author and labels
        author = entities.get('author', '')
        if author:
            context_parts.append(f"**Author:** {author}")
        
        labels = entities.get('labels', [])
        if labels:
            context_parts.append(f"**Labels:** {', '.join(labels[:5])}")
        
        # Related issues/PRs
        linked_issues = entities.get('linked_issues', [])
        linked_prs = entities.get('linked_prs', [])
        
        if linked_issues or linked_prs:
            context_parts.append("")
            if linked_issues:
                context_parts.append(f"**Related Issues:** {', '.join([f'#{i}' for i in linked_issues[:5]])}")
            if linked_prs:
                context_parts.append(f"**Related PRs:** {', '.join([f'#{p}' for p in linked_prs[:5]])}")
        
        context_parts.append("")
        
        # Description/Body
        if isinstance(content_info, dict):
            body = content_info.get('body', '')
        else:
            body = str(content_info) if content_info else ''
        
        if body and body.strip():
            context_parts.append("## Description\n")
            # Limit body length
            max_length = 4000
            if len(body) > max_length:
                body = body[:max_length] + "\n... (truncated)"
            context_parts.append(body)
            context_parts.append("")
        
        # Comments summary
        if comments:
            context_parts.append(f"## Comments ({len(comments)} total)\n")
            
            # Show first 3 comments
            for i, comment in enumerate(comments[:3], 1):
                commenter = comment.get('author', 'Anonymous')
                comment_body = comment.get('body', '')
                context_parts.append(f"### Comment {i} by {commenter}")
                
                if len(comment_body) > 500:
                    comment_body = comment_body[:500] + "\n... (truncated)"
                context_parts.append(comment_body)
                context_parts.append("")
            
            if len(comments) > 3:
                context_parts.append(f"... and {len(comments) - 3} more comments")
        
        context_parts.append("")
        context_parts.append("=" * 70)
        
        return "\n".join(context_parts)


    def _build_direct_lookup_pr_context(self, chunk: Dict, query_type: str) -> str:
        """
        Build context specifically for direct lookup PR data.
        This handles PR data retrieved via exact PR number match.
        """
        context_parts = []
        
        # Get the full PR data (content field contains the complete PR chunk)
        pr_data = chunk.get('content', {})
        
        if not pr_data:
            print("⚠️ CONTEXT_BUILDER | _build_direct_lookup_pr_context: No PR data available")
            return "No data available for this PR."
        
        # Extract key information
        entities = pr_data.get('entities', {})
        temporal = pr_data.get('temporal', {})
        raw = pr_data.get('raw_data', {})
        file_changes = pr_data.get('file_changes', [])
        content_info = pr_data.get('content', {})
        
        # Header
        pr_number = entities.get('pr_number', 'Unknown')
        repo_name = pr_data.get('repo_name', '')
        repo_owner = pr_data.get('repo_owner', '')
        
        print(f"✅ CONTEXT_BUILDER | Building context for PR #{pr_number}")
        
        context_parts.append(f"# PR #{pr_number}")
        if repo_owner and repo_name:
            context_parts.append(f"Repository: {repo_owner}/{repo_name}")
        context_parts.append("")
        
        # Core metadata
        if isinstance(content_info, dict):
            title = content_info.get('title', '')
        else:
            title = ''
        
        if title:
            context_parts.append(f"**Title:** {title}")
        
        state = content_info.get('state') or entities.get('pr_status', '')
        if state:
            context_parts.append(f"**State:** {state}")
        
        # Temporal information
        created_at = temporal.get('created_at', '')
        if created_at:
            context_parts.append(f"**Created At:** {created_at}")
        
        merged_at = temporal.get('merged_at', '')
        if merged_at:
            context_parts.append(f"**Merged At:** {merged_at}")
        
        closed_at = temporal.get('closed_at', '')
        if closed_at:
            context_parts.append(f"**Closed At:** {closed_at}")
        
        merged_by = entities.get('merged_by', '')
        if merged_by:
            context_parts.append(f"**Merged By:** {merged_by}")
        
        # Statistics
        changed_files_count = raw.get('changed_files_count', 0)
        additions = raw.get('additions', 0)
        deletions = raw.get('deletions', 0)
        
        if changed_files_count:
            context_parts.append(f"**Files Changed:** {changed_files_count}")
        
        if additions is not None or deletions is not None:
            context_parts.append(f"**Additions:** {additions}, **Deletions:** {deletions}")
        
        context_parts.append("")
        
        # Modified files
        if file_changes:
            context_parts.append("## Modified Files\n")
            
            # Show most impactful files first
            sorted_files = sorted(
                file_changes,
                key=lambda f: (f.get("status") == "removed", f.get("deletions", 0)),
                reverse=True
            )
            
            for file in sorted_files[:10]:
                filename = file.get('filename', 'unknown')
                status = file.get('status', '')
                adds = file.get('additions', 0)
                dels = file.get('deletions', 0)
                context_parts.append(f"- **{filename}** ({status}, +{adds} -{dels})")
            
            if len(sorted_files) > 10:
                context_parts.append(f"... and {len(sorted_files) - 10} more files")
        
        context_parts.append("")
        
        # Description/Body
        if isinstance(content_info, dict):
            body = content_info.get('body', '')
        else:
            body = str(content_info) if content_info else ''
        
        if body and body.strip():
            context_parts.append("## Description\n")
            # Limit body length based on query type
            max_length = 4000
            if len(body) > max_length:
                body = body[:max_length] + "\n... (truncated)"
            context_parts.append(body)
        
        context_parts.append("")
        context_parts.append("=" * 70)
        
        return "\n".join(context_parts)


    def _build_file_specific_context(self, chunks: List[Dict], file_path: str) -> str:
        """
        Build context specifically for a single file query.
        Organizes chunks: overview first, then code organized by type.
        Shows actual code directly with proper structure.
        """
        from collections import defaultdict
        
        # Organize chunks by type
        overview_chunks = []
        function_chunks = []
        class_chunks = []
        method_chunks = []
        code_chunks = []
        other_chunks = []
        
        for chunk in chunks:
            meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
            chunk_type = meta_norm.get_chunk_type('')
            
            if chunk_type == 'file_overview':
                overview_chunks.append(chunk)
            elif chunk_type == 'function':
                function_chunks.append(chunk)
            elif chunk_type == 'class':
                class_chunks.append(chunk)
            elif chunk_type == 'method':
                method_chunks.append(chunk)
            elif chunk_type == 'code':
                code_chunks.append(chunk)
            else:
                other_chunks.append(chunk)
        
        context_parts = []
        
        # Header with file path
        context_parts.append(f"# File: {file_path}\n")
        
        # 1. File Overview (if exists) - show as summary
        if overview_chunks:
            overview = overview_chunks[0]  # Usually only one overview
            meta_norm = MetadataNormalizer(overview.get('metadata', {}), overview)
            overview_content = meta_norm.get_content() or overview.get('content', '')
            
            if overview_content:
                context_parts.append("## File Overview\n")
                context_parts.append(overview_content)
                context_parts.append("\n" + "=" * 70 + "\n")
        
        # 2. Classes (with their methods)
        if class_chunks:
            context_parts.append("## Classes\n")
            for chunk in class_chunks:
                meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                metadata = chunk.get('metadata', {})
                class_name = metadata.get('class_name') or metadata.get('name', 'Unknown')
                content = meta_norm.get_content() or chunk.get('content', '')
                
                if content:
                    context_parts.append(f"### Class: {class_name}\n")
                    context_parts.append(content)
                    context_parts.append("\n")
            
            context_parts.append("=" * 70 + "\n")
        
        # 3. Methods (standalone methods, not part of classes)
        if method_chunks:
            context_parts.append("## Methods\n")
            for chunk in method_chunks:
                meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                metadata = chunk.get('metadata', {})
                method_name = metadata.get('method_name') or metadata.get('name', 'Unknown')
                content = meta_norm.get_content() or chunk.get('content', '')
                
                if content:
                    context_parts.append(f"### Method: {method_name}\n")
                    context_parts.append(content)
                    context_parts.append("\n")
                    
            
            context_parts.append("=" * 70 + "\n")
        
        # 4. Functions
        if function_chunks:
            context_parts.append("## Functions\n")
            for chunk in function_chunks:
                meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                metadata = chunk.get('metadata', {})
                function_name = metadata.get('function_name') or metadata.get('name', 'Unknown')
                content = meta_norm.get_content() or chunk.get('content', '')
                
                if content:
                    context_parts.append(f"### Function: {function_name}\n")
                    context_parts.append(content)
                    context_parts.append("\n")
            
            context_parts.append("=" * 70 + "\n")
        
        # 5. Other code chunks (general code blocks)
        if code_chunks:
            context_parts.append("## Code\n")
            for chunk in code_chunks:
                content = MetadataNormalizer(chunk.get('metadata', {}), chunk).get_content() or chunk.get('content', '')
                if content:
                    # Add line numbers if available
                    metadata = chunk.get('metadata', {})
                    if metadata.get('line_start') and metadata.get('line_end'):
                        context_parts.append(f"### Lines {metadata['line_start']}-{metadata['line_end']}\n")
                    context_parts.append(content)
                    context_parts.append("\n")
            
            context_parts.append("=" * 70 + "\n")
        
        # 6. Other chunks (if any)
        if other_chunks:
            context_parts.append("## Other Content\n")
            for chunk in other_chunks:
                content = MetadataNormalizer(chunk.get('metadata', {}), chunk).get_content() or chunk.get('content', '')
                if content:
                    context_parts.append(content)
                    context_parts.append("\n")
        
        return "\n".join(context_parts)

    def build_email_context(self, emails: List[Dict]) -> str:
        """Build context string from email results."""
        email_parts = ["## Related Email Discussions\n"]

        for i, email in enumerate(emails[:3], 1):
            metadata = email.get('metadata', {})

            email_parts.append(f"### Email {i}")
            email_parts.append(f"Subject: {metadata.get('subject', 'No subject')}")
            email_parts.append(f"From: {metadata.get('from', 'Unknown')}")
            email_parts.append(f"Date: {metadata.get('date', 'Unknown')}")

            if metadata.get('correlated_issues'):
                try:
                    email_parts.append(f"Related Issues: {', '.join(metadata['correlated_issues'][:3])}")
                except Exception:
                    pass
            if metadata.get('correlated_prs'):
                try:
                    email_parts.append(f"Related PRs: {', '.join(metadata['correlated_prs'][:3])}")
                except Exception:
                    pass

            # Get content with fallback lookups
            meta_norm = MetadataNormalizer(metadata, email)
            content = meta_norm.get_content() or ''
            if content:
                if len(content) > 800:
                    content = content[:800] + "\n... (truncated)"
                email_parts.append(f"\nContent:\n{content}")

            email_parts.append("\n" + "-" * 60 + "\n")

        return "\n".join(email_parts)

    def build_metrics_context(self) -> str:
        """Build context string from repository metrics."""
        if not self.repo_metrics:
            return ""

        repositories = self.repo_metrics.get('repositories', {})
        if not repositories:
            return ""

        # Use current repo if available, otherwise use first repo in dict
        repo_owner = getattr(self, 'repo_owner', None)
        repo_name = getattr(self, 'repo_name', None)
        repo_key = f"{repo_owner}/{repo_name}" if repo_owner and repo_name else None
        
        # Try to get current repo data first
        if repo_key and repo_key in repositories:
            repo_data = repositories[repo_key]
            display_name = repo_key
        else:
            # Fallback to first repo (for backward compatibility)
            repo_key = list(repositories.keys())[0]
            repo_data = repositories[repo_key]
            display_name = repo_key

        context_parts: List[str] = ["## REPOSITORY METRICS DATA\n"]
        context_parts.append(f"Repository: {display_name}\n")

        metrics = repo_data.get('metrics', {})
        if metrics:
            context_parts.append("### Code Statistics:")
            context_parts.append(f"- Total Files: {metrics.get('total_files', 0)}")
            context_parts.append(f"- Total Lines: {metrics.get('total_lines', 0)}")
            context_parts.append(f"- Code Lines: {metrics.get('total_code_lines', 0)}")
            context_parts.append(f"- Comment Lines: {metrics.get('total_comment_lines', 0)}")
            context_parts.append(f"- Blank Lines: {metrics.get('total_blank_lines', 0)}")
            context_parts.append(f"- Code-to-Comment Ratio: {metrics.get('code_to_comment_ratio', 0):.2f}\n")

        func_class = repo_data.get('functions_and_classes', {})
        if func_class:
            context_parts.append("### Functions & Classes:")
            context_parts.append(f"- Total Functions: {func_class.get('total_functions', 0)}")
            context_parts.append(f"- Total Classes: {func_class.get('total_classes', 0)}")
            context_parts.append(f"- Average Function Length: {func_class.get('average_function_length', 0):.2f} lines")

            funcs_by_lang = func_class.get('functions_by_language', {})
            classes_by_lang = func_class.get('classes_by_language', {})

            if funcs_by_lang or classes_by_lang:
                context_parts.append("\nBy Language:")
                all_langs = set(list(funcs_by_lang.keys()) + list(classes_by_lang.keys()))
                for lang in sorted(all_langs):
                    funcs = funcs_by_lang.get(lang, 0)
                    classes = classes_by_lang.get(lang, 0)
                    context_parts.append(f"  - {lang.capitalize()}: {funcs} functions, {classes} classes")
            context_parts.append("")

        languages = repo_data.get('languages', {})
        if languages:
            all_langs = languages.get('all', {})
            primary = languages.get('primary', '')

            context_parts.append("### Programming Languages:")
            if primary:
                context_parts.append(f"- Primary: {primary.capitalize()}")

            if all_langs:
                context_parts.append("- All Languages:")
                sorted_langs = sorted(all_langs.items(), key=lambda x: x[1], reverse=True)
                for lang, count in sorted_langs:
                    context_parts.append(f"  - {lang.capitalize()}: {count} files")
            context_parts.append("")

        frameworks = repo_data.get('frameworks', {})
        if frameworks:
            detected = frameworks.get('detected', [])
            usage = frameworks.get('usage', {})

            if detected:
                context_parts.append("### Frameworks & Libraries:")
                for fw in detected:
                    use_count = usage.get(fw, 0)
                    context_parts.append(f"- {fw.capitalize()}: {use_count} occurrences")
                context_parts.append("")

        tools = repo_data.get('tools', {})
        if tools:
            detected = tools.get('detected', [])
            categories = tools.get('categories', {})

            if detected:
                context_parts.append("### Development Tools:")
                for tool in detected:
                    context_parts.append(f"- {tool}")

                if categories:
                    for category, tool_list in categories.items():
                        cat_name = category.replace('_', ' ').title()
                        context_parts.append(f"  {cat_name}: {', '.join(tool_list)}")
                context_parts.append("")

        structure = repo_data.get('structure', {})
        if structure:
            dir_count = structure.get('directory_count', 0)
            max_depth = structure.get('max_depth', 0)
            root_files = structure.get('root_files', [])
            directories = structure.get('directories', [])
            src_paths = structure.get('src_paths', [])
            test_paths = structure.get('test_paths', [])
            config_paths = structure.get('config_paths', [])

            context_parts.append("### Repository Structure:")
            context_parts.append(f"- Total Directories: {dir_count}")
            context_parts.append(f"- Maximum Depth: {max_depth} levels")

            if root_files:
                context_parts.append(f"\nRoot Configuration Files ({len(root_files)}): {', '.join(root_files)}")

            if directories:
                context_parts.append(f"\nAll Directories ({len(directories)}):")
                for directory in directories[:30]:
                    context_parts.append(f"  - {directory}/")

            if src_paths:
                context_parts.append(f"\nSource Files ({len(src_paths)} total):")
                context_parts.append("Examples:")
                for path in src_paths[:10]:
                    context_parts.append(f"  - {path}")

            if test_paths:
                context_parts.append(f"\nTest Files ({len(test_paths)} total):")
                context_parts.append("Examples:")
                for path in test_paths[:5]:
                    context_parts.append(f"  - {path}")

            if config_paths:
                context_parts.append(f"\nConfiguration Files ({len(config_paths)} total):")
                context_parts.append("Examples:")
                for path in config_paths[:5]:
                    context_parts.append(f"  - {path}")

        return "\n".join(context_parts)