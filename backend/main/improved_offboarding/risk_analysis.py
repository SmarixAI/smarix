"""
Risk & Knowledge Analysis Module
Implements features 11-20: Knowledge loss risk, bus factor, hotspots, etc.
"""

from typing import Dict, Any, List, Set, DefaultDict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import math
import re


class RiskAnalysisProcessor:
    """
    Processes risk and knowledge analysis features (11-20)
    """
    
    def __init__(self):
        self.knowledge_units = {}
        self.hidden_dependencies = []
    
    def process(self, repo_data: Dict[str, Any], data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process all risk and knowledge analysis features
        
        Args:
            repo_data: Raw repository data
            data_collection_results: Results from data collection processor
            
        Returns:
            Dictionary with all risk analysis results
        """
        results = {
            'knowledge_loss_risk': self._calculate_knowledge_loss_risk(repo_data, data_collection_results),
            'single_owner_detection': self._detect_single_owners(repo_data, data_collection_results),
            'bus_factor_analysis': self._analyze_bus_factor(repo_data, data_collection_results),
            'knowledge_hotspots': self._detect_knowledge_hotspots(repo_data, data_collection_results),
            'cross_module_impact': self._detect_cross_module_impact(repo_data, data_collection_results),
            'criticality_scoring': self._calculate_criticality_scores(repo_data, data_collection_results),
            'knowledge_decay': self._detect_knowledge_decay(repo_data, data_collection_results),
            'hidden_dependencies': self._identify_hidden_dependencies(repo_data, data_collection_results),
            'operational_ownership': self._detect_operational_ownership(repo_data, data_collection_results),
            'oncall_responsibility': self._detect_oncall_responsibility(repo_data, data_collection_results)
        }
        
        return results
    
    def _calculate_knowledge_loss_risk(self, repo_data: Dict[str, Any], 
                                       data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 11: Knowledge loss risk scoring"""
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        current_owners = data_collection_results.get('file_ownership_history', {}).get('current_owners', {})
        
        risk_scores = {}
        
        for filename, history in ownership_history.items():
            if not history:
                continue
            
            # Calculate risk factors
            owner_count = len(set([h['author'] for h in history]))
            recent_activity = len([h for h in history if self._is_recent(h.get('date', ''), days=90)])
            total_changes = len(history)
            current_owner = current_owners.get(filename)
            
            # Risk score calculation
            risk = 0.0
            
            # Single owner = high risk
            if owner_count == 1:
                risk += 0.4
            
            # Low recent activity = medium risk
            if recent_activity < 2:
                risk += 0.2
            
            # High total changes but single owner = high risk
            if total_changes > 10 and owner_count == 1:
                risk += 0.2
            
            # No current owner = high risk
            if not current_owner:
                risk += 0.2
            
            risk_scores[filename] = {
                'risk_score': min(risk, 1.0),
                'risk_level': 'high' if risk >= 0.6 else ('medium' if risk >= 0.3 else 'low'),
                'owner_count': owner_count,
                'current_owner': current_owner,
                'recent_activity_count': recent_activity,
                'total_changes': total_changes
            }
        
        # Aggregate by owner
        owner_risk = defaultdict(lambda: {'files': [], 'total_risk': 0.0, 'high_risk_files': 0})
        for filename, risk_data in risk_scores.items():
            owner = risk_data['current_owner']
            if owner:
                owner_risk[owner]['files'].append(filename)
                owner_risk[owner]['total_risk'] += risk_data['risk_score']
                if risk_data['risk_level'] == 'high':
                    owner_risk[owner]['high_risk_files'] += 1
        
        return {
            'file_risk_scores': risk_scores,
            'owner_risk_summary': {k: {
                'file_count': len(v['files']),
                'average_risk': v['total_risk'] / len(v['files']) if v['files'] else 0,
                'high_risk_files': v['high_risk_files']
            } for k, v in owner_risk.items()},
            'high_risk_files': [f for f, d in risk_scores.items() if d['risk_level'] == 'high'],
            'total_files_analyzed': len(risk_scores)
        }
    
    def _is_recent(self, date_str: Optional[str], days: int = 90) -> bool:
        """Check if date is within specified days"""
        if not date_str:
            return False
        try:
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            cutoff = datetime.now(date.tzinfo) - timedelta(days=days)
            return date >= cutoff
        except:
            return False
    
    def _detect_single_owners(self, repo_data: Dict[str, Any], 
                             data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 12: Single-owner detection"""
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        current_owners = data_collection_results.get('file_ownership_history', {}).get('current_owners', {})
        
        single_owner_files = []
        
        for filename, history in ownership_history.items():
            unique_authors = set([h['author'] for h in history])
            if len(unique_authors) == 1:
                single_owner_files.append({
                    'file': filename,
                    'owner': list(unique_authors)[0],
                    'change_count': len(history),
                    'first_change': history[0].get('date') if history else None,
                    'last_change': history[-1].get('date') if history else None
                })
        
        # Group by owner
        owner_files = defaultdict(list)
        for file_data in single_owner_files:
            owner_files[file_data['owner']].append(file_data['file'])
        
        return {
            'single_owner_files': single_owner_files,
            'files_by_owner': dict(owner_files),
            'total_single_owner_files': len(single_owner_files),
            'owners_at_risk': len(owner_files)
        }
    
    def _analyze_bus_factor(self, repo_data: Dict[str, Any], 
                           data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 13: Bus-factor analysis"""
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        
        bus_factors = {}
        
        for filename, history in ownership_history.items():
            if not history:
                continue
            
            # Count contributions by author
            author_contributions = defaultdict(int)
            for h in history:
                author_contributions[h['author']] += 1
            
            # Calculate bus factor (minimum number of people needed to cover 50% of contributions)
            sorted_authors = sorted(author_contributions.items(), key=lambda x: x[1], reverse=True)
            total_contributions = sum(author_contributions.values())
            target = total_contributions * 0.5
            
            bus_factor = 0
            cumulative = 0
            for author, count in sorted_authors:
                bus_factor += 1
                cumulative += count
                if cumulative >= target:
                    break
            
            bus_factors[filename] = {
                'bus_factor': bus_factor,
                'total_contributors': len(author_contributions),
                'top_contributors': dict(sorted_authors[:3]),
                'risk_level': 'high' if bus_factor == 1 else ('medium' if bus_factor == 2 else 'low')
            }
        
        # Aggregate statistics
        high_risk_count = sum(1 for bf in bus_factors.values() if bf['risk_level'] == 'high')
        avg_bus_factor = sum(bf['bus_factor'] for bf in bus_factors.values()) / len(bus_factors) if bus_factors else 0
        
        return {
            'file_bus_factors': bus_factors,
            'high_risk_files': [f for f, bf in bus_factors.items() if bf['risk_level'] == 'high'],
            'average_bus_factor': round(avg_bus_factor, 2),
            'high_risk_count': high_risk_count,
            'total_files_analyzed': len(bus_factors)
        }
    
    def _detect_knowledge_hotspots(self, repo_data: Dict[str, Any], 
                                  data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 14: Knowledge hotspot detection"""
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        file_churn = data_collection_results.get('change_frequency', {}).get('file_churn', {})
        critical_subsystems = data_collection_results.get('critical_subsystems', {}).get('critical_subsystems', [])
        
        hotspots = []
        
        for filename, history in ownership_history.items():
            # Calculate hotspot score
            change_count = len(history)
            churn_data = file_churn.get(filename, {})
            churn_total = churn_data.get('total_changes', 0)
            
            # Check if in critical subsystem
            is_critical = any(filename.startswith(cs['path']) for cs in critical_subsystems)
            
            # Hotspot criteria: high changes + single/few owners + critical location
            unique_owners = len(set([h['author'] for h in history]))
            hotspot_score = (change_count * 0.3) + (churn_total * 0.2) + (is_critical * 0.3) + ((1.0 / max(unique_owners, 1)) * 0.2)
            
            if hotspot_score > 0.5:  # Threshold for hotspot
                hotspots.append({
                    'file': filename,
                    'hotspot_score': round(hotspot_score, 3),
                    'change_count': change_count,
                    'owner_count': unique_owners,
                    'is_critical_subsystem': is_critical,
                    'owners': list(set([h['author'] for h in history]))
                })
        
        # Sort by hotspot score
        hotspots.sort(key=lambda x: x['hotspot_score'], reverse=True)
        
        return {
            'knowledge_hotspots': hotspots[:20],  # Top 20
            'total_hotspots': len(hotspots),
            'high_priority_hotspots': [h for h in hotspots if h['hotspot_score'] > 0.7]
        }
    
    def _detect_cross_module_impact(self, repo_data: Dict[str, Any], 
                                    data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 15: Cross-module impact detection"""
        dependencies = data_collection_results.get('dependencies', {}).get('file_dependencies', {})
        directory_structure = data_collection_results.get('dependencies', {}).get('directory_structure', {})
        
        cross_module_impacts = []
        
        # Analyze files that are imported/included across modules
        file_importers = defaultdict(set)  # file -> {importers}
        
        for file_path, deps in dependencies.items():
            for dep in deps:
                # Find files that import this dependency
                for other_file, other_deps in dependencies.items():
                    if other_file != file_path:
                        # Check if other_file imports something from file_path's module
                        file_module = '/'.join(file_path.split('/')[:-1]) if '/' in file_path else '.'
                        for other_dep in other_deps:
                            if dep in other_dep or file_path in other_dep:
                                file_importers[file_path].add(other_file)
        
        # Identify high-impact files (imported by many other files)
        for file_path, importers in file_importers.items():
            if len(importers) > 2:  # Threshold
                cross_module_impacts.append({
                    'file': file_path,
                    'imported_by_count': len(importers),
                    'importers': list(importers),
                    'impact_level': 'high' if len(importers) > 5 else 'medium'
                })
        
        cross_module_impacts.sort(key=lambda x: x['imported_by_count'], reverse=True)
        
        return {
            'cross_module_impacts': cross_module_impacts,
            'high_impact_files': [cmi for cmi in cross_module_impacts if cmi['impact_level'] == 'high'],
            'total_impact_files': len(cross_module_impacts)
        }
    
    def _calculate_criticality_scores(self, repo_data: Dict[str, Any], 
                                     data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 16: Criticality scoring with explanation"""
        file_churn = data_collection_results.get('change_frequency', {}).get('file_churn', {})
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        critical_subsystems = data_collection_results.get('critical_subsystems', {}).get('critical_subsystems', [])
        dependencies = data_collection_results.get('dependencies', {}).get('file_dependencies', {})
        
        criticality_scores = {}
        
        for filename in set(list(file_churn.keys()) + list(ownership_history.keys())):
            score = 0.0
            factors = []
            
            # Factor 1: Change frequency (0-0.3)
            churn_data = file_churn.get(filename, {})
            change_count = churn_data.get('total_changes', 0)
            if change_count > 0:
                churn_score = min(change_count / 20.0, 1.0) * 0.3
                score += churn_score
                factors.append(f"High change frequency ({change_count} changes)")
            
            # Factor 2: Ownership concentration (0-0.25)
            history = ownership_history.get(filename, [])
            if history:
                unique_owners = len(set([h['author'] for h in history]))
                if unique_owners == 1:
                    score += 0.25
                    factors.append("Single owner (high risk)")
                elif unique_owners == 2:
                    score += 0.15
                    factors.append("Two owners (medium risk)")
            
            # Factor 3: Critical subsystem (0-0.2)
            is_critical = any(filename.startswith(cs['path']) for cs in critical_subsystems)
            if is_critical:
                score += 0.2
                factors.append("Part of critical subsystem")
            
            # Factor 4: Dependency impact (0-0.15)
            deps = dependencies.get(filename, [])
            if len(deps) > 5:
                score += 0.15
                factors.append(f"High dependency count ({len(deps)} dependencies)")
            
            # Factor 5: File location (0-0.1)
            if filename.startswith(('src/', 'lib/', 'core/', 'main.')) or '/' not in filename:
                score += 0.1
                factors.append("Core/root location")
            
            criticality_scores[filename] = {
                'criticality_score': round(min(score, 1.0), 3),
                'criticality_level': 'critical' if score >= 0.7 else ('high' if score >= 0.5 else ('medium' if score >= 0.3 else 'low')),
                'factors': factors,
                'explanation': self._generate_criticality_explanation(score, factors)
            }
        
        # Sort by criticality
        sorted_critical = sorted(criticality_scores.items(), key=lambda x: x[1]['criticality_score'], reverse=True)
        
        return {
            'criticality_scores': dict(criticality_scores),
            'most_critical_files': [{'file': f, 'score': d['criticality_score'], 'level': d['criticality_level']} 
                                   for f, d in sorted_critical[:20]],
            'critical_files_count': sum(1 for d in criticality_scores.values() if d['criticality_level'] == 'critical')
        }
    
    def _generate_criticality_explanation(self, score: float, factors: List[str]) -> str:
        """Generate human-readable explanation for criticality score"""
        if score >= 0.7:
            level = "critical"
        elif score >= 0.5:
            level = "high"
        elif score >= 0.3:
            level = "medium"
        else:
            level = "low"
        
        if factors:
            return f"This file has {level} criticality ({score:.1%}) due to: {', '.join(factors)}"
        else:
            return f"This file has {level} criticality ({score:.1%})"
    
    def _detect_knowledge_decay(self, repo_data: Dict[str, Any], 
                               data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 17: Knowledge decay detection"""
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        
        decay_detection = []
        
        for filename, history in ownership_history.items():
            if not history:
                continue
            
            # Get last change date
            last_change_date = history[-1].get('date')
            if not last_change_date:
                continue
            
            # Calculate days since last change
            try:
                last_date = datetime.fromisoformat(last_change_date.replace('Z', '+00:00'))
                days_since = (datetime.now(last_date.tzinfo) - last_date).days
            except:
                continue
            
            # Calculate change frequency over time
            recent_changes = len([h for h in history if self._is_recent(h.get('date', ''), days=180)])
            older_changes = len([h for h in history if not self._is_recent(h.get('date', ''), days=180)])
            
            # Decay indicators
            decay_score = 0.0
            indicators = []
            
            if days_since > 365:
                decay_score += 0.4
                indicators.append(f"No changes in {days_since} days")
            
            if older_changes > 0 and recent_changes == 0:
                decay_score += 0.3
                indicators.append("Historical activity but no recent changes")
            
            if recent_changes < older_changes / 2 and older_changes > 5:
                decay_score += 0.3
                indicators.append("Declining change frequency")
            
            if decay_score > 0.3:
                decay_detection.append({
                    'file': filename,
                    'decay_score': round(decay_score, 3),
                    'days_since_last_change': days_since,
                    'recent_changes': recent_changes,
                    'historical_changes': older_changes,
                    'indicators': indicators,
                    'last_change_date': last_change_date
                })
        
        decay_detection.sort(key=lambda x: x['decay_score'], reverse=True)
        
        return {
            'decay_detection': decay_detection,
            'high_decay_files': [d for d in decay_detection if d['decay_score'] > 0.6],
            'total_decay_files': len(decay_detection)
        }
    
    def _identify_hidden_dependencies(self, repo_data: Dict[str, Any], 
                                     data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 18: Hidden dependency identification"""
        dependencies = data_collection_results.get('dependencies', {}).get('file_dependencies', {})
        code_files = repo_data.get('code_files', [])
        
        hidden_deps = []
        
        # Look for files that are imported but don't exist in code_files
        all_file_paths = {f.get('path', '') for f in code_files}
        
        for file_path, deps in dependencies.items():
            for dep in deps:
                # Check if dependency is not in the repository
                if dep not in all_file_paths and not dep.startswith(('.', '/', 'http')):
                    # Check if it's a relative import that might be missing
                    if '/' in file_path:
                        base_dir = '/'.join(file_path.split('/')[:-1])
                        potential_path = f"{base_dir}/{dep}"
                        if potential_path not in all_file_paths:
                            hidden_deps.append({
                                'file': file_path,
                                'missing_dependency': dep,
                                'type': 'missing_file'
                            })
        
        # Look for circular dependencies
        circular_deps = []
        dep_graph = {f: set(deps) for f, deps in dependencies.items()}
        
        def has_circular_path(start, current, visited, path):
            if current in visited:
                if current == start and len(path) > 1:
                    return True, path + [current]
                return False, []
            
            visited.add(current)
            for neighbor in dep_graph.get(current, []):
                # Check if neighbor imports back to start
                if neighbor in dep_graph:
                    for neighbor_dep in dep_graph[neighbor]:
                        if neighbor_dep == start or neighbor_dep == current:
                            return True, path + [current, neighbor]
            
            return False, []
        
        for file_path in dep_graph:
            has_circular, path = has_circular_path(file_path, file_path, set(), [])
            if has_circular:
                circular_deps.append({
                    'files': path,
                    'type': 'circular_dependency'
                })
        
        self.hidden_dependencies = hidden_deps + circular_deps
        
        return {
            'hidden_dependencies': self.hidden_dependencies,
            'missing_files': [d for d in hidden_deps if d['type'] == 'missing_file'],
            'circular_dependencies': circular_deps,
            'total_hidden_deps': len(self.hidden_dependencies)
        }
    
    def _detect_operational_ownership(self, repo_data: Dict[str, Any], 
                                      data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 19: Operational ownership detection"""
        code_files = repo_data.get('code_files', [])
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        
        operational_files = []
        
        # Identify operational files (deployment, config, monitoring, etc.)
        operational_patterns = [
            r'deploy',
            r'config',
            r'settings',
            r'\.env',
            r'docker',
            r'kubernetes',
            r'k8s',
            r'monitoring',
            r'logging',
            r'infrastructure',
            r'ci/cd',
            r'\.github/workflows',
            r'jenkins',
            r'terraform',
            r'ansible'
        ]
        
        for file_info in code_files:
            path = file_info.get('path', '').lower()
            is_operational = any(re.search(pattern, path, re.IGNORECASE) for pattern in operational_patterns)
            
            if is_operational:
                history = ownership_history.get(file_info.get('path', ''), [])
                current_owner = history[-1]['author'] if history else None
                
                operational_files.append({
                    'file': file_info.get('path', ''),
                    'type': self._classify_operational_type(path),
                    'current_owner': current_owner,
                    'owner_count': len(set([h['author'] for h in history])) if history else 0
                })
        
        # Group by owner
        owner_operational = defaultdict(list)
        for op_file in operational_files:
            if op_file['current_owner']:
                owner_operational[op_file['current_owner']].append(op_file['file'])
        
        return {
            'operational_files': operational_files,
            'operational_files_by_owner': dict(owner_operational),
            'total_operational_files': len(operational_files),
            'owners_with_operational_responsibility': len(owner_operational)
        }
    
    def _classify_operational_type(self, path: str) -> str:
        """Classify operational file type"""
        if 'deploy' in path or 'docker' in path or 'k8s' in path:
            return 'deployment'
        elif 'config' in path or 'settings' in path or '.env' in path:
            return 'configuration'
        elif 'monitoring' in path or 'logging' in path:
            return 'monitoring'
        elif 'ci' in path or 'workflow' in path or 'jenkins' in path:
            return 'ci_cd'
        elif 'terraform' in path or 'ansible' in path:
            return 'infrastructure'
        else:
            return 'other'
    
    def _detect_oncall_responsibility(self, repo_data: Dict[str, Any], 
                                    data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 20: On-call & deployment responsibility detection"""
        operational_ownership = self._detect_operational_ownership(repo_data, data_collection_results)
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        
        oncall_responsibilities = {}
        
        # Identify on-call responsibilities based on operational files
        for op_file in operational_ownership.get('operational_files', []):
            owner = op_file['current_owner']
            if owner:
                if owner not in oncall_responsibilities:
                    oncall_responsibilities[owner] = {
                        'operational_files': [],
                        'deployment_files': [],
                        'monitoring_files': [],
                        'config_files': [],
                        'total_responsibilities': 0
                    }
                
                file_type = op_file['type']
                if file_type == 'deployment':
                    oncall_responsibilities[owner]['deployment_files'].append(op_file['file'])
                elif file_type == 'monitoring':
                    oncall_responsibilities[owner]['monitoring_files'].append(op_file['file'])
                elif file_type == 'configuration':
                    oncall_responsibilities[owner]['config_files'].append(op_file['file'])
                
                oncall_responsibilities[owner]['operational_files'].append(op_file['file'])
                oncall_responsibilities[owner]['total_responsibilities'] += 1
        
        # Also check for critical files ownership
        critical_subsystems = data_collection_results.get('critical_subsystems', {}).get('critical_subsystems', [])
        for cs in critical_subsystems:
            # Find files in this subsystem
            for filename, history in ownership_history.items():
                if filename.startswith(cs['path']):
                    if history:
                        owner = history[-1]['author']
                        if owner not in oncall_responsibilities:
                            oncall_responsibilities[owner] = {
                                'operational_files': [],
                                'deployment_files': [],
                                'monitoring_files': [],
                                'config_files': [],
                                'critical_subsystem_files': [],
                                'total_responsibilities': 0
                            }
                        if 'critical_subsystem_files' not in oncall_responsibilities[owner]:
                            oncall_responsibilities[owner]['critical_subsystem_files'] = []
                        oncall_responsibilities[owner]['critical_subsystem_files'].append(filename)
                        oncall_responsibilities[owner]['total_responsibilities'] += 1
        
        return {
            'oncall_responsibilities': {k: {
                'total_files': v['total_responsibilities'],
                'deployment_count': len(v.get('deployment_files', [])),
                'monitoring_count': len(v.get('monitoring_files', [])),
                'config_count': len(v.get('config_files', [])),
                'critical_subsystem_count': len(v.get('critical_subsystem_files', [])),
                'files': v
            } for k, v in oncall_responsibilities.items()},
            'total_oncall_owners': len(oncall_responsibilities),
            'high_responsibility_owners': [k for k, v in oncall_responsibilities.items() 
                                          if v['total_responsibilities'] > 5]
        }

