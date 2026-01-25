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
        # Special handling for FILE_LOOKUP queries with file-specific results
        if query_type == QueryType.FILE_LOOKUP and chunks:
            # Check if all chunks are from the same file (file-specific query)
            file_paths = set()
            for chunk in chunks:
                meta_norm = MetadataNormalizer(chunk.get('metadata', {}), chunk)
                file_path = meta_norm.get_file_path()
                if file_path:
                    file_paths.add(file_path)
            
            # If all chunks are from a single file, use file-specific context builder
            if len(file_paths) == 1:
                return self._build_file_specific_context(chunks, list(file_paths)[0])
        
        # Regular context building for other cases
        context_parts: List[str] = []

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
            # Use metadata normalizer for unified access
            meta_norm = MetadataNormalizer(metadata, chunk)

            context_parts.append(f"## Source {i}")
            
            # Get chunk type with fallback lookups
            chunk_type = meta_norm.get_chunk_type('unknown')
            context_parts.append(f"Type: {chunk_type}")

            # Get file path with fallback lookups
            file_path = meta_norm.get_file_path()
            if file_path:
                context_parts.append(f"File: {file_path}")

            if metadata.get('line_start') and metadata.get('line_end'):
                context_parts.append(f"Lines: {metadata['line_start']}-{metadata['line_end']}")

            # Get issue/PR numbers with fallback lookups
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

            # Get content with fallback lookups
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

                if len(content) <= max_length * 1.1:
                    context_parts.append(f"\nContent:\n{content}")
                else:
                    truncated = content[:max_length]

                    last_newline = truncated.rfind('\n\n')
                    if last_newline > int(max_length * 0.8):
                        truncated = truncated[:last_newline]
                    elif truncated.rfind('\n') > int(max_length * 0.9):
                        truncated = truncated[:truncated.rfind('\n')]

                    context_parts.append(f"\nContent:\n{truncated}\n... (truncated, {len(content) - len(truncated)} chars omitted)")

            context_parts.append("\n" + "=" * 60 + "\n")

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