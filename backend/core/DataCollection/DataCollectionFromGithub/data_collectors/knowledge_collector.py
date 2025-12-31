"""
Knowledge Signals Collector
Captures implicit knowledge from code patterns, comments, and history
"""

from typing import Dict, List, Any, Set
import re
from collections import defaultdict


class KnowledgeCollector:
    """Extracts implicit knowledge and patterns for offboarding"""
    
    def __init__(self):
        self.knowledge_indicators = {
            'workarounds': ['workaround', 'hack', 'temporary', 'fixme', 'todo'],
            'gotchas': ['gotcha', 'careful', 'warning', 'note', 'important', 'attention'],
            'decisions': ['decided', 'chosen', 'because', 'reason', 'why'],
            'domain_knowledge': ['business', 'requirement', 'spec', 'customer', 'user story'],
            'technical_debt': ['debt', 'refactor', 'cleanup', 'improve', 'optimize']
        }
    
    def collect_knowledge_data(self, 
                               code_files: List[Dict],
                               commits: List[Dict],
                               issues: List[Dict],
                               prs: List[Dict]) -> Dict[str, Any]:
        """Extract knowledge signals from various sources"""
        
        knowledge_data = {
            'code_patterns': {},
            'workarounds_and_hacks': [],
            'gotchas_and_warnings': [],
            'design_decisions': [],
            'domain_knowledge': [],
            'technical_debt': [],
            'frequently_modified_files': [],
            'complex_areas': [],
            'expert_knowledge_areas': {},
            'undocumented_features': [],
            'critical_paths': []
        }
        
        # Extract from code comments
        self._extract_from_comments(code_files, knowledge_data)
        
        # Extract from commit messages
        self._extract_from_commits(commits, knowledge_data)
        
        # Extract from issues (now with complete data)
        self._extract_from_issues(issues, knowledge_data)

        # Extract from PRs (now with complete data including file changes)
        self._extract_from_prs(prs, knowledge_data)

        # Identify complex areas
        knowledge_data['complex_areas'] = self._identify_complex_areas(code_files)

        # Map expert knowledge
        knowledge_data['expert_knowledge_areas'] = self._map_expert_knowledge(commits, prs)

        # Find frequently modified files
        knowledge_data['frequently_modified_files'] = self._find_frequently_modified(commits)

        return knowledge_data

    def _extract_from_comments(self, code_files: List[Dict], knowledge_data: Dict) -> None:
        """Extract knowledge from code comments"""

        for file_data in code_files:
            content = file_data.get('content', '')
            file_path = file_data.get('path', '')

            # Find all comments (simplified - handles # and // and /* */)
            comment_patterns = [
                r'#\s*(.+)',  # Python, Ruby, Shell
                r'//\s*(.+)',  # JavaScript, TypeScript, C++, Java
                r'/\*\s*(.+?)\*/',  # Multi-line comments
            ]

            for pattern in comment_patterns:
                comments = re.findall(pattern, content, re.DOTALL)

                for comment in comments:
                    comment_lower = comment.lower()

                    # Workarounds and hacks
                    if any(indicator in comment_lower for indicator in self.knowledge_indicators['workarounds']):
                        knowledge_data['workarounds_and_hacks'].append({
                            'file': file_path,
                            'comment': comment.strip(),
                            'type': 'workaround'
                        })

                    # Gotchas and warnings
                    if any(indicator in comment_lower for indicator in self.knowledge_indicators['gotchas']):
                        knowledge_data['gotchas_and_warnings'].append({
                            'file': file_path,
                            'comment': comment.strip(),
                            'type': 'gotcha'
                        })

                    # Design decisions
                    if any(indicator in comment_lower for indicator in self.knowledge_indicators['decisions']):
                        knowledge_data['design_decisions'].append({
                            'file': file_path,
                            'comment': comment.strip(),
                            'type': 'decision'
                        })

                    # Domain knowledge
                    if any(indicator in comment_lower for indicator in self.knowledge_indicators['domain_knowledge']):
                        knowledge_data['domain_knowledge'].append({
                            'file': file_path,
                            'comment': comment.strip(),
                            'type': 'domain'
                        })

                    # Technical debt
                    if any(indicator in comment_lower for indicator in self.knowledge_indicators['technical_debt']):
                        knowledge_data['technical_debt'].append({
                            'file': file_path,
                            'comment': comment.strip(),
                            'type': 'debt'
                        })

    def _extract_from_commits(self, commits: List[Dict], knowledge_data: Dict) -> None:
        """Extract knowledge from commit messages"""

        for commit in commits:
            message = commit.get('message', '').lower()

            # Look for explanation keywords
            if any(word in message for word in ['because', 'reason', 'why', 'fix for']):
                knowledge_data['design_decisions'].append({
                    'source': 'commit',
                    'sha': commit.get('sha'),
                    'message': commit.get('message'),
                    'author': commit.get('author', {}).get('name'),
                    'type': 'commit_explanation'
                })

            # Technical debt mentions
            if any(word in message for word in ['debt', 'refactor', 'cleanup', 'improve']):
                knowledge_data['technical_debt'].append({
                    'source': 'commit',
                    'sha': commit.get('sha'),
                    'message': commit.get('message'),
                    'type': 'debt_commit'
                })

            # Workaround mentions
            if any(word in message for word in ['workaround', 'temporary', 'hack']):
                knowledge_data['workarounds_and_hacks'].append({
                    'source': 'commit',
                    'sha': commit.get('sha'),
                    'message': commit.get('message'),
                    'type': 'workaround_commit'
                })

    def _extract_from_issues(self, issues: List[Dict], knowledge_data: Dict) -> None:
        """
        Extract knowledge from issues (NOW WITH COMPLETE DATA).

        New: Extracts from issue comments as well
        """

        for issue in issues:
            title = issue.get('title', '').lower()
            body = issue.get('body', '').lower()
            combined = title + ' ' + body

            # Also extract from ALL comments
            comments = issue.get('comments', [])
            all_comments_text = ' '.join([c.get('body', '').lower() for c in comments])
            full_text = combined + ' ' + all_comments_text

            # Bug patterns that reveal gotchas
            if any(word in full_text for word in ['gotcha', 'unexpected', 'confusing', 'tricky']):
                knowledge_data['gotchas_and_warnings'].append({
                    'source': 'issue',
                    'number': issue.get('number'),
                    'title': issue.get('title'),
                    'state': issue.get('state'),
                    'comments_count': len(comments),
                    'type': 'issue_gotcha'
                })

            # Domain knowledge in requirements
            if any(word in full_text for word in ['requirement', 'business', 'customer', 'user needs']):
                knowledge_data['domain_knowledge'].append({
                    'source': 'issue',
                    'number': issue.get('number'),
                    'title': issue.get('title'),
                    'has_detailed_discussion': len(comments) > 3,
                    'type': 'requirement'
                })

            # Undocumented features
            if any(word in full_text for word in ['undocumented', 'not documented', 'missing docs']):
                knowledge_data['undocumented_features'].append({
                    'source': 'issue',
                    'number': issue.get('number'),
                    'title': issue.get('title'),
                    'type': 'undocumented'
                })

            # Extract design decisions from issue discussions
            if len(comments) > 2:  # Issues with discussions
                for comment in comments:
                    comment_text = comment.get('body', '').lower()
                    if any(word in comment_text for word in ['decided', 'approach', 'solution', 'we should']):
                        knowledge_data['design_decisions'].append({
                            'source': 'issue_comment',
                            'issue_number': issue.get('number'),
                            'comment_id': comment.get('id'),
                            'author': comment.get('user', {}).get('login'),
                            'content_preview': comment.get('body', '')[:200],
                            'type': 'issue_discussion'
                        })

    def _extract_from_prs(self, prs: List[Dict], knowledge_data: Dict) -> None:
        """
        Extract knowledge from pull requests (NOW WITH COMPLETE DATA).

        New: Extracts from:
        - PR review comments (general reviews)
        - Line-by-line code review comments
        - Changed file analysis
        """

        for pr in prs:
            title = pr.get('title', '').lower()
            body = pr.get('body', '').lower()
            combined = title + ' ' + body

            # Extract from review comments
            review_comments = pr.get('review_comments', [])
            line_comments = pr.get('line_comments', [])

            all_review_text = ' '.join([
                r.get('body', '').lower() for r in review_comments
            ]) + ' ' + ' '.join([
                c.get('body', '').lower() for c in line_comments
            ])

            full_text = combined + ' ' + all_review_text

            # Design decisions in PR descriptions and reviews
            if any(word in full_text for word in ['approach', 'decided', 'chose', 'because']):
                knowledge_data['design_decisions'].append({
                    'source': 'pr',
                    'number': pr.get('number'),
                    'title': pr.get('title'),
                    'is_merged': pr.get('is_merged'),
                    'has_review_discussion': len(review_comments) + len(line_comments) > 0,
                    'type': 'pr_decision'
                })

            # Refactoring and debt reduction
            if any(word in full_text for word in ['refactor', 'cleanup', 'improve', 'optimize']):
                knowledge_data['technical_debt'].append({
                    'source': 'pr',
                    'number': pr.get('number'),
                    'title': pr.get('title'),
                    'files_changed': pr.get('changed_files_count', 0),
                    'type': 'refactor_pr'
                })

            # Extract knowledge from line-by-line comments (code-level insights)
            for line_comment in line_comments:
                comment_body = line_comment.get('body', '').lower()
                file_path = line_comment.get('path', '')

                # Gotchas mentioned in code review
                if any(word in comment_body for word in ['gotcha', 'careful', 'watch out', 'note']):
                    knowledge_data['gotchas_and_warnings'].append({
                        'source': 'pr_line_comment',
                        'pr_number': pr.get('number'),
                        'file': file_path,
                        'comment': line_comment.get('body', '')[:200],
                        'author': line_comment.get('user', {}).get('login'),
                        'type': 'code_review_gotcha'
                    })

                # Workarounds identified in reviews
                if any(word in comment_body for word in ['workaround', 'hack', 'temporary']):
                    knowledge_data['workarounds_and_hacks'].append({
                        'source': 'pr_line_comment',
                        'pr_number': pr.get('number'),
                        'file': file_path,
                        'comment': line_comment.get('body', '')[:200],
                        'type': 'review_workaround'
                    })

    def _identify_complex_areas(self, code_files: List[Dict]) -> List[Dict]:
        """Identify complex code areas that need documentation"""
        complex_areas = []

        for file_data in code_files:
            file_path = file_data.get('path', '')
            content = file_data.get('content', '')
            lines = file_data.get('lines', 0)

            # Calculate complexity indicators
            complexity_score = 0
            indicators = []

            # Long files
            if lines > 500:
                complexity_score += 2
                indicators.append(f'long_file ({lines} lines)')

            # High nesting depth
            max_indent = max([len(line) - len(line.lstrip()) for line in content.split('\n') if line.strip()], default=0)
            if max_indent > 16:
                complexity_score += 2
                indicators.append(f'deep_nesting ({max_indent//4} levels)')

            # Many conditional statements
            conditional_count = len(re.findall(r'\b(if|elif|else|switch|case)\b', content))
            if conditional_count > 20:
                complexity_score += 1
                indicators.append(f'many_conditionals ({conditional_count})')

            # Many function definitions
            function_count = len(re.findall(r'\b(def|function|func)\s+\w+', content))
            if function_count > 15:
                complexity_score += 1
                indicators.append(f'many_functions ({function_count})')

            # Complex regex patterns
            regex_count = len(re.findall(r'(re\.|RegExp|\/.*\/[gimuy]*)', content))
            if regex_count > 5:
                complexity_score += 1
                indicators.append(f'complex_regex ({regex_count})')

            # Low comment ratio
            comment_lines = len(re.findall(r'^\s*[#/]', content, re.MULTILINE))
            comment_ratio = comment_lines / lines if lines > 0 else 0
            if comment_ratio < 0.1 and lines > 100:
                complexity_score += 1
                indicators.append(f'low_comments ({comment_ratio:.1%})')

            if complexity_score >= 3:
                complex_areas.append({
                    'file': file_path,
                    'complexity_score': complexity_score,
                    'indicators': indicators,
                    'lines': lines,
                    'priority': 'high' if complexity_score >= 5 else 'medium'
                })

        # Sort by complexity score
        complex_areas.sort(key=lambda x: x['complexity_score'], reverse=True)
        return complex_areas[:20]  # Top 20 most complex

    def _map_expert_knowledge(self, commits: List[Dict], prs: List[Dict]) -> Dict[str, Any]:
        """
        Map which developers are experts in which areas.

        UPDATED: Now handles new PR data structure with changed_files as list of dicts
        """

        file_expertise = defaultdict(lambda: defaultdict(int))
        developer_areas = defaultdict(set)

        # Analyze commits
        for commit in commits:
            if not isinstance(commit, dict):
                continue

            author_data = commit.get('author', {})
            # Handle both dict and string author formats
            if isinstance(author_data, dict):
                author = author_data.get('name') or author_data.get('email') or 'unknown'
            else:
                author = str(author_data) if author_data else 'unknown'

            # Handle both 'changed_files' and 'changedfiles' field names
            changed_files = commit.get('changed_files', []) or commit.get('changedfiles', [])

            for file_path in changed_files:
                # File path should be a string
                if isinstance(file_path, str):
                    file_expertise[file_path][author] += 1

                    # Extract module/area from path
                    if '/' in file_path:
                        area = file_path.split('/')[0]
                        developer_areas[author].add(area)

        # Analyze PRs (UPDATED to handle new structure)
        for pr in prs:
            if not isinstance(pr, dict):
                continue

            user_data = pr.get('user', {})
            # Handle both dict and string user formats
            if isinstance(user_data, dict):
                author = user_data.get('login') or 'unknown'
            else:
                author = str(user_data) if user_data else 'unknown'

            changed_files = pr.get('changed_files', [])

            # FIXED: Extract filename from dict objects (new PR structure)
            for file_item in changed_files:
                if isinstance(file_item, dict):
                    # Extract filename from dict (new structure)
                    file_path = file_item.get('filename')
                elif isinstance(file_item, str):
                    # Already a string (old structure compatibility)
                    file_path = file_item
                else:
                    continue

                if file_path:
                    file_expertise[file_path][author] += 1

                    # Extract module/area from path
                    if '/' in file_path:
                        area = file_path.split('/')[0]
                        developer_areas[author].add(area)

        # Build expertise map
        expertise_map = {
            'file_experts': {},
            'developer_specializations': {},
            'critical_knowledge_holders': []
        }

        # File experts (top contributor to each file)
        for file_path, authors in file_expertise.items():
            if authors:
                top_expert = max(authors.items(), key=lambda x: x[1])
                expertise_map['file_experts'][file_path] = {
                    'expert': top_expert[0],
                    'contributions': top_expert[1],
                    'all_contributors': dict(authors)
                }

        # Developer specializations
        for developer, areas in developer_areas.items():
            expertise_map['developer_specializations'][developer] = {
                'areas': list(areas),
                'area_count': len(areas)
            }

        # Critical knowledge holders (experts in many areas)
        critical_developers = [
            {'developer': dev, 'areas': len(areas)}
            for dev, areas in developer_areas.items()
            if len(areas) >= 3
        ]
        critical_developers.sort(key=lambda x: x['areas'], reverse=True)
        expertise_map['critical_knowledge_holders'] = critical_developers

        return expertise_map

    def _find_frequently_modified(self, commits: List[Dict]) -> List[Dict]:
        """Find files that are frequently modified (may indicate instability)"""
        
        file_modifications = defaultdict(int)
        file_authors = defaultdict(set)
        
        for commit in commits:
            changed_files = commit.get('changed_files', [])
            author = commit.get('author', {}).get('name', 'unknown')
            
            for file_path in changed_files:
                file_modifications[file_path] += 1
                file_authors[file_path].add(author)
        
        # Build list of frequently modified files
        frequent_files = []
        for file_path, count in file_modifications.items():
            if count >= 5:  # Modified at least 5 times
                frequent_files.append({
                    'file': file_path,
                    'modification_count': count,
                    'unique_authors': len(file_authors[file_path]),
                    'authors': list(file_authors[file_path]),
                    'stability': 'unstable' if count > 15 else 'moderate'
                })
        
        # Sort by modification count
        frequent_files.sort(key=lambda x: x['modification_count'], reverse=True)
        return frequent_files[:30]  # Top 30 most modified