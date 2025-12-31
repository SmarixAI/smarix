"""
Relationship Mapper
Maps complex relationships between issues, PRs, commits, and files
"""

from typing import Dict, List, Any, Set
from collections import defaultdict


class RelationshipMapper:
    """
    Maps relationships:
    - Issue -> PR -> Commits -> Files
    - Developer -> Files (ownership)
    - File -> Dependencies
    - Knowledge threads
    """
    
    def __init__(self, repo_data: Dict[str, Any]):
        self.repo_data = repo_data
        self.issues = {i.get('number'): i for i in repo_data.get('issues', []) if i.get('number')}
        self.prs = {p.get('number'): p for p in repo_data.get('prs', []) if p.get('number')}
        self.commits = {c.get('sha'): c for c in repo_data.get('commits', []) if c.get('sha')}
    
    def map_relationships(self, enriched_chunks: List[Dict[str, Any]], 
                         knowledge_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Map all relationships"""
        
        relationships = {
            'issue_pr_links': self._map_issue_pr_links(),
            'pr_commit_links': self._map_pr_commit_links(),
            'commit_file_links': self._map_commit_file_links(),
            'file_dependencies': self._map_file_dependencies(enriched_chunks),
            'developer_ownership': self._map_developer_ownership(),
            'knowledge_threads': self._build_knowledge_threads(),
            'cross_references': self._find_cross_references(enriched_chunks)
        }
        
        return relationships
    
    def _map_issue_pr_links(self) -> List[Dict[str, Any]]:
        """Map issues to PRs that fix them"""
        links = []
        
        for pr_number, pr in self.prs.items():
            linked_issues = (
                pr.get('linked_issues', []) or 
                pr.get('linked_issue_numbers', []) or
                []
            )
            
            if not linked_issues:
                linked_issues = self._extract_issue_refs_from_text(
                    pr.get('title', ''),
                    pr.get('body', '') or pr.get('body_preview', '')
                )
            
            for issue_number in linked_issues:
                if issue_number in self.issues:
                    links.append({
                        'issue_number': issue_number,
                        'issue_title': self.issues[issue_number].get('title'),
                        'pr_number': pr_number,
                        'pr_title': pr.get('title'),
                        'is_merged': pr.get('is_merged', False),
                        'link_type': 'fixes'
                    })
        
        for issue_number, issue in self.issues.items():
            referenced_prs = (
                issue.get('referenced_prs', []) or
                []
            )
            
            for pr_number in referenced_prs:
                if not any(l['issue_number'] == issue_number and l['pr_number'] == pr_number for l in links):
                    if pr_number in self.prs:
                        links.append({
                            'issue_number': issue_number,
                            'issue_title': issue.get('title'),
                            'pr_number': pr_number,
                            'pr_title': self.prs[pr_number].get('title'),
                            'is_merged': self.prs[pr_number].get('is_merged', False),
                            'link_type': 'references'
                        })
        
        return links
    
    def _extract_issue_refs_from_text(self, title: str, body: str) -> List[int]:
        """Extract issue references from text"""
        import re
        
        issue_numbers = set()
        text = f"{title} {body}".lower()
        
        # Common patterns: #123, fixes #123, closes #123, etc.
        patterns = [
            r'#(\d+)',
            r'issue[s]?\s*#?(\d+)',
            r'fix(?:es|ed)?\s*#?(\d+)',
            r'close[sd]?\s*#?(\d+)',
            r'resolve[sd]?\s*#?(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            issue_numbers.update(int(m) for m in matches if m.isdigit())
        
        return list(issue_numbers)
    
    def _map_pr_commit_links(self) -> List[Dict[str, Any]]:
        """Map PRs to their commits"""
        links = []
        
        for pr_number, pr in self.prs.items():
            linked_commits = (
                pr.get('linked_commits', []) or
                pr.get('commits', []) or
                pr.get('commit_shas', []) or
                []
            )
            
            for commit_sha in linked_commits:
                if commit_sha in self.commits:
                    commit = self.commits[commit_sha]
                    links.append({
                        'pr_number': pr_number,
                        'pr_title': pr.get('title'),
                        'commit_sha': commit_sha,
                        'commit_message': commit.get('message', '')[:100],
                        'author': commit.get('author', {}).get('name'),
                        'link_type': 'includes'
                    })
        
        return links
    
    def _map_commit_file_links(self) -> List[Dict[str, Any]]:
        """Map commits to changed files"""
        links = []
        
        for commit_sha, commit in self.commits.items():
            changed_files = (
                commit.get('changed_files', []) or
                commit.get('files', []) or
                []
            )
            
            file_paths = []
            for f in changed_files:
                if isinstance(f, dict):
                    file_paths.append(f.get('filename') or f.get('path', ''))
                else:
                    file_paths.append(str(f))
            
            for file_path in file_paths:
                if file_path:  # Skip empty strings
                    links.append({
                        'commit_sha': commit_sha,
                        'commit_message': commit.get('message', '')[:100],
                        'file_path': file_path,
                        'author': commit.get('author', {}).get('name'),
                        'link_type': 'modifies'
                    })
        
        return links
    
    def _map_file_dependencies(self, enriched_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map file dependencies from imports and references"""
        dependencies = []
        file_imports = defaultdict(set)
        
        for chunk in enriched_chunks:
            if chunk.get('chunk_type') != 'code':
                continue
            
            source_file = chunk.get('file_path')
            if not source_file:
                continue
            
            # Get imports from entities
            entities = chunk.get('entities', {})
            modules = entities.get('modules', [])
            
            for module in modules:
                file_imports[source_file].add(module)
            
            # Get file references
            for ref_file in chunk.get('mentioned_files', []):
                file_imports[source_file].add(ref_file)
        
        for source, targets in file_imports.items():
            for target in targets:
                dependencies.append({
                    'source_file': source,
                    'target_file': target,
                    'dependency_type': 'imports'
                })
        
        return dependencies
    
    def _map_developer_ownership(self) -> Dict[str, Any]:
        """Map developer ownership from repo data"""
        dev_summary = self.repo_data.get('developer_summary', {})
        
        ownership = {
            'file_owners': dev_summary.get('ownership_map', {}),
            'top_contributors': dev_summary.get('contributors', [])[:10],
            'activity_summary': dev_summary.get('activity_summary', {})
        }
        
        # Add expert knowledge from offboarding
        offboarding = self.repo_data.get('offboarding', {})
        expert_map = offboarding.get('expert_knowledge_map', {})
        
        if expert_map:
            ownership['expert_areas'] = expert_map.get('file_experts', {})
            ownership['critical_knowledge_holders'] = expert_map.get('critical_knowledge_holders', [])
        
        return ownership
    
    def _build_knowledge_threads(self) -> List[Dict[str, Any]]:
        """Build knowledge threads connecting issues -> PRs -> commits -> files"""
        threads = []
        
        for issue_number, issue in self.issues.items():
            thread = {
                'issue_number': issue_number,
                'issue_title': issue.get('title'),
                'issue_state': issue.get('state'),
                'related_prs': [],
                'related_commits': [],
                'affected_files': set()
            }
            
            for pr_number, pr in self.prs.items():
                linked_issues = (
                    pr.get('linked_issues', []) or
                    pr.get('linked_issue_numbers', []) or
                    []
                )
                
                if not linked_issues:
                    linked_issues = self._extract_issue_refs_from_text(
                        pr.get('title', ''),
                        pr.get('body', '') or pr.get('body_preview', '')
                    )
                
                if issue_number in linked_issues:
                    pr_data = {
                        'pr_number': pr_number,
                        'pr_title': pr.get('title'),
                        'is_merged': pr.get('is_merged'),
                        'commits': []
                    }
                    
                    pr_commits = (
                        pr.get('linked_commits', []) or
                        pr.get('commits', []) or
                        []
                    )
                    
                    for commit_sha in pr_commits:
                        if commit_sha in self.commits:
                            commit = self.commits[commit_sha]
                            pr_data['commits'].append(commit_sha)
                            
                            changed_files = (
                                commit.get('changed_files', []) or
                                commit.get('files', []) or
                                []
                            )
                            
                            for f in changed_files:
                                if isinstance(f, dict):
                                    file_path = f.get('filename') or f.get('path', '')
                                else:
                                    file_path = str(f)
                                if file_path:
                                    thread['affected_files'].add(file_path)
                    
                    thread['related_prs'].append(pr_data)
            
            referenced_prs = issue.get('referenced_prs', []) or []
            for pr_number in referenced_prs:
                if not any(p['pr_number'] == pr_number for p in thread['related_prs']):
                    if pr_number in self.prs:
                        pr = self.prs[pr_number]
                        pr_data = {
                            'pr_number': pr_number,
                            'pr_title': pr.get('title'),
                            'is_merged': pr.get('is_merged'),
                            'commits': []
                        }
                        
                        pr_commits = (
                            pr.get('linked_commits', []) or
                            pr.get('commits', []) or
                            []
                        )
                        
                        for commit_sha in pr_commits:
                            if commit_sha in self.commits:
                                commit = self.commits[commit_sha]
                                pr_data['commits'].append(commit_sha)
                                
                                changed_files = (
                                    commit.get('changed_files', []) or
                                    commit.get('files', []) or
                                    []
                                )
                                
                                for f in changed_files:
                                    if isinstance(f, dict):
                                        file_path = f.get('filename') or f.get('path', '')
                                    else:
                                        file_path = str(f)
                                    if file_path:
                                        thread['affected_files'].add(file_path)
                        
                        thread['related_prs'].append(pr_data)
            
            for commit_sha, commit in self.commits.items():
                linked_issues = (
                    commit.get('linked_issues', []) or
                    []
                )
                
                if not linked_issues:
                    linked_issues = self._extract_issue_refs_from_text(
                        commit.get('message', ''), ''
                    )
                
                if issue_number in linked_issues:
                    if commit_sha not in thread['related_commits']:
                        thread['related_commits'].append(commit_sha)
                        
                        changed_files = (
                            commit.get('changed_files', []) or
                            commit.get('files', []) or
                            []
                        )
                        
                        for f in changed_files:
                            if isinstance(f, dict):
                                file_path = f.get('filename') or f.get('path', '')
                            else:
                                file_path = str(f)
                            if file_path:
                                thread['affected_files'].add(file_path)
            
            thread['affected_files'] = list(thread['affected_files'])
            
            if thread['related_prs'] or thread['related_commits'] or thread['affected_files']:
                threads.append(thread)
        
        return threads
    
    def _find_cross_references(self, enriched_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find cross-references between chunks"""
        cross_refs = []
        
        # Build index of chunk IDs by mentioned entities
        entity_index = defaultdict(list)
        
        for chunk in enriched_chunks:
            chunk_id = chunk['chunk_id']
            
            # Index by file references
            for file in chunk.get('mentioned_files', []):
                entity_index[f"file:{file}"].append(chunk_id)
            
            for person in chunk.get('mentioned_people', []):
                entity_index[f"person:{person}"].append(chunk_id)
            
            for api in chunk.get('mentioned_apis', []):
                entity_index[f"api:{api}"].append(chunk_id)
            
            entities = chunk.get('entities', {})
            for func in entities.get('functions', []):
                entity_index[f"function:{func}"].append(chunk_id)
            for cls in entities.get('classes', []):
                entity_index[f"class:{cls}"].append(chunk_id)
        
        for entity_key, chunk_ids in entity_index.items():
            if len(chunk_ids) > 1:
                entity_type, entity_name = entity_key.split(':', 1)
                cross_refs.append({
                    'entity_type': entity_type,
                    'entity_name': entity_name,
                    'referencing_chunks': chunk_ids,
                    'reference_count': len(chunk_ids)
                })
        
        cross_refs.sort(key=lambda x: x['reference_count'], reverse=True)
        
        return cross_refs[:100]