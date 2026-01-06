"""
Final Call Topic Identification Module
Implements features 31-38: Automatic topic detection, risk prioritization, knowledge units, etc.
"""

from typing import Dict, Any, List, Set, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import re


class FinalCallTopicIdentifier:
    """
    Identifies and prioritizes topics for Final Call discussions (Features 31-38)
    """
    
    def __init__(self):
        self.topics = []
        self.implicit_knowledge = []
        self.architecture_decisions = []
        self.failure_scenarios = []
    
    def process(self, prerequisite_data: Dict[str, Any], 
                employee_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all topic identification features
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            employee_username: Username of departing employee (optional)
            
        Returns:
            Dictionary with all topic identification results
        """
        results = {
            'final_call_topics': self._detect_final_call_topics(prerequisite_data, employee_username),
            'high_risk_prioritization': self._prioritize_high_risk_knowledge(prerequisite_data, employee_username),
            'knowledge_units_requiring_explanation': self._identify_knowledge_units_needing_explanation(prerequisite_data, employee_username),
            'implicit_knowledge': self._identify_implicit_knowledge(prerequisite_data, employee_username),
            'architecture_decisions': self._extract_architecture_decisions(prerequisite_data, employee_username),
            'failure_scenarios': self._identify_failure_scenarios(prerequisite_data, employee_username),
            'business_logic_explanations': self._detect_business_logic_explanations(prerequisite_data, employee_username),
            'operational_flow_explanations': self._detect_operational_flow_explanations(prerequisite_data, employee_username)
        }
        
        return results
    
    def _detect_final_call_topics(self, prerequisite_data: Dict[str, Any], 
                                  employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 31: Automatic Final Call topic detection"""
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        data_collection = prerequisite_data.get('data_collection', {})
        ai_intelligence = prerequisite_data.get('ai_intelligence', {})
        
        topics = []
        
        # Topic 1: High-risk knowledge loss files
        knowledge_loss_risk = risk_analysis.get('knowledge_loss_risk', {})
        high_risk_files = knowledge_loss_risk.get('high_risk_files', [])
        if high_risk_files:
            topics.append({
                'topic_id': 'high_risk_knowledge',
                'title': 'High-Risk Knowledge Transfer',
                'category': 'knowledge_risk',
                'priority': 'critical',
                'description': f"{len(high_risk_files)} files with high knowledge loss risk",
                'related_files': high_risk_files[:10],  # Top 10
                'risk_score': 0.9
            })
        
        # Topic 2: Single-owner files
        single_owners = risk_analysis.get('single_owner_detection', {})
        single_owner_files = single_owners.get('single_owner_files', [])
        if single_owner_files:
            # Filter by employee if specified
            if employee_username:
                employee_files = [f for f in single_owner_files if f.get('owner') == employee_username]
            else:
                employee_files = single_owner_files
            
            if employee_files:
                topics.append({
                    'topic_id': 'single_owner_knowledge',
                    'title': 'Single-Owner Knowledge Transfer',
                    'category': 'ownership_risk',
                    'priority': 'high',
                    'description': f"{len(employee_files)} files with single ownership",
                    'related_files': [f.get('file', '') for f in employee_files[:10]],
                    'risk_score': 0.8
                })
        
        # Topic 3: Critical subsystems
        critical_subsystems = data_collection.get('critical_subsystems', {}).get('critical_subsystems', [])
        if critical_subsystems:
            topics.append({
                'topic_id': 'critical_subsystems',
                'title': 'Critical Subsystem Knowledge',
                'category': 'system_knowledge',
                'priority': 'high',
                'description': f"{len(critical_subsystems)} critical subsystems identified",
                'related_subsystems': [cs.get('path', '') for cs in critical_subsystems],
                'risk_score': 0.85
            })
        
        # Topic 4: Knowledge hotspots
        hotspots = risk_analysis.get('knowledge_hotspots', {}).get('knowledge_hotspots', [])
        if hotspots:
            topics.append({
                'topic_id': 'knowledge_hotspots',
                'title': 'Knowledge Hotspot Areas',
                'category': 'knowledge_concentration',
                'priority': 'medium',
                'description': f"{len(hotspots)} knowledge hotspots identified",
                'related_files': [h.get('file', '') for h in hotspots[:10]],
                'risk_score': 0.7
            })
        
        # Topic 5: Operational ownership
        operational = risk_analysis.get('operational_ownership', {})
        operational_files = operational.get('operational_files', [])
        if employee_username:
            employee_ops = [f for f in operational_files if f.get('current_owner') == employee_username]
        else:
            employee_ops = operational_files
        
        if employee_ops:
            topics.append({
                'topic_id': 'operational_responsibilities',
                'title': 'Operational Responsibilities & Runbooks',
                'category': 'operational',
                'priority': 'critical',
                'description': f"{len(employee_ops)} operational files owned",
                'related_files': [f.get('file', '') for f in employee_ops],
                'risk_score': 0.95
            })
        
        # Topic 6: Hidden dependencies
        hidden_deps = risk_analysis.get('hidden_dependencies', {}).get('hidden_dependencies', [])
        if hidden_deps:
            topics.append({
                'topic_id': 'hidden_dependencies',
                'title': 'Hidden Dependencies & Integration Points',
                'category': 'dependencies',
                'priority': 'high',
                'description': f"{len(hidden_deps)} hidden dependencies identified",
                'related_dependencies': hidden_deps[:10],
                'risk_score': 0.75
            })
        
        # Topic 7: Architecture decisions
        arch_decisions = self._extract_architecture_decisions(prerequisite_data, employee_username)
        if arch_decisions.get('decisions'):
            topics.append({
                'topic_id': 'architecture_decisions',
                'title': 'Architecture & Design Decisions',
                'category': 'architecture',
                'priority': 'high',
                'description': f"{len(arch_decisions.get('decisions', []))} architecture decisions identified",
                'related_decisions': arch_decisions.get('decisions', [])[:10],
                'risk_score': 0.8
            })
        
        # Topic 8: Failure scenarios
        failure_scenarios = self._identify_failure_scenarios(prerequisite_data, employee_username)
        if failure_scenarios.get('scenarios'):
            topics.append({
                'topic_id': 'failure_scenarios',
                'title': 'Known Failure Scenarios & Workarounds',
                'category': 'operational',
                'priority': 'high',
                'description': f"{len(failure_scenarios.get('scenarios', []))} failure scenarios identified",
                'related_scenarios': failure_scenarios.get('scenarios', [])[:10],
                'risk_score': 0.85
            })
        
        # Sort by priority and risk score
        priority_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
        topics.sort(key=lambda x: (priority_order.get(x.get('priority', 'low'), 0), x.get('risk_score', 0)), reverse=True)
        
        self.topics = topics
        
        return {
            'topics': topics,
            'total_topics': len(topics),
            'critical_topics': [t for t in topics if t.get('priority') == 'critical'],
            'high_priority_topics': [t for t in topics if t.get('priority') in ['critical', 'high']]
        }
    
    def _prioritize_high_risk_knowledge(self, prerequisite_data: Dict[str, Any], 
                                       employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 32: High-risk knowledge prioritization"""
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        knowledge_loss_risk = risk_analysis.get('knowledge_loss_risk', {})
        file_risk_scores = knowledge_loss_risk.get('file_risk_scores', {})
        
        # Get high-risk files
        high_risk_files = []
        for filename, risk_data in file_risk_scores.items():
            if risk_data.get('risk_level') == 'high':
                # Filter by employee if specified
                if employee_username and risk_data.get('current_owner') != employee_username:
                    continue
                
                high_risk_files.append({
                    'file': filename,
                    'risk_score': risk_data.get('risk_score', 0),
                    'risk_level': risk_data.get('risk_level'),
                    'owner_count': risk_data.get('owner_count', 0),
                    'current_owner': risk_data.get('current_owner'),
                    'recent_activity': risk_data.get('recent_activity_count', 0),
                    'total_changes': risk_data.get('total_changes', 0)
                })
        
        # Sort by risk score
        high_risk_files.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        
        # Group by risk level
        critical_risk = [f for f in high_risk_files if f.get('risk_score', 0) >= 0.8]
        high_risk = [f for f in high_risk_files if 0.6 <= f.get('risk_score', 0) < 0.8]
        medium_risk = [f for f in high_risk_files if 0.4 <= f.get('risk_score', 0) < 0.6]
        
        return {
            'prioritized_files': high_risk_files,
            'critical_risk_files': critical_risk,
            'high_risk_files': high_risk,
            'medium_risk_files': medium_risk,
            'total_high_risk': len(high_risk_files),
            'priority_order': [f.get('file') for f in high_risk_files]
        }
    
    def _identify_knowledge_units_needing_explanation(self, prerequisite_data: Dict[str, Any], 
                                                      employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 33: Knowledge units requiring explanation"""
        ai_intelligence = prerequisite_data.get('ai_intelligence', {})
        knowledge_units = ai_intelligence.get('knowledge_unit_identification', {}).get('knowledge_units', {})
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        
        units_needing_explanation = []
        
        # Check each knowledge unit
        for unit_type, units in knowledge_units.items():
            for unit in units:
                unit_name = unit.get('name', '')
                file_count = unit.get('file_count', 0)
                
                # Check if unit has high-risk files
                files_in_unit = unit.get('files', [])
                high_risk_count = 0
                
                knowledge_loss_risk = risk_analysis.get('knowledge_loss_risk', {})
                file_risk_scores = knowledge_loss_risk.get('file_risk_scores', {})
                
                for file_path in files_in_unit:
                    risk_data = file_risk_scores.get(file_path, {})
                    if risk_data.get('risk_level') == 'high':
                        high_risk_count += 1
                
                # Determine if explanation needed
                needs_explanation = False
                reasons = []
                
                if high_risk_count > 0:
                    needs_explanation = True
                    reasons.append(f"{high_risk_count} high-risk files")
                
                if file_count > 10:
                    needs_explanation = True
                    reasons.append(f"Large unit ({file_count} files)")
                
                if unit_type == 'critical_subsystems':
                    needs_explanation = True
                    reasons.append("Critical subsystem")
                
                if needs_explanation:
                    units_needing_explanation.append({
                        'unit_name': unit_name,
                        'unit_type': unit_type,
                        'file_count': file_count,
                        'high_risk_files': high_risk_count,
                        'reasons': reasons,
                        'priority': 'high' if high_risk_count > 0 else 'medium'
                    })
        
        return {
            'knowledge_units': units_needing_explanation,
            'total_units_needing_explanation': len(units_needing_explanation),
            'high_priority_units': [u for u in units_needing_explanation if u.get('priority') == 'high']
        }
    
    def _identify_implicit_knowledge(self, prerequisite_data: Dict[str, Any], 
                                     employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 34: Implicit knowledge identification"""
        data_collection = prerequisite_data.get('data_collection', {})
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        
        implicit_knowledge = []
        
        # Pattern 1: Files with high churn but low documentation
        file_churn = data_collection.get('change_frequency', {}).get('file_churn', {})
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        
        for filename, churn_data in file_churn.items():
            change_count = churn_data.get('total_changes', 0)
            if change_count > 10:  # High churn
                history = ownership_history.get(filename, [])
                unique_owners = len(set([h['author'] for h in history]))
                
                # High churn + few owners = implicit knowledge
                if unique_owners <= 2:
                    implicit_knowledge.append({
                        'type': 'high_churn_low_ownership',
                        'file': filename,
                        'change_count': change_count,
                        'owner_count': unique_owners,
                        'description': f"File with {change_count} changes but only {unique_owners} owner(s) - likely contains implicit knowledge",
                        'priority': 'high'
                    })
        
        # Pattern 2: Complex files with single owner
        single_owners = risk_analysis.get('single_owner_detection', {}).get('single_owner_files', [])
        for so_file in single_owners:
            if employee_username and so_file.get('owner') != employee_username:
                continue
            
            change_count = so_file.get('change_count', 0)
            if change_count > 5:
                implicit_knowledge.append({
                    'type': 'single_owner_complex',
                    'file': so_file.get('file', ''),
                    'owner': so_file.get('owner', ''),
                    'change_count': change_count,
                    'description': f"Single-owner file with {change_count} changes - contains implicit knowledge",
                    'priority': 'critical'
                })
        
        # Pattern 3: Operational files with undocumented processes
        operational = risk_analysis.get('operational_ownership', {}).get('operational_files', [])
        for op_file in operational:
            if employee_username and op_file.get('current_owner') != employee_username:
                continue
            
            implicit_knowledge.append({
                'type': 'operational_knowledge',
                'file': op_file.get('file', ''),
                'file_type': op_file.get('type', ''),
                'description': f"Operational {op_file.get('type', 'file')} - may contain undocumented operational knowledge",
                'priority': 'high'
            })
        
        self.implicit_knowledge = implicit_knowledge
        
        return {
            'implicit_knowledge_items': implicit_knowledge,
            'total_implicit_knowledge': len(implicit_knowledge),
            'critical_items': [ik for ik in implicit_knowledge if ik.get('priority') == 'critical'],
            'high_priority_items': [ik for ik in implicit_knowledge if ik.get('priority') in ['critical', 'high']]
        }
    
    def _extract_architecture_decisions(self, prerequisite_data: Dict[str, Any], 
                                       employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 35: Architecture decision extraction"""
        data_collection = prerequisite_data.get('data_collection', {})
        prs = data_collection.get('pr_activity', {}).get('pr_details', [])
        
        architecture_decisions = []
        
        # Look for architecture-related PRs
        arch_keywords = [
            'architecture', 'design', 'refactor', 'restructure', 'migration',
            'refactoring', 'redesign', 'system design', 'architectural',
            'infrastructure', 'platform', 'framework', 'pattern'
        ]
        
        for pr in prs:
            title = pr.get('title', '').lower()
            body = pr.get('body', '').lower() if pr.get('body') else ''
            text = f"{title} {body}"
            
            # Check if PR contains architecture discussion
            has_arch_keywords = any(keyword in text for keyword in arch_keywords)
            
            if has_arch_keywords:
                # Check if it's a significant change
                changed_files = pr.get('changed_files_count', 0)
                if changed_files > 3:  # Significant change
                    architecture_decisions.append({
                        'pr_number': pr.get('number'),
                        'title': pr.get('title', ''),
                        'author': pr.get('author', ''),
                        'created_at': pr.get('created_at'),
                        'changed_files': changed_files,
                        'description': f"Architecture decision in PR #{pr.get('number')}: {pr.get('title', '')}",
                        'type': 'pr_based',
                        'priority': 'high' if changed_files > 10 else 'medium'
                    })
        
        # Extract from critical subsystems
        critical_subsystems = data_collection.get('critical_subsystems', {}).get('critical_subsystems', [])
        for cs in critical_subsystems:
            architecture_decisions.append({
                'subsystem': cs.get('path', ''),
                'score': cs.get('score', 0),
                'description': f"Critical subsystem architecture: {cs.get('path', '')}",
                'type': 'subsystem',
                'priority': 'high'
            })
        
        self.architecture_decisions = architecture_decisions
        
        return {
            'decisions': architecture_decisions,
            'total_decisions': len(architecture_decisions),
            'pr_based_decisions': [d for d in architecture_decisions if d.get('type') == 'pr_based'],
            'subsystem_decisions': [d for d in architecture_decisions if d.get('type') == 'subsystem']
        }
    
    def _identify_failure_scenarios(self, prerequisite_data: Dict[str, Any], 
                                    employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 36: Failure scenario identification"""
        data_collection = prerequisite_data.get('data_collection', {})
        prs = data_collection.get('pr_activity', {}).get('pr_details', [])
        
        failure_scenarios = []
        
        # Look for failure/bug/error-related PRs
        failure_keywords = [
            'fix', 'bug', 'error', 'failure', 'crash', 'exception',
            'timeout', 'deadlock', 'race condition', 'memory leak',
            'workaround', 'hotfix', 'patch', 'issue', 'problem'
        ]
        
        for pr in prs:
            title = pr.get('title', '').lower()
            body = pr.get('body', '').lower() if pr.get('body') else ''
            text = f"{title} {body}"
            
            # Check if PR addresses a failure scenario
            has_failure_keywords = any(keyword in text for keyword in failure_keywords)
            
            if has_failure_keywords:
                # Check for workaround mentions
                has_workaround = 'workaround' in text or 'temporary fix' in text
                
                failure_scenarios.append({
                    'pr_number': pr.get('number'),
                    'title': pr.get('title', ''),
                    'author': pr.get('author', ''),
                    'created_at': pr.get('created_at'),
                    'type': 'workaround' if has_workaround else 'fix',
                    'description': f"Failure scenario addressed in PR #{pr.get('number')}: {pr.get('title', '')}",
                    'priority': 'high' if has_workaround else 'medium'
                })
        
        # Check for high-churn files (may indicate recurring issues)
        file_churn = data_collection.get('change_frequency', {}).get('file_churn', {})
        high_churn_files = [f for f, d in file_churn.items() if d.get('total_changes', 0) > 15]
        
        for filename in high_churn_files:
            failure_scenarios.append({
                'file': filename,
                'change_count': file_churn[filename].get('total_changes', 0),
                'type': 'high_churn',
                'description': f"File with {file_churn[filename].get('total_changes', 0)} changes - may indicate recurring issues",
                'priority': 'medium'
            })
        
        self.failure_scenarios = failure_scenarios
        
        return {
            'scenarios': failure_scenarios,
            'total_scenarios': len(failure_scenarios),
            'workarounds': [s for s in failure_scenarios if s.get('type') == 'workaround'],
            'fixes': [s for s in failure_scenarios if s.get('type') == 'fix'],
            'high_priority_scenarios': [s for s in failure_scenarios if s.get('priority') == 'high']
        }
    
    def _detect_business_logic_explanations(self, prerequisite_data: Dict[str, Any], 
                                           employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 37: Business logic explanation detection"""
        data_collection = prerequisite_data.get('data_collection', {})
        code_files = data_collection.get('file_activity', {}).get('file_details', [])
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        
        business_logic_files = []
        
        # Identify files that likely contain business logic
        business_logic_patterns = [
            r'business', r'logic', r'rule', r'policy', r'validation',
            r'workflow', r'process', r'algorithm', r'calculation',
            r'service', r'handler', r'controller', r'manager'
        ]
        
        for file_info in code_files:
            path = file_info.get('path', '').lower()
            
            # Check if file matches business logic patterns
            matches_pattern = any(re.search(pattern, path, re.IGNORECASE) for pattern in business_logic_patterns)
            
            if matches_pattern:
                history = ownership_history.get(file_info.get('path', ''), [])
                unique_owners = len(set([h['author'] for h in history])) if history else 0
                
                # Filter by employee if specified
                if employee_username:
                    employee_contributions = len([h for h in history if h.get('author') == employee_username])
                    if employee_contributions == 0:
                        continue
                
                business_logic_files.append({
                    'file': file_info.get('path', ''),
                    'owner_count': unique_owners,
                    'change_count': file_info.get('modification_count', 0),
                    'description': f"Business logic file: {file_info.get('path', '')}",
                    'priority': 'high' if unique_owners <= 2 else 'medium'
                })
        
        return {
            'business_logic_files': business_logic_files,
            'total_files': len(business_logic_files),
            'high_priority_files': [f for f in business_logic_files if f.get('priority') == 'high'],
            'single_owner_logic': [f for f in business_logic_files if f.get('owner_count') == 1]
        }
    
    def _detect_operational_flow_explanations(self, prerequisite_data: Dict[str, Any], 
                                              employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 38: Operational flow explanation detection"""
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        operational = risk_analysis.get('operational_ownership', {})
        operational_files = operational.get('operational_files', [])
        
        operational_flows = []
        
        # Group operational files by type
        by_type = defaultdict(list)
        for op_file in operational_files:
            if employee_username and op_file.get('current_owner') != employee_username:
                continue
            
            file_type = op_file.get('type', 'other')
            by_type[file_type].append(op_file)
        
        # Create flow descriptions
        for file_type, files in by_type.items():
            operational_flows.append({
                'flow_type': file_type,
                'files': [f.get('file', '') for f in files],
                'file_count': len(files),
                'description': f"{file_type.replace('_', ' ').title()} operational flow with {len(files)} file(s)",
                'priority': 'critical' if file_type in ['deployment', 'ci_cd'] else 'high',
                'owners': list(set([f.get('current_owner') for f in files if f.get('current_owner')]))
            })
        
        # Also check for on-call responsibilities
        oncall = risk_analysis.get('oncall_responsibility', {})
        oncall_responsibilities = oncall.get('oncall_responsibilities', {})
        
        for owner, resp_data in oncall_responsibilities.items():
            if employee_username and owner != employee_username:
                continue
            
            if resp_data.get('total_files', 0) > 0:
                operational_flows.append({
                    'flow_type': 'oncall',
                    'owner': owner,
                    'total_responsibilities': resp_data.get('total_files', 0),
                    'deployment_count': resp_data.get('deployment_count', 0),
                    'monitoring_count': resp_data.get('monitoring_count', 0),
                    'description': f"On-call responsibilities for {owner}",
                    'priority': 'critical'
                })
        
        return {
            'operational_flows': operational_flows,
            'total_flows': len(operational_flows),
            'critical_flows': [f for f in operational_flows if f.get('priority') == 'critical'],
            'flow_types': list(set([f.get('flow_type') for f in operational_flows]))
        }

