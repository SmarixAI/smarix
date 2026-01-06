"""
Documentation Detection Module
Implements features 74-78: Gap detection, type detection, priority calculation, etc.
"""

from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
from datetime import datetime
import re
from pathlib import Path


class DocumentationDetector:
    """
    Detects documentation gaps and requirements (Features 74-78)
    """
    
    def __init__(self):
        self.documentation_gaps = []
        self.existing_docs = []
        self.duplicate_docs = []
    
    def process(self, prerequisite_data: Dict[str, Any], 
                final_call_data: Optional[Dict[str, Any]] = None,
                handover_data: Optional[Dict[str, Any]] = None,
                employee_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all documentation detection features
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            final_call_data: Final Call results (optional)
            handover_data: Handover results (optional)
            employee_username: Departing employee username
            
        Returns:
            Dictionary with all documentation detection results
        """
        results = {
            'documentation_gaps': self._detect_documentation_gaps(prerequisite_data, final_call_data, handover_data, employee_username),
            'required_documentation_types': self._detect_required_types(prerequisite_data, final_call_data, handover_data, employee_username),
            'documentation_priority': self._calculate_documentation_priority(prerequisite_data, final_call_data, handover_data, employee_username),
            'existing_documentation': self._discover_existing_documentation(prerequisite_data),
            'duplicate_documentation': self._detect_duplicate_documentation(prerequisite_data)
        }
        
        return results
    
    def _detect_documentation_gaps(self, prerequisite_data: Dict[str, Any], 
                                   final_call_data: Optional[Dict[str, Any]],
                                   handover_data: Optional[Dict[str, Any]],
                                   employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 74: Documentation gap detection"""
        data_collection = prerequisite_data.get('data_collection', {})
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        
        code_files = data_collection.get('code_files', [])
        documentation = data_collection.get('documentation', [])
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        
        # Get documented files
        documented_files = {doc.get('path', '') for doc in documentation}
        
        gaps = []
        
        # Gap 1: High-risk files without documentation
        knowledge_loss_risk = risk_analysis.get('knowledge_loss_risk', {})
        file_risk_scores = knowledge_loss_risk.get('file_risk_scores', {})
        
        for filename, risk_data in file_risk_scores.items():
            if risk_data.get('risk_level') in ['critical', 'high']:
                # Check if file is documented
                file_documented = any(
                    doc_path == filename or 
                    filename in doc_path or 
                    doc_path.replace('.md', '') == filename.replace('.py', '').replace('.js', '')
                    for doc_path in documented_files
                )
                
                if not file_documented:
                    gaps.append({
                        'gap_type': 'high_risk_no_documentation',
                        'file': filename,
                        'risk_level': risk_data.get('risk_level'),
                        'risk_score': risk_data.get('risk_score', 0),
                        'severity': 'critical',
                        'description': f"High-risk file {filename} lacks documentation",
                        'recommended_doc_type': 'comprehensive'
                    })
        
        # Gap 2: Single-owner files without documentation
        single_owners = risk_analysis.get('single_owner_detection', {}).get('single_owner_files', [])
        for so_file in single_owners:
            file_path = so_file.get('file', '')
            if employee_username and so_file.get('owner') != employee_username:
                continue
            
            file_documented = any(
                doc_path == file_path or file_path in doc_path
                for doc_path in documented_files
            )
            
            if not file_documented:
                gaps.append({
                    'gap_type': 'single_owner_no_documentation',
                    'file': file_path,
                    'owner': so_file.get('owner', ''),
                    'severity': 'high',
                    'description': f"Single-owner file {file_path} lacks documentation",
                    'recommended_doc_type': 'detailed'
                })
        
        # Gap 3: Critical subsystems without documentation
        critical_subsystems = data_collection.get('critical_subsystems', {}).get('critical_subsystems', [])
        for subsystem in critical_subsystems:
            subsystem_path = subsystem.get('path', '')
            
            # Check if subsystem has documentation
            subsystem_documented = any(
                'readme' in doc.get('path', '').lower() or
                'docs' in doc.get('path', '').lower() or
                subsystem_path in doc.get('path', '')
                for doc in documentation
            )
            
            if not subsystem_documented:
                gaps.append({
                    'gap_type': 'critical_subsystem_no_documentation',
                    'subsystem': subsystem_path,
                    'severity': 'high',
                    'description': f"Critical subsystem {subsystem_path} lacks documentation",
                    'recommended_doc_type': 'architecture'
                })
        
        # Gap 4: Operational files without runbooks
        operational = risk_analysis.get('operational_ownership', {}).get('operational_files', [])
        for op_file in operational:
            if employee_username and op_file.get('current_owner') != employee_username:
                continue
            
            file_path = op_file.get('file', '')
            file_type = op_file.get('type', '')
            
            # Check for runbook
            has_runbook = any(
                'runbook' in doc.get('path', '').lower() or
                'operational' in doc.get('path', '').lower() or
                file_path in doc.get('path', '')
                for doc in documentation
            )
            
            if not has_runbook and file_type in ['deployment', 'ci_cd', 'monitoring']:
                gaps.append({
                    'gap_type': 'operational_no_runbook',
                    'file': file_path,
                    'file_type': file_type,
                    'severity': 'critical',
                    'description': f"Operational {file_type} file {file_path} lacks runbook",
                    'recommended_doc_type': 'runbook'
                })
        
        # Gap 5: Knowledge units from Final Call without documentation
        if final_call_data:
            final_call_topics = final_call_data.get('topic_identification', {}).get('final_call_topics', {}).get('topics', [])
            for topic in final_call_topics:
                if topic.get('priority') in ['critical', 'high']:
                    related_files = topic.get('related_files', [])
                    for file_path in related_files:
                        file_documented = any(
                            doc_path == file_path or file_path in doc_path
                            for doc_path in documented_files
                        )
                        
                        if not file_documented:
                            gaps.append({
                                'gap_type': 'final_call_topic_no_documentation',
                                'file': file_path,
                                'topic': topic.get('title', ''),
                                'severity': 'high',
                                'description': f"Final Call topic file {file_path} lacks documentation",
                                'recommended_doc_type': 'knowledge_transfer'
                            })
        
        # Remove duplicates
        unique_gaps = {}
        for gap in gaps:
            key = (gap.get('file', ''), gap.get('gap_type', ''))
            if key not in unique_gaps or gap.get('severity') == 'critical':
                unique_gaps[key] = gap
        
        gaps = list(unique_gaps.values())
        self.documentation_gaps = gaps
        
        # Group by severity
        gaps_by_severity = defaultdict(list)
        for gap in gaps:
            gaps_by_severity[gap.get('severity', 'medium')].append(gap)
        
        return {
            'documentation_gaps': gaps,
            'total_gaps': len(gaps),
            'gaps_by_severity': dict(gaps_by_severity),
            'critical_gaps': gaps_by_severity.get('critical', []),
            'high_severity_gaps': gaps_by_severity.get('high', []),
            'gaps_by_type': self._group_gaps_by_type(gaps)
        }
    
    def _group_gaps_by_type(self, gaps: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group gaps by type"""
        by_type = defaultdict(list)
        for gap in gaps:
            by_type[gap.get('gap_type', 'unknown')].append(gap)
        return dict(by_type)
    
    def _detect_required_types(self, prerequisite_data: Dict[str, Any], 
                              final_call_data: Optional[Dict[str, Any]],
                              handover_data: Optional[Dict[str, Any]],
                              employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 75: Required documentation type detection"""
        gaps = self._detect_documentation_gaps(prerequisite_data, final_call_data, handover_data, employee_username)
        documentation_gaps = gaps.get('documentation_gaps', [])
        
        required_types = defaultdict(list)
        
        for gap in documentation_gaps:
            doc_type = gap.get('recommended_doc_type', 'general')
            required_types[doc_type].append(gap)
        
        # Define documentation types
        doc_type_definitions = {
            'comprehensive': {
                'description': 'Comprehensive documentation covering all aspects',
                'sections': ['overview', 'architecture', 'usage', 'api', 'examples', 'troubleshooting'],
                'format': 'markdown',
                'estimated_hours': 4
            },
            'detailed': {
                'description': 'Detailed documentation with examples',
                'sections': ['overview', 'usage', 'examples', 'troubleshooting'],
                'format': 'markdown',
                'estimated_hours': 2
            },
            'architecture': {
                'description': 'Architecture and design documentation',
                'sections': ['overview', 'architecture', 'design_decisions', 'dependencies'],
                'format': 'markdown',
                'estimated_hours': 3
            },
            'runbook': {
                'description': 'Operational runbook',
                'sections': ['overview', 'deployment', 'monitoring', 'troubleshooting', 'escalation'],
                'format': 'markdown',
                'estimated_hours': 2
            },
            'knowledge_transfer': {
                'description': 'Knowledge transfer documentation',
                'sections': ['overview', 'key_concepts', 'common_issues', 'gotchas'],
                'format': 'markdown',
                'estimated_hours': 2
            },
            'api': {
                'description': 'API documentation',
                'sections': ['overview', 'endpoints', 'authentication', 'examples'],
                'format': 'markdown_or_openapi',
                'estimated_hours': 3
            },
            'general': {
                'description': 'General documentation',
                'sections': ['overview', 'usage'],
                'format': 'markdown',
                'estimated_hours': 1
            }
        }
        
        return {
            'required_types': dict(required_types),
            'type_definitions': doc_type_definitions,
            'total_required_docs': len(documentation_gaps),
            'types_summary': {
                doc_type: len(gaps) 
                for doc_type, gaps in required_types.items()
            }
        }
    
    def _calculate_documentation_priority(self, prerequisite_data: Dict[str, Any], 
                                         final_call_data: Optional[Dict[str, Any]],
                                         handover_data: Optional[Dict[str, Any]],
                                         employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 76: Documentation priority calculation"""
        gaps = self._detect_documentation_gaps(prerequisite_data, final_call_data, handover_data, employee_username)
        documentation_gaps = gaps.get('documentation_gaps', [])
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        ownership_risks = risk_analysis.get('ownership_risk_scoring', {}).get('ownership_risks', {})
        
        prioritized_docs = []
        
        for gap in documentation_gaps:
            file_path = gap.get('file', '')
            severity = gap.get('severity', 'medium')
            risk_score = gap.get('risk_score', 0)
            
            # Calculate priority score
            priority_score = 0.0
            
            # Severity weight
            severity_weights = {'critical': 0.4, 'high': 0.3, 'medium': 0.2, 'low': 0.1}
            priority_score += severity_weights.get(severity, 0.2)
            
            # Risk score weight
            priority_score += risk_score * 0.3
            
            # Ownership risk weight
            ownership_risk = ownership_risks.get(file_path, {})
            ownership_risk_score = ownership_risk.get('ownership_risk_score', 0)
            priority_score += ownership_risk_score * 0.2
            
            # Gap type weight
            gap_type = gap.get('gap_type', '')
            if 'operational' in gap_type or 'critical' in gap_type:
                priority_score += 0.1
            
            priority_score = min(priority_score, 1.0)
            
            # Determine priority level
            if priority_score >= 0.7:
                priority_level = 'critical'
            elif priority_score >= 0.5:
                priority_level = 'high'
            elif priority_score >= 0.3:
                priority_level = 'medium'
            else:
                priority_level = 'low'
            
            prioritized_docs.append({
                'file': file_path,
                'gap_type': gap_type,
                'priority_score': round(priority_score, 3),
                'priority_level': priority_level,
                'severity': severity,
                'recommended_doc_type': gap.get('recommended_doc_type', 'general'),
                'factors': {
                    'severity': severity,
                    'risk_score': risk_score,
                    'ownership_risk': ownership_risk_score,
                    'gap_type': gap_type
                },
                'estimated_hours': self._estimate_doc_hours(gap.get('recommended_doc_type', 'general'))
            })
        
        # Sort by priority
        prioritized_docs.sort(key=lambda x: (x.get('priority_score', 0), x.get('severity', 'medium')), reverse=True)
        
        return {
            'prioritized_documentation': prioritized_docs,
            'total_items': len(prioritized_docs),
            'critical_priority': [d for d in prioritized_docs if d.get('priority_level') == 'critical'],
            'high_priority': [d for d in prioritized_docs if d.get('priority_level') == 'high'],
            'priority_summary': {
                'critical': sum(1 for d in prioritized_docs if d.get('priority_level') == 'critical'),
                'high': sum(1 for d in prioritized_docs if d.get('priority_level') == 'high'),
                'medium': sum(1 for d in prioritized_docs if d.get('priority_level') == 'medium'),
                'low': sum(1 for d in prioritized_docs if d.get('priority_level') == 'low')
            }
        }
    
    def _estimate_doc_hours(self, doc_type: str) -> float:
        """Estimate hours needed for documentation type"""
        estimates = {
            'comprehensive': 4.0,
            'detailed': 2.0,
            'architecture': 3.0,
            'runbook': 2.0,
            'knowledge_transfer': 2.0,
            'api': 3.0,
            'general': 1.0
        }
        return estimates.get(doc_type, 1.0)
    
    def _discover_existing_documentation(self, prerequisite_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 77: Existing documentation discovery"""
        data_collection = prerequisite_data.get('data_collection', {})
        documentation = data_collection.get('documentation', [])
        code_files = data_collection.get('code_files', [])
        
        existing_docs = []
        
        for doc in documentation:
            doc_path = doc.get('path', '')
            doc_name = doc.get('name', '')
            doc_size = doc.get('size', 0)
            
            # Classify documentation type
            doc_type = self._classify_documentation_type(doc_path, doc_name)
            
            # Find related code files
            related_files = []
            for code_file in code_files:
                code_path = code_file.get('path', '')
                # Simple matching - in real system would be more sophisticated
                if doc_path.lower().replace('.md', '') in code_path.lower() or \
                   code_path.split('/')[-1].replace('.py', '').replace('.js', '') in doc_name.lower():
                    related_files.append(code_path)
            
            existing_docs.append({
                'path': doc_path,
                'name': doc_name,
                'type': doc_type,
                'size': doc_size,
                'related_files': related_files[:5],  # Top 5
                'last_modified': doc.get('sha', ''),  # Would use actual date in real system
                'freshness': 'unknown'  # Would calculate based on dates
            })
        
        self.existing_docs = existing_docs
        
        # Group by type
        docs_by_type = defaultdict(list)
        for doc in existing_docs:
            docs_by_type[doc.get('type', 'unknown')].append(doc)
        
        return {
            'existing_documentation': existing_docs,
            'total_docs': len(existing_docs),
            'docs_by_type': dict(docs_by_type),
            'documentation_coverage': self._calculate_coverage(existing_docs, code_files)
        }
    
    def _classify_documentation_type(self, path: str, name: str) -> str:
        """Classify documentation type"""
        path_lower = path.lower()
        name_lower = name.lower()
        
        if 'readme' in path_lower or 'readme' in name_lower:
            return 'readme'
        elif 'api' in path_lower or 'api' in name_lower:
            return 'api'
        elif 'runbook' in path_lower or 'runbook' in name_lower:
            return 'runbook'
        elif 'architecture' in path_lower or 'arch' in path_lower:
            return 'architecture'
        elif 'guide' in path_lower or 'tutorial' in path_lower:
            return 'guide'
        elif 'changelog' in path_lower or 'changelog' in name_lower:
            return 'changelog'
        elif 'license' in path_lower or 'license' in name_lower:
            return 'license'
        elif 'contributing' in path_lower:
            return 'contributing'
        else:
            return 'general'
    
    def _calculate_coverage(self, existing_docs: List[Dict[str, Any]], 
                           code_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate documentation coverage"""
        total_code_files = len(code_files)
        documented_files = set()
        
        for doc in existing_docs:
            documented_files.update(doc.get('related_files', []))
        
        coverage_percentage = (len(documented_files) / total_code_files * 100) if total_code_files > 0 else 0
        
        return {
            'total_code_files': total_code_files,
            'documented_files': len(documented_files),
            'coverage_percentage': round(coverage_percentage, 2),
            'undocumented_files': total_code_files - len(documented_files)
        }
    
    def _detect_duplicate_documentation(self, prerequisite_data: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 78: Duplicate documentation detection"""
        existing_docs = self._discover_existing_documentation(prerequisite_data)
        docs = existing_docs.get('existing_documentation', [])
        
        duplicates = []
        
        # Group by name similarity
        name_groups = defaultdict(list)
        for doc in docs:
            name_key = doc.get('name', '').lower().replace('.md', '').replace('.txt', '')
            name_groups[name_key].append(doc)
        
        # Find duplicates
        for name_key, doc_group in name_groups.items():
            if len(doc_group) > 1:
                duplicates.append({
                    'duplicate_key': name_key,
                    'duplicate_count': len(doc_group),
                    'documents': doc_group,
                    'recommendation': 'Consolidate into single documentation file'
                })
        
        # Also check for similar content (by size)
        size_groups = defaultdict(list)
        for doc in docs:
            size_key = f"{doc.get('size', 0) // 1000}kb"  # Group by size ranges
            size_groups[size_key].append(doc)
        
        potential_duplicates = []
        for size_key, doc_group in size_groups.items():
            if len(doc_group) > 2:  # Multiple docs of similar size
                # Check if they're in same directory
                paths = [d.get('path', '') for d in doc_group]
                if len(set('/'.join(p.split('/')[:-1]) for p in paths if '/' in p)) == 1:
                    potential_duplicates.append({
                        'size_group': size_key,
                        'documents': doc_group,
                        'recommendation': 'Review for content duplication'
                    })
        
        self.duplicate_docs = duplicates + potential_duplicates
        
        return {
            'duplicate_documentation': duplicates,
            'potential_duplicates': potential_duplicates,
            'total_duplicates': len(duplicates),
            'duplicate_summary': {
                'exact_name_duplicates': len(duplicates),
                'potential_content_duplicates': len(potential_duplicates)
            }
        }

