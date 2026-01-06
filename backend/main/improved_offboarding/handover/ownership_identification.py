"""
Ownership Identification Module
Implements features 53-57: Ownership gaps, successor requirements, risk scoring, etc.
"""

from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
from datetime import datetime


class OwnershipIdentifier:
    """
    Identifies ownership gaps and requirements (Features 53-57)
    """
    
    def __init__(self):
        self.ownership_gaps = []
        self.successor_requirements = []
        self.ownership_risks = {}
    
    def process(self, prerequisite_data: Dict[str, Any], 
                final_call_data: Optional[Dict[str, Any]] = None,
                employee_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all ownership identification features
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            final_call_data: Final Call results (optional)
            employee_username: Username of departing employee
            
        Returns:
            Dictionary with all ownership identification results
        """
        results = {
            'ownership_gaps': self._detect_ownership_gaps(prerequisite_data, employee_username),
            'successor_requirements': self._detect_successor_requirements(prerequisite_data, final_call_data, employee_username),
            'ownership_risk_scoring': self._calculate_ownership_risk(prerequisite_data, employee_username),
            'backup_owner_requirements': self._detect_backup_owner_requirements(prerequisite_data, employee_username),
            'critical_system_validation': self._validate_critical_system_ownership(prerequisite_data, employee_username)
        }
        
        return results
    
    def _detect_ownership_gaps(self, prerequisite_data: Dict[str, Any], 
                              employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 53: Ownership gaps detection"""
        data_collection = prerequisite_data.get('data_collection', {})
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        current_owners = data_collection.get('file_ownership_history', {}).get('current_owners', {})
        single_owners = risk_analysis.get('single_owner_detection', {}).get('single_owner_files', [])
        
        gaps = []
        
        # Gap 1: Files with no current owner
        for filename, owner in current_owners.items():
            if not owner or (employee_username and owner == employee_username):
                gaps.append({
                    'gap_type': 'no_owner',
                    'file': filename,
                    'current_owner': owner if owner else None,
                    'severity': 'high',
                    'description': f"File {filename} has no current owner or owner is departing",
                    'requires_action': True
                })
        
        # Gap 2: Single-owner files where owner is departing
        if employee_username:
            for so_file in single_owners:
                if so_file.get('owner') == employee_username:
                    gaps.append({
                        'gap_type': 'single_owner_departing',
                        'file': so_file.get('file', ''),
                        'current_owner': employee_username,
                        'owner_count': 1,
                        'severity': 'critical',
                        'description': f"File {so_file.get('file', '')} has only one owner who is departing",
                        'requires_action': True
                    })
        
        # Gap 3: High-risk files with departing owner
        knowledge_loss_risk = risk_analysis.get('knowledge_loss_risk', {})
        file_risk_scores = knowledge_loss_risk.get('file_risk_scores', {})
        
        for filename, risk_data in file_risk_scores.items():
            if risk_data.get('risk_level') == 'high':
                owner = risk_data.get('current_owner')
                if employee_username and owner == employee_username:
                    gaps.append({
                        'gap_type': 'high_risk_departing_owner',
                        'file': filename,
                        'current_owner': owner,
                        'risk_score': risk_data.get('risk_score', 0),
                        'severity': 'critical',
                        'description': f"High-risk file {filename} owned by departing employee",
                        'requires_action': True
                    })
        
        # Gap 4: Operational files with departing owner
        operational = risk_analysis.get('operational_ownership', {})
        operational_files = operational.get('operational_files', [])
        
        for op_file in operational_files:
            if employee_username and op_file.get('current_owner') == employee_username:
                gaps.append({
                    'gap_type': 'operational_departing_owner',
                    'file': op_file.get('file', ''),
                    'file_type': op_file.get('type', ''),
                    'current_owner': employee_username,
                    'severity': 'critical',
                    'description': f"Operational {op_file.get('type', 'file')} owned by departing employee",
                    'requires_action': True
                })
        
        # Group gaps by severity
        gaps_by_severity = defaultdict(list)
        for gap in gaps:
            gaps_by_severity[gap.get('severity', 'medium')].append(gap)
        
        self.ownership_gaps = gaps
        
        return {
            'ownership_gaps': gaps,
            'total_gaps': len(gaps),
            'gaps_by_severity': dict(gaps_by_severity),
            'critical_gaps': gaps_by_severity.get('critical', []),
            'high_severity_gaps': gaps_by_severity.get('high', []),
            'gaps_by_type': self._group_gaps_by_type(gaps)
        }
    
    def _group_gaps_by_type(self, gaps: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group gaps by type"""
        gaps_by_type = defaultdict(list)
        for gap in gaps:
            gaps_by_type[gap.get('gap_type', 'unknown')].append(gap)
        return dict(gaps_by_type)
    
    def _detect_successor_requirements(self, prerequisite_data: Dict[str, Any], 
                                      final_call_data: Optional[Dict[str, Any]],
                                      employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 54: Successor requirement detection"""
        ownership_gaps = self._detect_ownership_gaps(prerequisite_data, employee_username)
        gaps = ownership_gaps.get('ownership_gaps', [])
        
        requirements = []
        
        # Analyze each gap to determine successor requirements
        for gap in gaps:
            gap_type = gap.get('gap_type', '')
            file_path = gap.get('file', '')
            severity = gap.get('severity', 'medium')
            
            # Determine requirements based on gap type
            if gap_type == 'single_owner_departing':
                requirements.append({
                    'requirement_id': f"req_{len(requirements) + 1}",
                    'gap_id': gap.get('gap_type', ''),
                    'file': file_path,
                    'requirement_type': 'primary_successor',
                    'priority': 'critical',
                    'description': f"Primary successor required for {file_path}",
                    'required_capabilities': self._infer_required_capabilities(file_path, prerequisite_data),
                    'urgency': 'immediate'
                })
            
            elif gap_type == 'high_risk_departing_owner':
                requirements.append({
                    'requirement_id': f"req_{len(requirements) + 1}",
                    'gap_id': gap.get('gap_type', ''),
                    'file': file_path,
                    'requirement_type': 'primary_successor',
                    'priority': 'high',
                    'description': f"Primary successor required for high-risk file {file_path}",
                    'required_capabilities': self._infer_required_capabilities(file_path, prerequisite_data),
                    'urgency': 'high'
                })
            
            elif gap_type == 'operational_departing_owner':
                requirements.append({
                    'requirement_id': f"req_{len(requirements) + 1}",
                    'gap_id': gap.get('gap_type', ''),
                    'file': file_path,
                    'requirement_type': 'operational_successor',
                    'priority': 'critical',
                    'description': f"Operational successor required for {file_path}",
                    'required_capabilities': ['operational_knowledge', 'deployment_expertise'],
                    'urgency': 'immediate'
                })
            
            # Always require backup for critical/high severity
            if severity in ['critical', 'high']:
                requirements.append({
                    'requirement_id': f"req_{len(requirements) + 1}",
                    'gap_id': gap.get('gap_type', ''),
                    'file': file_path,
                    'requirement_type': 'backup_successor',
                    'priority': 'high' if severity == 'critical' else 'medium',
                    'description': f"Backup successor recommended for {file_path}",
                    'required_capabilities': self._infer_required_capabilities(file_path, prerequisite_data),
                    'urgency': 'high' if severity == 'critical' else 'medium'
                })
        
        # Group by requirement type
        requirements_by_type = defaultdict(list)
        for req in requirements:
            requirements_by_type[req.get('requirement_type')].append(req)
        
        self.successor_requirements = requirements
        
        return {
            'successor_requirements': requirements,
            'total_requirements': len(requirements),
            'requirements_by_type': dict(requirements_by_type),
            'critical_requirements': [r for r in requirements if r.get('priority') == 'critical'],
            'primary_successor_requirements': requirements_by_type.get('primary_successor', []),
            'backup_successor_requirements': requirements_by_type.get('backup_successor', [])
        }
    
    def _infer_required_capabilities(self, file_path: str, 
                                   prerequisite_data: Dict[str, Any]) -> List[str]:
        """Infer required capabilities from file path and context"""
        capabilities = []
        file_lower = file_path.lower()
        
        # Technology-based capabilities
        if any(ext in file_lower for ext in ['.py', '.pyx']):
            capabilities.append('python')
        elif any(ext in file_lower for ext in ['.js', '.ts', '.jsx', '.tsx']):
            capabilities.append('javascript')
        elif any(ext in file_lower for ext in ['.java']):
            capabilities.append('java')
        elif any(ext in file_lower for ext in ['.go']):
            capabilities.append('go')
        elif any(ext in file_lower for ext in ['.rs']):
            capabilities.append('rust')
        elif any(ext in file_lower for ext in ['.cpp', '.c', '.h', '.hpp']):
            capabilities.append('c_cpp')
        
        # Domain-based capabilities
        if 'deploy' in file_lower or 'docker' in file_lower or 'k8s' in file_lower:
            capabilities.append('devops')
            capabilities.append('deployment')
        if 'config' in file_lower or 'settings' in file_lower:
            capabilities.append('configuration_management')
        if 'test' in file_lower:
            capabilities.append('testing')
        if 'api' in file_lower or 'service' in file_lower:
            capabilities.append('api_development')
        if 'database' in file_lower or 'db' in file_lower or 'sql' in file_lower:
            capabilities.append('database')
        
        return capabilities if capabilities else ['general_software_development']
    
    def _calculate_ownership_risk(self, prerequisite_data: Dict[str, Any], 
                                 employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 55: Ownership risk scoring"""
        data_collection = prerequisite_data.get('data_collection', {})
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        knowledge_loss_risk = risk_analysis.get('knowledge_loss_risk', {})
        file_risk_scores = knowledge_loss_risk.get('file_risk_scores', {})
        criticality = risk_analysis.get('criticality_scoring', {}).get('criticality_scores', {})
        
        ownership_risks = {}
        
        for filename in set(list(ownership_history.keys()) + list(file_risk_scores.keys())):
            risk_score = 0.0
            risk_factors = []
            
            # Factor 1: Knowledge loss risk
            knowledge_risk = file_risk_scores.get(filename, {})
            if knowledge_risk.get('risk_level') == 'high':
                risk_score += 0.3
                risk_factors.append('high_knowledge_loss_risk')
            
            # Factor 2: Criticality
            crit_data = criticality.get(filename, {})
            if crit_data.get('criticality_level') in ['critical', 'high']:
                risk_score += 0.25
                risk_factors.append(f"high_criticality_{crit_data.get('criticality_level')}")
            
            # Factor 3: Owner count
            history = ownership_history.get(filename, [])
            if history:
                unique_owners = len(set([h.get('author') for h in history]))
                if unique_owners == 1:
                    risk_score += 0.25
                    risk_factors.append('single_owner')
                elif unique_owners == 2:
                    risk_score += 0.15
                    risk_factors.append('two_owners')
            
            # Factor 4: Departing employee ownership
            if employee_username:
                current_owner = knowledge_risk.get('current_owner') or (history[-1].get('author') if history else None)
                if current_owner == employee_username:
                    risk_score += 0.2
                    risk_factors.append('departing_employee_owner')
            
            ownership_risks[filename] = {
                'file': filename,
                'ownership_risk_score': min(risk_score, 1.0),
                'ownership_risk_level': 'critical' if risk_score >= 0.7 else ('high' if risk_score >= 0.5 else ('medium' if risk_score >= 0.3 else 'low')),
                'risk_factors': risk_factors,
                'requires_successor': risk_score >= 0.5,
                'requires_backup': risk_score >= 0.7
            }
        
        # Sort by risk score
        sorted_risks = sorted(ownership_risks.items(), key=lambda x: x[1]['ownership_risk_score'], reverse=True)
        
        self.ownership_risks = ownership_risks
        
        return {
            'ownership_risks': ownership_risks,
            'high_risk_files': [f for f, r in sorted_risks[:20] if r.get('ownership_risk_level') in ['critical', 'high']],
            'critical_risk_files': [f for f, r in sorted_risks if r.get('ownership_risk_level') == 'critical'],
            'files_requiring_successor': [f for f, r in ownership_risks.items() if r.get('requires_successor')],
            'files_requiring_backup': [f for f, r in ownership_risks.items() if r.get('requires_backup')],
            'risk_summary': {
                'critical': sum(1 for r in ownership_risks.values() if r.get('ownership_risk_level') == 'critical'),
                'high': sum(1 for r in ownership_risks.values() if r.get('ownership_risk_level') == 'high'),
                'medium': sum(1 for r in ownership_risks.values() if r.get('ownership_risk_level') == 'medium'),
                'low': sum(1 for r in ownership_risks.values() if r.get('ownership_risk_level') == 'low')
            }
        }
    
    def _detect_backup_owner_requirements(self, prerequisite_data: Dict[str, Any], 
                                          employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 56: Backup owner requirement detection"""
        ownership_risks = self._calculate_ownership_risk(prerequisite_data, employee_username)
        high_risk_files = ownership_risks.get('files_requiring_backup', [])
        ownership_risks_data = ownership_risks.get('ownership_risks', {})
        
        backup_requirements = []
        
        for filename in high_risk_files:
            risk_data = ownership_risks_data.get(filename, {})
            
            backup_requirements.append({
                'file': filename,
                'risk_score': risk_data.get('ownership_risk_score', 0),
                'risk_level': risk_data.get('ownership_risk_level', 'medium'),
                'priority': 'critical' if risk_data.get('ownership_risk_level') == 'critical' else 'high',
                'required_capabilities': self._infer_required_capabilities(filename, prerequisite_data),
                'description': f"Backup owner required for {filename} due to {risk_data.get('ownership_risk_level')} ownership risk",
                'urgency': 'immediate' if risk_data.get('ownership_risk_level') == 'critical' else 'high'
            })
        
        # Also check operational files
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        operational = risk_analysis.get('operational_ownership', {})
        operational_files = operational.get('operational_files', [])
        
        for op_file in operational_files:
            if employee_username and op_file.get('current_owner') == employee_username:
                backup_requirements.append({
                    'file': op_file.get('file', ''),
                    'file_type': op_file.get('type', ''),
                    'risk_score': 0.8,  # Operational files are high risk
                    'risk_level': 'critical',
                    'priority': 'critical',
                    'required_capabilities': ['operational_knowledge', 'devops'],
                    'description': f"Backup owner required for operational {op_file.get('type', 'file')}",
                    'urgency': 'immediate'
                })
        
        return {
            'backup_requirements': backup_requirements,
            'total_backup_requirements': len(backup_requirements),
            'critical_backup_requirements': [r for r in backup_requirements if r.get('priority') == 'critical'],
            'backup_requirements_by_priority': {
                'critical': [r for r in backup_requirements if r.get('priority') == 'critical'],
                'high': [r for r in backup_requirements if r.get('priority') == 'high']
            }
        }
    
    def _validate_critical_system_ownership(self, prerequisite_data: Dict[str, Any], 
                                           employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 57: Critical system ownership validation"""
        data_collection = prerequisite_data.get('data_collection', {})
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        
        critical_subsystems = data_collection.get('critical_subsystems', {}).get('critical_subsystems', [])
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        ownership_risks = self._calculate_ownership_risk(prerequisite_data, employee_username)
        ownership_risks_data = ownership_risks.get('ownership_risks', {})
        
        validation_results = []
        
        for subsystem in critical_subsystems:
            subsystem_path = subsystem.get('path', '')
            subsystem_score = subsystem.get('score', 0)
            
            # Find files in this subsystem
            files_in_subsystem = []
            for filename in ownership_history.keys():
                if filename.startswith(subsystem_path) or subsystem_path in filename:
                    files_in_subsystem.append(filename)
            
            # Validate ownership for each file
            validation_status = 'valid'
            issues = []
            departing_owner_files = []
            
            for filename in files_in_subsystem:
                risk_data = ownership_risks_data.get(filename, {})
                risk_level = risk_data.get('ownership_risk_level', 'low')
                
                if risk_level in ['critical', 'high']:
                    validation_status = 'needs_attention'
                    issues.append(f"File {filename} has {risk_level} ownership risk")
                
                if employee_username:
                    history = ownership_history.get(filename, [])
                    if history and history[-1].get('author') == employee_username:
                        departing_owner_files.append(filename)
                        validation_status = 'critical'
                        issues.append(f"File {filename} owned by departing employee")
            
            validation_results.append({
                'subsystem': subsystem_path,
                'subsystem_score': subsystem_score,
                'files_count': len(files_in_subsystem),
                'validation_status': validation_status,
                'issues': issues,
                'departing_owner_files': departing_owner_files,
                'requires_action': validation_status != 'valid',
                'action_required': 'Assign successor and backup owner' if validation_status == 'critical' else 'Review ownership'
            })
        
        # Overall validation summary
        valid_count = sum(1 for v in validation_results if v.get('validation_status') == 'valid')
        needs_attention_count = sum(1 for v in validation_results if v.get('validation_status') == 'needs_attention')
        critical_count = sum(1 for v in validation_results if v.get('validation_status') == 'critical')
        
        return {
            'validation_results': validation_results,
            'validation_summary': {
                'total_subsystems': len(validation_results),
                'valid': valid_count,
                'needs_attention': needs_attention_count,
                'critical': critical_count,
                'overall_status': 'critical' if critical_count > 0 else ('needs_attention' if needs_attention_count > 0 else 'valid')
            },
            'critical_subsystems': [v for v in validation_results if v.get('validation_status') == 'critical'],
            'subsystems_requiring_action': [v for v in validation_results if v.get('requires_action')]
        }

