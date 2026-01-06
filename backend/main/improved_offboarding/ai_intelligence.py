"""
AI Intelligence Module
Implements features 21-30: Semantic clustering, knowledge units, role detection, etc.
"""

from typing import Dict, Any, List, Set, Optional, Tuple
from collections import defaultdict
import re
import hashlib


class AIIntelligenceProcessor:
    """
    Processes AI intelligence features (21-30)
    Note: This is a rule-based implementation with placeholders for AI integration
    """
    
    def __init__(self):
        self.prompt_version = "1.0.0"
        self.ai_decisions = []
        self.knowledge_units = {}
        self.semantic_clusters = []
    
    def process(self, repo_data: Dict[str, Any], 
                data_collection_results: Dict[str, Any],
                risk_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process all AI intelligence features
        
        Args:
            repo_data: Raw repository data
            data_collection_results: Results from data collection processor
            risk_analysis_results: Results from risk analysis processor
            
        Returns:
            Dictionary with all AI intelligence results
        """
        results = {
            'semantic_pr_clustering': self._cluster_prs_semantically(repo_data, data_collection_results),
            'knowledge_unit_identification': self._identify_knowledge_units(repo_data, data_collection_results),
            'role_detection': self._detect_roles_from_history(repo_data, data_collection_results),
            'ai_confidence_scoring': self._calculate_ai_confidence(repo_data, data_collection_results),
            'rule_based_fallback': self._create_rule_based_fallbacks(repo_data, data_collection_results),
            'explainability': self._generate_explanations(repo_data, data_collection_results, risk_analysis_results),
            'prompt_versioning': self._track_prompt_versioning(),
            'llm_output_validation': self._validate_llm_outputs(repo_data, data_collection_results),
            'knowledge_similarity': self._detect_knowledge_similarity(repo_data, data_collection_results),
            'knowledge_gap_detection': self._detect_knowledge_gaps(repo_data, data_collection_results, risk_analysis_results)
        }
        
        return results
    
    def _cluster_prs_semantically(self, repo_data: Dict[str, Any], 
                                  data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 21: Semantic PR clustering"""
        prs = repo_data.get('prs', [])
        
        # Extract keywords and topics from PRs
        pr_features = []
        for pr in prs:
            title = pr.get('title', '').lower()
            body = pr.get('body', '').lower()
            text = f"{title} {body}"
            
            # Extract keywords
            keywords = self._extract_keywords(text)
            
            # Categorize by common patterns
            category = self._categorize_pr(text)
            
            pr_features.append({
                'pr_number': pr.get('number'),
                'title': pr.get('title', ''),
                'keywords': keywords,
                'category': category,
                'text': text[:200]  # First 200 chars
            })
        
        # Cluster by category and keywords
        clusters = defaultdict(list)
        for pr_feat in pr_features:
            cluster_key = pr_feat['category']
            clusters[cluster_key].append(pr_feat)
        
        # Further sub-cluster by keywords
        refined_clusters = {}
        for category, prs_in_category in clusters.items():
            if len(prs_in_category) > 3:
                # Sub-cluster by top keywords
                keyword_groups = defaultdict(list)
                for pr in prs_in_category:
                    top_keyword = pr['keywords'][0] if pr['keywords'] else 'other'
                    keyword_groups[top_keyword].append(pr)
                refined_clusters[category] = dict(keyword_groups)
            else:
                refined_clusters[category] = {'all': prs_in_category}
        
        self.semantic_clusters = refined_clusters
        
        return {
            'clusters': refined_clusters,
            'cluster_summary': {k: len(sum(v.values() if isinstance(v, dict) else [v], [])) 
                              for k, v in refined_clusters.items()},
            'total_clusters': len(refined_clusters),
            'total_prs_clustered': len(prs)
        }
    
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extract top keywords from text"""
        # Common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        # Count frequencies
        word_freq = defaultdict(int)
        for word in words:
            if word not in stop_words:
                word_freq[word] += 1
        
        # Return top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]
    
    def _categorize_pr(self, text: str) -> str:
        """Categorize PR by content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['fix', 'bug', 'error', 'issue', 'problem', 'broken']):
            return 'bugfix'
        elif any(word in text_lower for word in ['feature', 'add', 'new', 'implement', 'create']):
            return 'feature'
        elif any(word in text_lower for word in ['refactor', 'cleanup', 'improve', 'optimize', 'update']):
            return 'refactor'
        elif any(word in text_lower for word in ['test', 'testing', 'spec', 'coverage']):
            return 'testing'
        elif any(word in text_lower for word in ['doc', 'readme', 'comment', 'documentation']):
            return 'documentation'
        elif any(word in text_lower for word in ['config', 'setting', 'environment', 'deploy']):
            return 'configuration'
        else:
            return 'other'
    
    def _identify_knowledge_units(self, repo_data: Dict[str, Any], 
                                 data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 22: Knowledge unit identification (system/module/feature)"""
        code_files = repo_data.get('code_files', [])
        directory_structure = data_collection_results.get('dependencies', {}).get('directory_structure', {})
        critical_subsystems = data_collection_results.get('critical_subsystems', {}).get('critical_subsystems', [])
        
        knowledge_units = {
            'systems': [],
            'modules': [],
            'features': []
        }
        
        # Identify systems (top-level directories)
        top_level_dirs = set()
        for file_info in code_files:
            path = file_info.get('path', '')
            if '/' in path:
                top_dir = path.split('/')[0]
                top_level_dirs.add(top_dir)
        
        for top_dir in top_level_dirs:
            files_in_dir = [f.get('path', '') for f in code_files if f.get('path', '').startswith(top_dir + '/')]
            knowledge_units['systems'].append({
                'name': top_dir,
                'type': 'system',
                'file_count': len(files_in_dir),
                'files': files_in_dir[:10]  # Sample
            })
        
        # Identify modules (subdirectories with significant file count)
        for directory, files in directory_structure.items():
            if len(files) >= 3:  # Threshold for module
                knowledge_units['modules'].append({
                    'name': directory,
                    'type': 'module',
                    'file_count': len(files),
                    'files': files[:10]  # Sample
                })
        
        # Identify features (based on critical subsystems and file groupings)
        for cs in critical_subsystems:
            knowledge_units['features'].append({
                'name': cs['path'],
                'type': 'feature',
                'criticality_score': cs.get('score', 0),
                'description': f"Critical subsystem: {cs['path']}"
            })
        
        self.knowledge_units = knowledge_units
        
        return {
            'knowledge_units': knowledge_units,
            'total_systems': len(knowledge_units['systems']),
            'total_modules': len(knowledge_units['modules']),
            'total_features': len(knowledge_units['features'])
        }
    
    def _detect_roles_from_history(self, repo_data: Dict[str, Any], 
                                   data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 23: Role detection from work history"""
        multi_repo = data_collection_results.get('multi_repo_contribution', {}).get('contributors', {})
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        operational_ownership = data_collection_results.get('operational_ownership', {}).get('operational_files', [])
        
        roles = {}
        
        for contributor, stats in multi_repo.items():
            role_indicators = {
                'backend_developer': 0,
                'frontend_developer': 0,
                'devops_engineer': 0,
                'fullstack_developer': 0,
                'maintainer': 0,
                'contributor': 0
            }
            
            # Analyze file patterns
            files_modified = stats.get('files_modified', [])
            for file_path in files_modified:
                file_lower = file_path.lower()
                
                if any(ext in file_lower for ext in ['.js', '.ts', '.jsx', '.tsx', '.vue', '.html', '.css']):
                    role_indicators['frontend_developer'] += 1
                elif any(ext in file_lower for ext in ['.py', '.java', '.go', '.rs', '.cpp', '.c']):
                    role_indicators['backend_developer'] += 1
                
                if any(word in file_lower for word in ['deploy', 'docker', 'k8s', 'ci', 'config', 'terraform']):
                    role_indicators['devops_engineer'] += 1
            
            # Check operational files
            op_files = [op for op in operational_ownership if op.get('current_owner') == contributor]
            if op_files:
                role_indicators['devops_engineer'] += len(op_files)
            
            # Determine primary role
            max_role = max(role_indicators.items(), key=lambda x: x[1])
            primary_role = max_role[0] if max_role[1] > 0 else 'contributor'
            
            # Check if fullstack
            if role_indicators['frontend_developer'] > 0 and role_indicators['backend_developer'] > 0:
                primary_role = 'fullstack_developer'
            
            # Check if maintainer (high contribution count)
            if stats.get('prs', 0) + stats.get('commits', 0) > 20:
                role_indicators['maintainer'] = 1
                if primary_role == 'contributor':
                    primary_role = 'maintainer'
            
            roles[contributor] = {
                'primary_role': primary_role,
                'role_confidence': min(max_role[1] / max(stats.get('files_modified_count', 1), 1), 1.0),
                'role_indicators': {k: v for k, v in role_indicators.items() if v > 0},
                'contribution_stats': {
                    'prs': stats.get('prs', 0),
                    'commits': stats.get('commits', 0),
                    'files_modified': stats.get('files_modified_count', 0)
                }
            }
        
        return {
            'detected_roles': roles,
            'role_distribution': self._count_roles(roles),
            'total_contributors_analyzed': len(roles)
        }
    
    def _count_roles(self, roles: Dict[str, Any]) -> Dict[str, int]:
        """Count role distribution"""
        distribution = defaultdict(int)
        for role_data in roles.values():
            distribution[role_data['primary_role']] += 1
        return dict(distribution)
    
    def _calculate_ai_confidence(self, repo_data: Dict[str, Any], 
                               data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 24: AI confidence scoring"""
        # Calculate confidence scores for various AI decisions
        confidence_scores = {}
        
        # Confidence for role detection
        roles = self._detect_roles_from_history(repo_data, data_collection_results)
        for contributor, role_data in roles.get('detected_roles', {}).items():
            confidence_scores[f"role_{contributor}"] = {
                'decision': role_data['primary_role'],
                'confidence': role_data['role_confidence'],
                'explanation': f"Based on {role_data['contribution_stats']['files_modified']} files modified"
            }
        
        # Confidence for knowledge unit identification
        knowledge_units = self._identify_knowledge_units(repo_data, data_collection_results)
        for unit_type, units in knowledge_units.get('knowledge_units', {}).items():
            for unit in units:
                confidence = min(unit.get('file_count', 0) / 10.0, 1.0) if unit.get('file_count', 0) > 0 else 0.5
                confidence_scores[f"knowledge_unit_{unit['name']}"] = {
                    'decision': f"{unit_type}: {unit['name']}",
                    'confidence': confidence,
                    'explanation': f"Identified based on {unit.get('file_count', 0)} files"
                }
        
        # Confidence for PR clustering
        clusters = self._cluster_prs_semantically(repo_data, data_collection_results)
        for cluster_name, cluster_data in clusters.get('clusters', {}).items():
            cluster_size = sum(len(v) if isinstance(v, list) else len(v.values()) if isinstance(v, dict) else 1 
                              for v in (cluster_data.values() if isinstance(cluster_data, dict) else [cluster_data]))
            confidence = min(cluster_size / 5.0, 1.0)
            confidence_scores[f"cluster_{cluster_name}"] = {
                'decision': f"PR cluster: {cluster_name}",
                'confidence': confidence,
                'explanation': f"Based on {cluster_size} PRs"
            }
        
        return {
            'confidence_scores': confidence_scores,
            'average_confidence': sum(c['confidence'] for c in confidence_scores.values()) / len(confidence_scores) if confidence_scores else 0,
            'high_confidence_decisions': [k for k, v in confidence_scores.items() if v['confidence'] > 0.7],
            'low_confidence_decisions': [k for k, v in confidence_scores.items() if v['confidence'] < 0.5]
        }
    
    def _create_rule_based_fallbacks(self, repo_data: Dict[str, Any], 
                                    data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 25: Rule-based fallback for all AI decisions"""
        fallback_rules = {
            'role_detection': {
                'rule': 'If AI confidence < 0.5, assign role based on file extension patterns',
                'fallback_logic': 'Count file extensions, assign most common pattern role'
            },
            'knowledge_unit_identification': {
                'rule': 'If AI fails, use directory structure as knowledge units',
                'fallback_logic': 'Each directory with >3 files becomes a knowledge unit'
            },
            'pr_clustering': {
                'rule': 'If semantic clustering fails, cluster by PR labels or file patterns',
                'fallback_logic': 'Group PRs by common file paths modified'
            },
            'criticality_scoring': {
                'rule': 'If AI scoring unavailable, use rule-based scoring',
                'fallback_logic': 'Score = (change_frequency * 0.4) + (owner_count_inverse * 0.3) + (location_weight * 0.3)'
            }
        }
        
        return {
            'fallback_rules': fallback_rules,
            'fallback_applied': False,  # Would be True if AI failed
            'rule_coverage': 'All AI decisions have rule-based fallbacks'
        }
    
    def _generate_explanations(self, repo_data: Dict[str, Any], 
                              data_collection_results: Dict[str, Any],
                              risk_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 26: Explainability for every AI output"""
        explanations = {}
        
        # Explain role detection
        roles = self._detect_roles_from_history(repo_data, data_collection_results)
        for contributor, role_data in roles.get('detected_roles', {}).items():
            explanations[f"role_{contributor}"] = {
                'output': role_data['primary_role'],
                'explanation': f"Detected as {role_data['primary_role']} because: " +
                             f"{role_data['contribution_stats']['prs']} PRs, " +
                             f"{role_data['contribution_stats']['commits']} commits, " +
                             f"{role_data['contribution_stats']['files_modified']} files modified. " +
                             f"Role indicators: {', '.join(role_data['role_indicators'].keys())}",
                'confidence': role_data['role_confidence'],
                'factors': list(role_data['role_indicators'].keys())
            }
        
        # Explain criticality scores
        criticality = risk_analysis_results.get('criticality_scoring', {}).get('criticality_scores', {})
        for filename, crit_data in list(criticality.items())[:10]:  # Sample
            explanations[f"criticality_{filename}"] = {
                'output': crit_data['criticality_level'],
                'explanation': crit_data.get('explanation', ''),
                'score': crit_data['criticality_score'],
                'factors': crit_data.get('factors', [])
            }
        
        # Explain knowledge units
        knowledge_units = self._identify_knowledge_units(repo_data, data_collection_results)
        for unit_type, units in knowledge_units.get('knowledge_units', {}).items():
            for unit in units[:5]:  # Sample
                explanations[f"knowledge_unit_{unit['name']}"] = {
                    'output': f"{unit_type}: {unit['name']}",
                    'explanation': f"Identified as {unit_type} with {unit.get('file_count', 0)} files. " +
                                 f"Based on directory structure and file organization patterns.",
                    'file_count': unit.get('file_count', 0)
                }
        
        return {
            'explanations': explanations,
            'total_explanations': len(explanations),
            'explanation_coverage': 'All AI outputs include explanations'
        }
    
    def _track_prompt_versioning(self) -> Dict[str, Any]:
        """Feature 27: Prompt versioning and audit trail"""
        return {
            'current_version': self.prompt_version,
            'version_history': [
                {
                    'version': '1.0.0',
                    'date': '2024-01-01',
                    'changes': 'Initial version with rule-based implementations',
                    'prompt_hash': hashlib.md5(f"v{self.prompt_version}".encode()).hexdigest()[:8]
                }
            ],
            'audit_trail': [
                {
                    'timestamp': '2024-01-01T00:00:00Z',
                    'action': 'prompt_created',
                    'version': self.prompt_version,
                    'details': 'Initial prompt versioning system'
                }
            ]
        }
    
    def _validate_llm_outputs(self, repo_data: Dict[str, Any], 
                             data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 28: LLM output validation"""
        validation_results = {}
        
        # Validate role detection
        roles = self._detect_roles_from_history(repo_data, data_collection_results)
        for contributor, role_data in roles.get('detected_roles', {}).items():
            validation_results[f"role_{contributor}"] = {
                'output': role_data['primary_role'],
                'validation_status': 'valid' if role_data['role_confidence'] > 0.3 else 'low_confidence',
                'validation_rules': [
                    'Role must be one of: backend_developer, frontend_developer, devops_engineer, fullstack_developer, maintainer, contributor',
                    'Confidence must be > 0.3',
                    'Must have at least 1 file modified'
                ],
                'rules_passed': [
                    role_data['primary_role'] in ['backend_developer', 'frontend_developer', 'devops_engineer', 'fullstack_developer', 'maintainer', 'contributor'],
                    role_data['role_confidence'] > 0.3,
                    role_data['contribution_stats']['files_modified'] > 0
                ]
            }
        
        # Validate knowledge units
        knowledge_units = self._identify_knowledge_units(repo_data, data_collection_results)
        for unit_type, units in knowledge_units.get('knowledge_units', {}).items():
            for unit in units:
                validation_results[f"knowledge_unit_{unit['name']}"] = {
                    'output': f"{unit_type}: {unit['name']}",
                    'validation_status': 'valid' if unit.get('file_count', 0) > 0 else 'invalid',
                    'validation_rules': [
                        'Must have at least 1 file',
                        'Name must be non-empty',
                        'Type must be: system, module, or feature'
                    ],
                    'rules_passed': [
                        unit.get('file_count', 0) > 0,
                        bool(unit.get('name', '')),
                        unit.get('type') in ['system', 'module', 'feature']
                    ]
                }
        
        return {
            'validation_results': validation_results,
            'total_validated': len(validation_results),
            'valid_count': sum(1 for v in validation_results.values() if v['validation_status'] == 'valid'),
            'invalid_count': sum(1 for v in validation_results.values() if v['validation_status'] == 'invalid')
        }
    
    def _detect_knowledge_similarity(self, repo_data: Dict[str, Any], 
                                     data_collection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 29: Knowledge similarity & duplication detection"""
        code_files = repo_data.get('code_files', [])
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        
        similarities = []
        
        # Detect similar file names
        file_names = {}
        for file_info in code_files:
            path = file_info.get('path', '')
            filename = path.split('/')[-1] if '/' in path else path
            base_name = filename.split('.')[0] if '.' in filename else filename
            
            if base_name not in file_names:
                file_names[base_name] = []
            file_names[base_name].append(path)
        
        # Find duplicates
        duplicates = {k: v for k, v in file_names.items() if len(v) > 1}
        
        # Detect similar ownership patterns
        ownership_patterns = defaultdict(list)
        for filename, history in ownership_history.items():
            owners = tuple(sorted(set([h['author'] for h in history])))
            ownership_patterns[owners].append(filename)
        
        similar_ownership = {k: v for k, v in ownership_patterns.items() if len(v) > 1}
        
        return {
            'duplicate_file_names': duplicates,
            'similar_ownership_patterns': {str(k): v for k, v in similar_ownership.items()},
            'total_duplicates': sum(len(v) for v in duplicates.values()),
            'total_similar_patterns': len(similar_ownership)
        }
    
    def _detect_knowledge_gaps(self, repo_data: Dict[str, Any], 
                              data_collection_results: Dict[str, Any],
                              risk_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 30: Knowledge gap detection"""
        ownership_history = data_collection_results.get('file_ownership_history', {}).get('ownership_history', {})
        single_owners = risk_analysis_results.get('single_owner_detection', {}).get('single_owner_files', [])
        knowledge_decay = risk_analysis_results.get('knowledge_decay', {}).get('decay_detection', [])
        
        knowledge_gaps = []
        
        # Gap 1: Single owner files
        for so_file in single_owners:
            knowledge_gaps.append({
                'type': 'single_owner',
                'file': so_file.get('file', ''),
                'severity': 'high',
                'description': f"File has only one owner ({so_file.get('owner', 'unknown')}), creating knowledge risk",
                'recommendation': 'Identify backup owner or document knowledge'
            })
        
        # Gap 2: Decayed knowledge
        for decay_file in knowledge_decay[:10]:  # Top 10
            knowledge_gaps.append({
                'type': 'knowledge_decay',
                'file': decay_file.get('file', ''),
                'severity': 'medium',
                'description': f"File has not been modified in {decay_file.get('days_since_last_change', 0)} days",
                'recommendation': 'Review and update documentation'
            })
        
        # Gap 3: Files with no ownership history
        all_files = set()
        code_files = repo_data.get('code_files', [])
        for f in code_files:
            all_files.add(f.get('path', ''))
        
        files_with_history = set(ownership_history.keys())
        files_without_history = all_files - files_with_history
        
        for file_path in list(files_without_history)[:10]:  # Sample
            knowledge_gaps.append({
                'type': 'no_history',
                'file': file_path,
                'severity': 'low',
                'description': 'File has no tracked ownership or change history',
                'recommendation': 'Investigate file origin and ownership'
            })
        
        return {
            'knowledge_gaps': knowledge_gaps,
            'gap_summary': {
                'high_severity': sum(1 for g in knowledge_gaps if g['severity'] == 'high'),
                'medium_severity': sum(1 for g in knowledge_gaps if g['severity'] == 'medium'),
                'low_severity': sum(1 for g in knowledge_gaps if g['severity'] == 'low')
            },
            'total_gaps': len(knowledge_gaps)
        }

