"""
Data Collection Module
Implements features 1-10: PR, commit, and file-level activity ingestion
"""

from typing import Dict, Any, List, Set, DefaultDict, Optional
from collections import defaultdict
from datetime import datetime
import re


class DataCollectionProcessor:
    """
    Processes and aggregates data collection features (1-10)
    """
    
    def __init__(self):
        self.file_ownership_history = defaultdict(list)  # file_path -> [(author, date, commit_sha)]
        self.file_churn = defaultdict(int)  # file_path -> change_count
        self.pr_lifecycle = {}  # pr_number -> lifecycle_events
        self.dependency_map = defaultdict(set)  # file_path -> {dependencies}
        self.directory_map = defaultdict(list)  # directory -> [files]
        self.generated_code_files = set()
        self.critical_subsystems = []
        self.config_files = set()
        self.logic_files = set()
    
    def process(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process all data collection features
        
        Args:
            repo_data: Raw repository data from JSON
            
        Returns:
            Dictionary with all data collection results
        """
        results = {
            'pr_activity': self._ingest_pr_activity(repo_data),
            'commit_activity': self._ingest_commit_activity(repo_data),
            'file_activity': self._ingest_file_activity(repo_data),
            'multi_repo_contribution': self._aggregate_multi_repo_contributions(repo_data),
            'commit_timeline': self._reconstruct_commit_timeline(repo_data),
            'file_ownership_history': self._track_file_ownership_history(repo_data),
            'change_frequency': self._calculate_change_frequency(repo_data),
            'pr_lifecycle': self._track_pr_lifecycle(repo_data),
            'dependencies': self._map_dependencies(repo_data),
            'directory_structure': self._map_directory_structure(repo_data),
            'generated_code_detection': self._detect_generated_code(repo_data),
            'critical_subsystems': self._identify_critical_subsystems(repo_data),
            'config_vs_logic': self._detect_config_vs_logic(repo_data)
        }
        
        return results
    
    def _ingest_pr_activity(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 1: PR activity ingestion"""
        prs = repo_data.get('prs', [])
        
        pr_activity = {
            'total_prs': len(prs),
            'prs_by_state': defaultdict(int),
            'prs_by_author': defaultdict(int),
            'prs_by_file': defaultdict(list),  # file -> [pr_numbers]
            'pr_details': []
        }
        
        for pr in prs:
            pr_number = pr.get('number')
            state = pr.get('state', 'unknown')
            author = pr.get('user', {}).get('login', 'unknown')
            changed_files = pr.get('changed_files', [])
            
            pr_activity['prs_by_state'][state] += 1
            pr_activity['prs_by_author'][author] += 1
            
            # Track files changed in PR
            if isinstance(changed_files, list):
                for file_info in changed_files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        pr_activity['prs_by_file'][filename].append(pr_number)
            
            pr_activity['pr_details'].append({
                'number': pr_number,
                'title': pr.get('title', ''),
                'state': state,
                'author': author,
                'created_at': pr.get('created_at'),
                'merged_at': pr.get('merged_at'),
                'changed_files_count': len(changed_files) if isinstance(changed_files, list) else 0
            })
        
        return pr_activity
    
    def _ingest_commit_activity(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 2: Commit activity ingestion"""
        commits = repo_data.get('commits', [])
        
        commit_activity = {
            'total_commits': len(commits),
            'commits_by_author': defaultdict(int),
            'commits_by_date': defaultdict(int),
            'commit_timeline': [],
            'commit_details': []
        }
        
        for commit in commits:
            author_info = commit.get('author') or commit.get('commit', {}).get('author', {})
            author = author_info.get('login') or author_info.get('name', 'unknown')
            date = commit.get('commit', {}).get('author', {}).get('date') or commit.get('date')
            
            commit_activity['commits_by_author'][author] += 1
            
            if date:
                date_key = date[:10]  # YYYY-MM-DD
                commit_activity['commits_by_date'][date_key] += 1
            
            commit_activity['commit_details'].append({
                'sha': commit.get('sha', ''),
                'message': commit.get('message', '') or commit.get('commit', {}).get('message', ''),
                'author': author,
                'date': date,
                'files_count': len(commit.get('files', [])) if isinstance(commit.get('files'), list) else 0
            })
        
        return commit_activity
    
    def _ingest_file_activity(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 3: File-level activity ingestion"""
        code_files = repo_data.get('code_files', [])
        prs = repo_data.get('prs', [])
        commits = repo_data.get('commits', [])
        
        file_activity = {
            'total_files': len(code_files),
            'files_by_extension': defaultdict(int),
            'files_by_size': {
                'small': 0,  # < 1KB
                'medium': 0,  # 1KB - 100KB
                'large': 0   # > 100KB
            },
            'file_modification_count': defaultdict(int),
            'file_details': []
        }
        
        # Track file modifications from PRs and commits
        all_modified_files = set()
        
        for pr in prs:
            changed_files = pr.get('changed_files', [])
            if isinstance(changed_files, list):
                for file_info in changed_files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        all_modified_files.add(filename)
                        file_activity['file_modification_count'][filename] += 1
        
        for commit in commits:
            files = commit.get('files', [])
            if isinstance(files, list):
                for file_info in files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        all_modified_files.add(filename)
                        file_activity['file_modification_count'][filename] += 1
        
        # Analyze code files
        for file_info in code_files:
            path = file_info.get('path', '')
            size = file_info.get('size', 0)
            extension = file_info.get('extension', '')
            
            file_activity['files_by_extension'][extension] += 1
            
            if size < 1024:
                file_activity['files_by_size']['small'] += 1
            elif size < 102400:
                file_activity['files_by_size']['medium'] += 1
            else:
                file_activity['files_by_size']['large'] += 1
            
            file_activity['file_details'].append({
                'path': path,
                'size': size,
                'extension': extension,
                'modification_count': file_activity['file_modification_count'][path],
                'has_been_modified': path in all_modified_files
            })
        
        return file_activity
    
    def _aggregate_multi_repo_contributions(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 4: Multi-repo contribution aggregation"""
        prs = repo_data.get('prs', [])
        commits = repo_data.get('commits', [])
        
        contributor_stats = defaultdict(lambda: {
            'prs': 0,
            'commits': 0,
            'files_modified': set(),
            'first_contribution': None,
            'last_contribution': None
        })
        
        # Aggregate from PRs
        for pr in prs:
            author = pr.get('user', {}).get('login', 'unknown')
            contributor_stats[author]['prs'] += 1
            created_at = pr.get('created_at')
            if created_at:
                if not contributor_stats[author]['first_contribution'] or created_at < contributor_stats[author]['first_contribution']:
                    contributor_stats[author]['first_contribution'] = created_at
                if not contributor_stats[author]['last_contribution'] or created_at > contributor_stats[author]['last_contribution']:
                    contributor_stats[author]['last_contribution'] = created_at
            
            # Track files
            changed_files = pr.get('changed_files', [])
            if isinstance(changed_files, list):
                for file_info in changed_files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        contributor_stats[author]['files_modified'].add(filename)
        
        # Aggregate from commits
        for commit in commits:
            author_info = commit.get('author') or commit.get('commit', {}).get('author', {})
            author = author_info.get('login') or author_info.get('name', 'unknown')
            contributor_stats[author]['commits'] += 1
            
            date = commit.get('commit', {}).get('author', {}).get('date') or commit.get('date')
            if date:
                if not contributor_stats[author]['first_contribution'] or date < contributor_stats[author]['first_contribution']:
                    contributor_stats[author]['first_contribution'] = date
                if not contributor_stats[author]['last_contribution'] or date > contributor_stats[author]['last_contribution']:
                    contributor_stats[author]['last_contribution'] = date
            
            # Track files
            files = commit.get('files', [])
            if isinstance(files, list):
                for file_info in files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        contributor_stats[author]['files_modified'].add(filename)
        
        # Convert sets to lists for JSON serialization
        result = {}
        for author, stats in contributor_stats.items():
            result[author] = {
                'prs': stats['prs'],
                'commits': stats['commits'],
                'files_modified_count': len(stats['files_modified']),
                'files_modified': list(stats['files_modified']),
                'first_contribution': stats['first_contribution'],
                'last_contribution': stats['last_contribution']
            }
        
        return {
            'total_contributors': len(result),
            'contributors': result
        }
    
    def _reconstruct_commit_timeline(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 5: Commit timeline reconstruction"""
        commits = repo_data.get('commits', [])
        
        timeline = []
        for commit in commits:
            date = commit.get('commit', {}).get('author', {}).get('date') or commit.get('date')
            if date:
                author_info = commit.get('author') or commit.get('commit', {}).get('author', {})
                author = author_info.get('login') or author_info.get('name', 'unknown')
                
                timeline.append({
                    'sha': commit.get('sha', ''),
                    'date': date,
                    'author': author,
                    'message': (commit.get('message', '') or commit.get('commit', {}).get('message', ''))[:100],
                    'files_count': len(commit.get('files', [])) if isinstance(commit.get('files'), list) else 0
                })
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'] if x['date'] else '')
        
        return {
            'total_commits': len(timeline),
            'first_commit': timeline[0] if timeline else None,
            'last_commit': timeline[-1] if timeline else None,
            'timeline': timeline
        }
    
    def _track_file_ownership_history(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 6: File ownership history tracking"""
        commits = repo_data.get('commits', [])
        prs = repo_data.get('prs', [])
        
        ownership_history = defaultdict(list)
        
        # Track from commits
        for commit in commits:
            date = commit.get('commit', {}).get('author', {}).get('date') or commit.get('date')
            author_info = commit.get('author') or commit.get('commit', {}).get('author', {})
            author = author_info.get('login') or author_info.get('name', 'unknown')
            sha = commit.get('sha', '')
            
            files = commit.get('files', [])
            if isinstance(files, list):
                for file_info in files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        ownership_history[filename].append({
                            'author': author,
                            'date': date,
                            'commit_sha': sha,
                            'change_type': 'commit'
                        })
        
        # Track from PRs
        for pr in prs:
            date = pr.get('created_at')
            author = pr.get('user', {}).get('login', 'unknown')
            pr_number = pr.get('number')
            
            changed_files = pr.get('changed_files', [])
            if isinstance(changed_files, list):
                for file_info in changed_files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        ownership_history[filename].append({
                            'author': author,
                            'date': date,
                            'pr_number': pr_number,
                            'change_type': 'pr'
                        })
        
        # Sort each file's history by date
        for filename in ownership_history:
            ownership_history[filename].sort(key=lambda x: x.get('date', '') or '')
        
        # Calculate current owners (most recent contributor)
        current_owners = {}
        for filename, history in ownership_history.items():
            if history:
                current_owners[filename] = history[-1]['author']
        
        return {
            'ownership_history': dict(ownership_history),
            'current_owners': current_owners,
            'total_files_tracked': len(ownership_history)
        }
    
    def _calculate_change_frequency(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 7: Change frequency (churn) calculation"""
        commits = repo_data.get('commits', [])
        prs = repo_data.get('prs', [])
        
        file_churn = defaultdict(int)
        file_changes_by_date = defaultdict(lambda: defaultdict(int))
        
        # Calculate from commits
        for commit in commits:
            date = commit.get('commit', {}).get('author', {}).get('date') or commit.get('date')
            date_key = date[:10] if date else None
            
            files = commit.get('files', [])
            if isinstance(files, list):
                for file_info in files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        file_churn[filename] += 1
                        if date_key:
                            file_changes_by_date[filename][date_key] += 1
        
        # Calculate from PRs
        for pr in prs:
            changed_files = pr.get('changed_files', [])
            if isinstance(changed_files, list):
                for file_info in changed_files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        file_churn[filename] += 1
        
        # Calculate churn rates
        churn_analysis = {}
        for filename, count in file_churn.items():
            churn_analysis[filename] = {
                'total_changes': count,
                'churn_rate': 'high' if count > 10 else ('medium' if count > 5 else 'low'),
                'changes_by_date': dict(file_changes_by_date[filename])
            }
        
        return {
            'file_churn': dict(churn_analysis),
            'high_churn_files': [f for f, data in churn_analysis.items() if data['churn_rate'] == 'high'],
            'total_files_with_changes': len(churn_analysis)
        }
    
    def _track_pr_lifecycle(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 8: PR state and lifecycle tracking"""
        prs = repo_data.get('prs', [])
        
        lifecycle_data = {}
        
        for pr in prs:
            pr_number = pr.get('number')
            if not pr_number:
                continue
            
            lifecycle_data[pr_number] = {
                'state': pr.get('state', 'unknown'),
                'is_merged': pr.get('is_merged', False) or pr.get('merged_at') is not None,
                'created_at': pr.get('created_at'),
                'updated_at': pr.get('updated_at'),
                'closed_at': pr.get('closed_at'),
                'merged_at': pr.get('merged_at'),
                'lifecycle_stage': self._determine_pr_stage(pr),
                'duration_days': self._calculate_pr_duration(pr)
            }
        
        # Aggregate statistics
        stages = defaultdict(int)
        for pr_data in lifecycle_data.values():
            stages[pr_data['lifecycle_stage']] += 1
        
        return {
            'pr_lifecycles': lifecycle_data,
            'stage_distribution': dict(stages),
            'total_prs_tracked': len(lifecycle_data)
        }
    
    def _determine_pr_stage(self, pr: Dict[str, Any]) -> str:
        """Determine current stage of PR"""
        if pr.get('merged_at'):
            return 'merged'
        elif pr.get('closed_at'):
            return 'closed'
        elif pr.get('state') == 'open':
            return 'open'
        else:
            return 'unknown'
    
    def _calculate_pr_duration(self, pr: Dict[str, Any]) -> Optional[float]:
        """Calculate PR duration in days"""
        created = pr.get('created_at')
        closed = pr.get('closed_at') or pr.get('merged_at')
        
        if created and closed:
            try:
                from datetime import datetime
                created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                closed_dt = datetime.fromisoformat(closed.replace('Z', '+00:00'))
                duration = (closed_dt - created_dt).total_seconds() / 86400
                return round(duration, 2)
            except:
                return None
        return None
    
    def _map_dependencies(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 9: Dependency and directory mapping"""
        code_files = repo_data.get('code_files', [])
        dependencies = repo_data.get('dependencies', [])
        
        # Map file dependencies (imports, includes, requires)
        dependency_map = defaultdict(set)
        
        for file_info in code_files:
            path = file_info.get('path', '')
            content = file_info.get('content', '')
            
            if not content:
                continue
            
            # Detect imports/includes based on file extension
            if path.endswith('.py'):
                # Python imports
                imports = re.findall(r'^(?:from\s+(\S+)\s+)?import\s+(\S+)', content, re.MULTILINE)
                for match in imports:
                    module = match[0] if match[0] else match[1]
                    dependency_map[path].add(module.split('.')[0])
            elif path.endswith(('.c', '.cpp', '.h', '.hpp')):
                # C/C++ includes
                includes = re.findall(r'#include\s+[<"]([^>"]+)[>"]', content)
                for include in includes:
                    dependency_map[path].add(include)
            elif path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                # JavaScript/TypeScript imports
                imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)
                for imp in imports:
                    dependency_map[path].add(imp.split('/')[0])
        
        # Directory structure
        directory_map = defaultdict(list)
        for file_info in code_files:
            path = file_info.get('path', '')
            if path:
                directory = '/'.join(path.split('/')[:-1]) if '/' in path else '.'
                directory_map[directory].append(path)
        
        return {
            'file_dependencies': {k: list(v) for k, v in dependency_map.items()},
            'directory_structure': dict(directory_map),
            'external_dependencies': dependencies,
            'total_files_with_deps': len(dependency_map)
        }
    
    def _map_directory_structure(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Helper for directory mapping"""
        return self._map_dependencies(repo_data)['directory_structure']
    
    def _detect_generated_code(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 10: Detection of generated vs handwritten code"""
        code_files = repo_data.get('code_files', [])
        
        generated_files = []
        handwritten_files = []
        
        generated_indicators = [
            r'generated',
            r'auto.?generated',
            r'do not edit',
            r'automatically generated',
            r'code generator',
            r'@generated'
        ]
        
        for file_info in code_files:
            path = file_info.get('path', '').lower()
            content = file_info.get('content', '').lower()
            
            is_generated = False
            
            # Check file path
            for indicator in generated_indicators:
                if re.search(indicator, path):
                    is_generated = True
                    break
            
            # Check file content (first 500 chars)
            if not is_generated and content:
                content_sample = content[:500]
                for indicator in generated_indicators:
                    if re.search(indicator, content_sample):
                        is_generated = True
                        break
            
            if is_generated:
                generated_files.append(file_info.get('path', ''))
                self.generated_code_files.add(file_info.get('path', ''))
            else:
                handwritten_files.append(file_info.get('path', ''))
        
        return {
            'generated_files': generated_files,
            'handwritten_files': handwritten_files,
            'generated_count': len(generated_files),
            'handwritten_count': len(handwritten_files),
            'generation_ratio': len(generated_files) / len(code_files) if code_files else 0
        }
    
    def _identify_critical_subsystems(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 11: Identification of critical subsystems"""
        code_files = repo_data.get('code_files', [])
        prs = repo_data.get('prs', [])
        commits = repo_data.get('commits', [])
        
        # Calculate file criticality scores
        file_scores = defaultdict(float)
        
        # Factor 1: Number of changes
        change_counts = defaultdict(int)
        for pr in prs:
            changed_files = pr.get('changed_files', [])
            if isinstance(changed_files, list):
                for file_info in changed_files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        change_counts[filename] += 1
        
        for commit in commits:
            files = commit.get('files', [])
            if isinstance(files, list):
                for file_info in files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    if filename:
                        change_counts[filename] += 1
        
        # Factor 2: File size (larger = potentially more critical)
        file_sizes = {}
        for file_info in code_files:
            path = file_info.get('path', '')
            size = file_info.get('size', 0)
            file_sizes[path] = size
        
        # Factor 3: File location (root/core files often more critical)
        for filename in change_counts:
            score = change_counts[filename] * 0.4  # Change frequency weight
            if filename in file_sizes:
                score += min(file_sizes[filename] / 10000, 1.0) * 0.3  # Size weight
            if '/' not in filename or filename.startswith(('src/', 'lib/', 'core/', 'main.')):
                score += 0.3  # Location weight
            
            file_scores[filename] = score
        
        # Group by directory
        subsystem_scores = defaultdict(float)
        for filename, score in file_scores.items():
            directory = '/'.join(filename.split('/')[:-1]) if '/' in filename else 'root'
            subsystem_scores[directory] += score
        
        # Identify critical subsystems (top 20%)
        sorted_subsystems = sorted(subsystem_scores.items(), key=lambda x: x[1], reverse=True)
        critical_count = max(1, len(sorted_subsystems) // 5)
        critical_subsystems = [{'path': path, 'score': score} for path, score in sorted_subsystems[:critical_count]]
        
        self.critical_subsystems = critical_subsystems
        
        return {
            'critical_subsystems': critical_subsystems,
            'subsystem_scores': dict(subsystem_scores),
            'file_criticality_scores': dict(file_scores),
            'total_subsystems': len(subsystem_scores)
        }
    
    def _detect_config_vs_logic(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 12: Configuration vs logic change detection"""
        code_files = repo_data.get('code_files', [])
        prs = repo_data.get('prs', [])
        
        config_patterns = [
            r'\.(json|yaml|yml|toml|ini|conf|config|properties)$',
            r'config/',
            r'settings',
            r'\.env',
            r'package\.json',
            r'requirements\.txt',
            r'pom\.xml',
            r'build\.gradle'
        ]
        
        config_files = []
        logic_files = []
        
        for file_info in code_files:
            path = file_info.get('path', '')
            is_config = False
            
            for pattern in config_patterns:
                if re.search(pattern, path, re.IGNORECASE):
                    is_config = True
                    break
            
            if is_config:
                config_files.append(path)
                self.config_files.add(path)
            else:
                logic_files.append(path)
                self.logic_files.add(path)
        
        # Analyze PR changes
        config_changes = []
        logic_changes = []
        
        for pr in prs:
            changed_files = pr.get('changed_files', [])
            if isinstance(changed_files, list):
                pr_config_changes = []
                pr_logic_changes = []
                
                for file_info in changed_files:
                    if isinstance(file_info, dict):
                        filename = file_info.get('filename', '')
                    else:
                        filename = str(file_info)
                    
                    if filename in self.config_files:
                        pr_config_changes.append(filename)
                    elif filename in self.logic_files:
                        pr_logic_changes.append(filename)
                
                if pr_config_changes:
                    config_changes.append({
                        'pr_number': pr.get('number'),
                        'files': pr_config_changes
                    })
                if pr_logic_changes:
                    logic_changes.append({
                        'pr_number': pr.get('number'),
                        'files': pr_logic_changes
                    })
        
        return {
            'config_files': config_files,
            'logic_files': logic_files,
            'config_changes_in_prs': config_changes,
            'logic_changes_in_prs': logic_changes,
            'config_file_count': len(config_files),
            'logic_file_count': len(logic_files)
        }

