"""
Execution & Validation Module
Implements features 68-73: Acceptance workflow, completion tracking, etc.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta


class ExecutionValidator:
    """
    Tracks execution and validates handover completion (Features 68-73)
    """
    
    def __init__(self):
        self.workflows = {}
        self.completion_status = {}
    
    def process(self, ownership_results: Dict[str, Any], 
               assignment_results: Dict[str, Any],
               kt_planning_results: Dict[str, Any],
               employee_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all execution and validation features
        
        Args:
            ownership_results: Results from ownership identification
            assignment_results: Results from smart assignment
            kt_planning_results: Results from knowledge transfer planning
            employee_username: Departing employee username
            
        Returns:
            Dictionary with all execution and validation results
        """
        results = {
            'ownership_acceptance_workflow': self._setup_acceptance_workflow(assignment_results),
            'kt_completion_tracking': self._track_kt_completion(kt_planning_results),
            'partial_handover_tracking': self._track_partial_handover(assignment_results, kt_planning_results),
            'backup_ownership_confirmation': self._confirm_backup_ownership(ownership_results, assignment_results),
            'manager_approval_flow': self._setup_manager_approval(assignment_results, kt_planning_results),
            'sla_due_date_tracking': self._track_sla_due_dates(assignment_results, kt_planning_results)
        }
        
        return results
    
    def _setup_acceptance_workflow(self, assignment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 68: Ownership acceptance workflow"""
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        
        acceptance_workflows = []
        
        for assignment in assignments:
            file_path = assignment.get('file', '')
            candidate = assignment.get('assigned_candidate', '')
            requirement_type = assignment.get('requirement_type', 'primary_successor')
            
            workflow = {
                'file': file_path,
                'candidate': candidate,
                'requirement_type': requirement_type,
                'workflow_stages': [
                    {
                        'stage': 'assignment_notification',
                        'status': 'pending',
                        'description': 'Candidate notified of assignment',
                        'required_action': 'Candidate acknowledges assignment',
                        'due_date': None,
                        'completed_at': None
                    },
                    {
                        'stage': 'knowledge_review',
                        'status': 'pending',
                        'description': 'Candidate reviews existing knowledge and documentation',
                        'required_action': 'Candidate confirms understanding of current state',
                        'due_date': None,
                        'completed_at': None
                    },
                    {
                        'stage': 'knowledge_transfer',
                        'status': 'pending',
                        'description': 'Knowledge transfer session completed',
                        'required_action': 'Complete KT session with departing employee',
                        'due_date': None,
                        'completed_at': None
                    },
                    {
                        'stage': 'hands_on_practice',
                        'status': 'pending',
                        'description': 'Candidate practices with assigned files',
                        'required_action': 'Candidate performs hands-on work under supervision',
                        'due_date': None,
                        'completed_at': None
                    },
                    {
                        'stage': 'acceptance_confirmation',
                        'status': 'pending',
                        'description': 'Candidate formally accepts ownership',
                        'required_action': 'Candidate confirms acceptance of ownership',
                        'due_date': None,
                        'completed_at': None
                    }
                ],
                'current_stage': 'assignment_notification',
                'overall_status': 'pending',
                'acceptance_date': None
            }
            
            acceptance_workflows.append(workflow)
        
        return {
            'acceptance_workflows': acceptance_workflows,
            'total_workflows': len(acceptance_workflows),
            'workflows_by_status': {
                'pending': len([w for w in acceptance_workflows if w.get('overall_status') == 'pending']),
                'in_progress': len([w for w in acceptance_workflows if w.get('overall_status') == 'in_progress']),
                'completed': len([w for w in acceptance_workflows if w.get('overall_status') == 'completed'])
            }
        }
    
    def _track_kt_completion(self, kt_planning_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 69: KT completion criteria tracking"""
        kt_recommendations = kt_planning_results.get('kt_type_recommendations', {}).get('kt_recommendations', [])
        expected_artifacts = kt_planning_results.get('expected_artifacts', {}).get('artifact_definitions', [])
        
        completion_tracking = []
        
        for kt_rec in kt_recommendations:
            file_path = kt_rec.get('file', '')
            candidate = kt_rec.get('candidate', '')
            kt_types = kt_rec.get('recommended_kt_types', [])
            
            # Find expected artifacts for this file
            artifacts = next((a.get('required_artifacts', []) for a in expected_artifacts if a.get('file') == file_path), [])
            
            completion_criteria = []
            
            # Criteria for each KT type
            for kt_type in kt_types:
                kt_type_name = kt_type.get('type', '')
                
                if kt_type_name in ['intensive_hands_on', 'hands_on_session']:
                    completion_criteria.append({
                        'criterion': f"{kt_type_name} session completed",
                        'type': 'session',
                        'required': True,
                        'status': 'pending',
                        'verification_method': 'Session attendance and participation confirmed'
                    })
                    completion_criteria.append({
                        'criterion': f"Follow-up questions answered",
                        'type': 'qa',
                        'required': True,
                        'status': 'pending',
                        'verification_method': 'Q&A session completed'
                    })
            
            if any(kt.get('type') == 'documentation' for kt in kt_types):
                completion_criteria.append({
                    'criterion': 'Documentation created/updated',
                    'type': 'documentation',
                    'required': True,
                    'status': 'pending',
                    'verification_method': 'Documentation reviewed and approved'
                })
            
            # Artifact completion criteria
            for artifact in artifacts:
                if artifact.get('required'):
                    completion_criteria.append({
                        'criterion': f"{artifact.get('artifact_type', 'artifact')} created",
                        'type': 'artifact',
                        'required': True,
                        'status': 'pending',
                        'verification_method': f"Artifact reviewed: {artifact.get('description', '')}"
                    })
            
            # Calculate completion
            total_criteria = len(completion_criteria)
            completed_criteria = sum(1 for c in completion_criteria if c.get('status') == 'completed')
            completion_percentage = (completed_criteria / total_criteria * 100) if total_criteria > 0 else 0
            
            completion_tracking.append({
                'file': file_path,
                'candidate': candidate,
                'completion_criteria': completion_criteria,
                'total_criteria': total_criteria,
                'completed_criteria': completed_criteria,
                'completion_percentage': completion_percentage,
                'status': 'complete' if completion_percentage == 100 else ('in_progress' if completion_percentage > 0 else 'not_started')
            })
        
        return {
            'completion_tracking': completion_tracking,
            'total_kt_items': len(completion_tracking),
            'completed_items': [t for t in completion_tracking if t.get('status') == 'complete'],
            'in_progress_items': [t for t in completion_tracking if t.get('status') == 'in_progress'],
            'overall_completion_percentage': sum(t.get('completion_percentage', 0) for t in completion_tracking) / len(completion_tracking) if completion_tracking else 0
        }
    
    def _track_partial_handover(self, assignment_results: Dict[str, Any], 
                               kt_planning_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 70: Partial handover tracking"""
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        kt_completion = self._track_kt_completion(kt_planning_results)
        completion_tracking = kt_completion.get('completion_tracking', [])
        
        partial_tracking = []
        
        for assignment in assignments:
            file_path = assignment.get('file', '')
            candidate = assignment.get('assigned_candidate', '')
            
            # Find completion status
            completion = next((c for c in completion_tracking if c.get('file') == file_path), None)
            
            if completion:
                completion_pct = completion.get('completion_percentage', 0)
                status = completion.get('status', 'not_started')
                
                partial_tracking.append({
                    'file': file_path,
                    'candidate': candidate,
                    'completion_percentage': completion_pct,
                    'status': status,
                    'completed_components': [c for c in completion.get('completion_criteria', []) if c.get('status') == 'completed'],
                    'pending_components': [c for c in completion.get('completion_criteria', []) if c.get('status') == 'pending'],
                    'blockers': [] if completion_pct == 100 else ['Knowledge transfer in progress'],
                    'estimated_completion_date': None,  # Would be calculated based on schedule
                    'last_updated': datetime.now().isoformat()
                })
        
        return {
            'partial_handover_tracking': partial_tracking,
            'total_items': len(partial_tracking),
            'fully_complete': [t for t in partial_tracking if t.get('completion_percentage', 0) == 100],
            'partially_complete': [t for t in partial_tracking if 0 < t.get('completion_percentage', 0) < 100],
            'not_started': [t for t in partial_tracking if t.get('completion_percentage', 0) == 0],
            'overall_progress': sum(t.get('completion_percentage', 0) for t in partial_tracking) / len(partial_tracking) if partial_tracking else 0
        }
    
    def _confirm_backup_ownership(self, ownership_results: Dict[str, Any], 
                                 assignment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 71: Backup ownership confirmation"""
        backup_requirements = ownership_results.get('backup_owner_requirements', {}).get('backup_requirements', [])
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        
        # Create assignment map
        file_to_candidate = {a.get('file', ''): a.get('assigned_candidate', '') for a in assignments}
        
        backup_confirmations = []
        
        for requirement in backup_requirements:
            file_path = requirement.get('file', '')
            primary_candidate = file_to_candidate.get(file_path, '')
            
            backup_confirmations.append({
                'file': file_path,
                'primary_owner': primary_candidate,
                'backup_owner': None,  # Would be assigned separately
                'backup_requirement_priority': requirement.get('priority', 'high'),
                'confirmation_status': 'pending',
                'confirmation_stages': [
                    {
                        'stage': 'backup_assigned',
                        'status': 'pending',
                        'description': 'Backup owner assigned',
                        'completed_at': None
                    },
                    {
                        'stage': 'backup_knowledge_transfer',
                        'status': 'pending',
                        'description': 'Backup owner receives knowledge transfer',
                        'completed_at': None
                    },
                    {
                        'stage': 'backup_confirmation',
                        'status': 'pending',
                        'description': 'Backup owner confirms understanding',
                        'completed_at': None
                    }
                ],
                'required_capabilities': requirement.get('required_capabilities', []),
                'confirmation_date': None
            })
        
        return {
            'backup_confirmations': backup_confirmations,
            'total_backup_requirements': len(backup_confirmations),
            'confirmed_backups': [b for b in backup_confirmations if b.get('confirmation_status') == 'confirmed'],
            'pending_backups': [b for b in backup_confirmations if b.get('confirmation_status') == 'pending'],
            'critical_backup_requirements': [b for b in backup_confirmations if b.get('backup_requirement_priority') == 'critical']
        }
    
    def _setup_manager_approval(self, assignment_results: Dict[str, Any], 
                               kt_planning_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 72: Manager approval flow"""
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        kt_completion = self._track_kt_completion(kt_planning_results)
        completion_tracking = kt_completion.get('completion_tracking', [])
        
        approval_workflows = []
        
        for assignment in assignments:
            file_path = assignment.get('file', '')
            candidate = assignment.get('assigned_candidate', '')
            
            # Find completion status
            completion = next((c for c in completion_tracking if c.get('file') == file_path), None)
            completion_pct = completion.get('completion_percentage', 0) if completion else 0
            
            approval_workflows.append({
                'file': file_path,
                'candidate': candidate,
                'approval_stages': [
                    {
                        'stage': 'assignment_approval',
                        'status': 'pending',
                        'description': 'Manager approves candidate assignment',
                        'approver_role': 'manager',
                        'required': True,
                        'approved_at': None,
                        'approver': None
                    },
                    {
                        'stage': 'kt_plan_approval',
                        'status': 'pending',
                        'description': 'Manager approves knowledge transfer plan',
                        'approver_role': 'manager',
                        'required': True,
                        'approved_at': None,
                        'approver': None
                    },
                    {
                        'stage': 'kt_completion_approval',
                        'status': 'pending',
                        'description': 'Manager approves knowledge transfer completion',
                        'approver_role': 'manager',
                        'required': completion_pct == 100,
                        'approved_at': None,
                        'approver': None,
                        'completion_percentage': completion_pct
                    },
                    {
                        'stage': 'ownership_transfer_approval',
                        'status': 'pending',
                        'description': 'Manager approves final ownership transfer',
                        'approver_role': 'manager',
                        'required': True,
                        'approved_at': None,
                        'approver': None
                    }
                ],
                'current_stage': 'assignment_approval',
                'overall_approval_status': 'pending',
                'final_approval_date': None
            })
        
        return {
            'approval_workflows': approval_workflows,
            'total_workflows': len(approval_workflows),
            'workflows_by_stage': {
                'assignment_approval': len([w for w in approval_workflows if w.get('current_stage') == 'assignment_approval']),
                'kt_plan_approval': len([w for w in approval_workflows if w.get('current_stage') == 'kt_plan_approval']),
                'kt_completion_approval': len([w for w in approval_workflows if w.get('current_stage') == 'kt_completion_approval']),
                'ownership_transfer_approval': len([w for w in approval_workflows if w.get('current_stage') == 'ownership_transfer_approval'])
            },
            'fully_approved': [w for w in approval_workflows if w.get('overall_approval_status') == 'approved']
        }
    
    def _track_sla_due_dates(self, assignment_results: Dict[str, Any], 
                            kt_planning_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 73: SLA & due-date tracking"""
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        kt_time = kt_planning_results.get('kt_time_estimation', {})
        time_by_file = kt_time.get('time_by_file', {})
        ownership_risks = {}  # Would come from ownership_results
        
        # Define SLA based on risk level
        sla_definitions = {
            'critical': {
                'assignment_notification_days': 1,
                'kt_completion_days': 7,
                'ownership_transfer_days': 14
            },
            'high': {
                'assignment_notification_days': 2,
                'kt_completion_days': 14,
                'ownership_transfer_days': 21
            },
            'medium': {
                'assignment_notification_days': 3,
                'kt_completion_days': 21,
                'ownership_transfer_days': 30
            },
            'low': {
                'assignment_notification_days': 5,
                'kt_completion_days': 30,
                'ownership_transfer_days': 45
            }
        }
        
        sla_tracking = []
        base_date = datetime.now()
        
        for assignment in assignments:
            file_path = assignment.get('file', '')
            candidate = assignment.get('assigned_candidate', '')
            risk_level = ownership_risks.get(file_path, {}).get('ownership_risk_level', 'medium') if ownership_risks else 'medium'
            
            sla = sla_definitions.get(risk_level, sla_definitions['medium'])
            kt_hours = time_by_file.get(file_path, {}).get('estimated_hours', 0)
            
            sla_tracking.append({
                'file': file_path,
                'candidate': candidate,
                'risk_level': risk_level,
                'sla_milestones': [
                    {
                        'milestone': 'assignment_notification',
                        'due_date': (base_date + timedelta(days=sla['assignment_notification_days'])).isoformat(),
                        'status': 'pending',
                        'sla_days': sla['assignment_notification_days']
                    },
                    {
                        'milestone': 'kt_completion',
                        'due_date': (base_date + timedelta(days=sla['kt_completion_days'])).isoformat(),
                        'status': 'pending',
                        'sla_days': sla['kt_completion_days'],
                        'estimated_kt_hours': kt_hours
                    },
                    {
                        'milestone': 'ownership_transfer',
                        'due_date': (base_date + timedelta(days=sla['ownership_transfer_days'])).isoformat(),
                        'status': 'pending',
                        'sla_days': sla['ownership_transfer_days']
                    }
                ],
                'overall_sla_status': 'on_track',
                'at_risk_milestones': [],
                'overdue_milestones': []
            })
        
        return {
            'sla_tracking': sla_tracking,
            'total_sla_items': len(sla_tracking),
            'sla_summary': {
                'on_track': len([s for s in sla_tracking if s.get('overall_sla_status') == 'on_track']),
                'at_risk': len([s for s in sla_tracking if s.get('overall_sla_status') == 'at_risk']),
                'overdue': len([s for s in sla_tracking if s.get('overall_sla_status') == 'overdue'])
            },
            'upcoming_due_dates': sorted(
                [m for s in sla_tracking for m in s.get('sla_milestones', [])],
                key=lambda x: x.get('due_date', '')
            )[:10]  # Next 10
        }

