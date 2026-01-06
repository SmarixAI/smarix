"""
Management & Quality Module
Implements features 84-89: Ownership assignment, status tracking, freshness, etc.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta


class ManagementQualityProcessor:
    """
    Manages documentation quality and lifecycle (Features 84-89)
    """
    
    def __init__(self):
        self.doc_ownership = {}
        self.status_tracking = {}
    
    def process(self, detection_results: Dict[str, Any], 
               creation_results: Dict[str, Any],
               handover_data: Optional[Dict[str, Any]] = None,
               employee_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all management and quality features
        
        Args:
            detection_results: Results from documentation detection
            creation_results: Results from AI-assisted creation
            handover_data: Handover results (optional)
            employee_username: Departing employee username
            
        Returns:
            Dictionary with all management and quality results
        """
        results = {
            'documentation_ownership': self._assign_documentation_ownership(detection_results, handover_data, employee_username),
            'documentation_status_tracking': self._track_documentation_status(detection_results, creation_results),
            'freshness_scoring': self._calculate_freshness_scores(detection_results),
            'review_approval_workflow': self._setup_review_approval_workflow(detection_results, creation_results),
            'validation_against_checklist': self._validate_against_checklist(detection_results, creation_results, handover_data),
            'ai_followup_suggestions': self._generate_followup_suggestions(detection_results, creation_results)
        }
        
        return results
    
    def _assign_documentation_ownership(self, detection_results: Dict[str, Any], 
                                       handover_data: Optional[Dict[str, Any]],
                                       employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 84: Documentation ownership assignment"""
        prioritized_docs = detection_results.get('documentation_priority', {}).get('prioritized_documentation', [])
        
        ownership_assignments = []
        
        # Get assignments from handover data if available
        handover_assignments = {}
        if handover_data:
            assignments = handover_data.get('smart_assignment', {}).get('load_balanced_assignment', {}).get('balanced_assignments', [])
            handover_assignments = {a.get('file', ''): a.get('assigned_candidate', '') for a in assignments}
        
        for doc_item in prioritized_docs:
            file_path = doc_item.get('file', '')
            priority = doc_item.get('priority_level', 'medium')
            
            # Assign owner
            owner = None
            
            # Try to get from handover assignments
            if file_path in handover_assignments:
                owner = handover_assignments[file_path]
            else:
                # Assign based on priority (would use actual assignment logic in real system)
                owner = 'tech_lead' if priority in ['critical', 'high'] else 'documentation_team'
            
            ownership_assignments.append({
                'file': file_path,
                'documentation_owner': owner,
                'assignment_reason': 'handover_assignment' if file_path in handover_assignments else 'priority_based',
                'priority': priority,
                'assigned_date': datetime.now().isoformat(),
                'status': 'assigned'
            })
        
        self.doc_ownership = {a.get('file', ''): a for a in ownership_assignments}
        
        # Group by owner
        by_owner = defaultdict(list)
        for assignment in ownership_assignments:
            by_owner[assignment.get('documentation_owner')].append(assignment)
        
        return {
            'ownership_assignments': ownership_assignments,
            'total_assignments': len(ownership_assignments),
            'assignments_by_owner': dict(by_owner),
            'owners': list(by_owner.keys()),
            'assignment_summary': {
                owner: len(assignments) 
                for owner, assignments in by_owner.items()
            }
        }
    
    def _track_documentation_status(self, detection_results: Dict[str, Any], 
                                   creation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 85: Documentation status tracking"""
        prioritized_docs = detection_results.get('documentation_priority', {}).get('prioritized_documentation', [])
        outlines = creation_results.get('documentation_outlines', {}).get('documentation_outlines', [])
        content_drafts = creation_results.get('content_drafting', {}).get('content_drafts', [])
        
        status_tracking = []
        
        for doc_item in prioritized_docs:
            file_path = doc_item.get('file', '')
            
            # Check if outline exists
            outline = next((o for o in outlines if o.get('file') == file_path), None)
            has_outline = outline is not None
            
            # Check if draft exists
            draft = next((d for d in content_drafts if d.get('file') == file_path), None)
            has_draft = draft is not None
            
            # Determine status
            if has_draft and draft.get('overall_completeness') == 'complete':
                status = 'draft_complete'
            elif has_draft:
                status = 'draft_in_progress'
            elif has_outline:
                status = 'outline_created'
            else:
                status = 'not_started'
            
            # Calculate progress
            progress = 0.0
            if has_outline:
                progress += 0.2
            if has_draft:
                draft_completeness = draft.get('overall_completeness', 'partial')
                if draft_completeness == 'complete':
                    progress = 1.0
                else:
                    progress += 0.6
            
            status_tracking.append({
                'file': file_path,
                'status': status,
                'progress_percentage': round(progress * 100, 1),
                'has_outline': has_outline,
                'has_draft': has_draft,
                'draft_sections': len(draft.get('draft_sections', [])) if draft else 0,
                'last_updated': datetime.now().isoformat(),
                'next_action': self._determine_next_action(status, has_outline, has_draft)
            })
        
        self.status_tracking = {s.get('file', ''): s for s in status_tracking}
        
        return {
            'status_tracking': status_tracking,
            'total_items': len(status_tracking),
            'status_summary': {
                'not_started': len([s for s in status_tracking if s.get('status') == 'not_started']),
                'outline_created': len([s for s in status_tracking if s.get('status') == 'outline_created']),
                'draft_in_progress': len([s for s in status_tracking if s.get('status') == 'draft_in_progress']),
                'draft_complete': len([s for s in status_tracking if s.get('status') == 'draft_complete'])
            },
            'overall_progress': sum(s.get('progress_percentage', 0) for s in status_tracking) / len(status_tracking) if status_tracking else 0
        }
    
    def _determine_next_action(self, status: str, has_outline: bool, has_draft: bool) -> str:
        """Determine next action based on status"""
        if status == 'not_started':
            return 'Create documentation outline'
        elif status == 'outline_created':
            return 'Draft content sections'
        elif status == 'draft_in_progress':
            return 'Complete draft and review'
        elif status == 'draft_complete':
            return 'Submit for review'
        else:
            return 'Review and update'
    
    def _calculate_freshness_scores(self, detection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 86: Freshness scoring"""
        existing_docs = detection_results.get('existing_documentation', {}).get('existing_documentation', [])
        
        freshness_scores = []
        
        for doc in existing_docs:
            doc_path = doc.get('path', '')
            last_modified = doc.get('last_modified', '')
            
            # Calculate freshness score (would use actual dates in real system)
            freshness_score = 0.5  # Default
            
            # Factors affecting freshness
            factors = []
            
            # Size factor (larger docs may need more frequent updates)
            doc_size = doc.get('size', 0)
            if doc_size > 100000:  # Large file
                freshness_score -= 0.1
                factors.append('large_file_may_need_updates')
            
            # Type factor
            doc_type = doc.get('type', 'general')
            if doc_type in ['api', 'runbook']:
                freshness_score -= 0.1
                factors.append(f'{doc_type}_docs_require_frequent_updates')
            
            # Related files factor (would check if related code changed)
            related_files = doc.get('related_files', [])
            if len(related_files) > 5:
                freshness_score -= 0.1
                factors.append('many_related_files_may_indicate_staleness')
            
            freshness_score = max(0.0, min(1.0, freshness_score))
            
            # Determine freshness level
            if freshness_score >= 0.7:
                freshness_level = 'fresh'
            elif freshness_score >= 0.5:
                freshness_level = 'moderate'
            elif freshness_score >= 0.3:
                freshness_level = 'stale'
            else:
                freshness_level = 'very_stale'
            
            freshness_scores.append({
                'file': doc_path,
                'freshness_score': round(freshness_score, 3),
                'freshness_level': freshness_level,
                'factors': factors,
                'recommendation': 'update_soon' if freshness_level in ['stale', 'very_stale'] else 'monitor',
                'last_modified': last_modified
            })
        
        return {
            'freshness_scores': freshness_scores,
            'total_docs_scored': len(freshness_scores),
            'freshness_summary': {
                'fresh': len([s for s in freshness_scores if s.get('freshness_level') == 'fresh']),
                'moderate': len([s for s in freshness_scores if s.get('freshness_level') == 'moderate']),
                'stale': len([s for s in freshness_scores if s.get('freshness_level') == 'stale']),
                'very_stale': len([s for s in freshness_scores if s.get('freshness_level') == 'very_stale'])
            },
            'docs_needing_update': [s for s in freshness_scores if s.get('freshness_level') in ['stale', 'very_stale']]
        }
    
    def _setup_review_approval_workflow(self, detection_results: Dict[str, Any], 
                                       creation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 87: Review & approval workflow"""
        prioritized_docs = detection_results.get('documentation_priority', {}).get('prioritized_documentation', [])
        content_drafts = creation_results.get('content_drafting', {}).get('content_drafts', [])
        
        review_workflows = []
        
        for doc_item in prioritized_docs:
            file_path = doc_item.get('file', '')
            priority = doc_item.get('priority_level', 'medium')
            
            # Check if draft exists
            draft = next((d for d in content_drafts if d.get('file') == file_path), None)
            
            if draft:
                review_workflows.append({
                    'file': file_path,
                    'priority': priority,
                    'workflow_stages': [
                        {
                            'stage': 'draft_review',
                            'status': 'pending',
                            'description': 'Technical review of draft content',
                            'reviewer_role': 'tech_lead',
                            'required': True,
                            'completed_at': None
                        },
                        {
                            'stage': 'content_review',
                            'status': 'pending',
                            'description': 'Content and clarity review',
                            'reviewer_role': 'documentation_team',
                            'required': priority in ['critical', 'high'],
                            'completed_at': None
                        },
                        {
                            'stage': 'stakeholder_review',
                            'status': 'pending',
                            'description': 'Stakeholder review and approval',
                            'reviewer_role': 'manager',
                            'required': priority == 'critical',
                            'completed_at': None
                        },
                        {
                            'stage': 'final_approval',
                            'status': 'pending',
                            'description': 'Final approval and publication',
                            'reviewer_role': 'manager',
                            'required': True,
                            'completed_at': None
                        }
                    ],
                    'current_stage': 'draft_review',
                    'overall_status': 'pending',
                    'estimated_review_days': 3 if priority == 'critical' else (2 if priority == 'high' else 1)
                })
        
        return {
            'review_workflows': review_workflows,
            'total_workflows': len(review_workflows),
            'workflows_by_priority': {
                'critical': [w for w in review_workflows if w.get('priority') == 'critical'],
                'high': [w for w in review_workflows if w.get('priority') == 'high'],
                'medium': [w for w in review_workflows if w.get('priority') == 'medium']
            },
            'workflows_by_stage': {
                'draft_review': len([w for w in review_workflows if w.get('current_stage') == 'draft_review']),
                'content_review': len([w for w in review_workflows if w.get('current_stage') == 'content_review']),
                'stakeholder_review': len([w for w in review_workflows if w.get('current_stage') == 'stakeholder_review']),
                'final_approval': len([w for w in review_workflows if w.get('current_stage') == 'final_approval'])
            }
        }
    
    def _validate_against_checklist(self, detection_results: Dict[str, Any], 
                                   creation_results: Dict[str, Any],
                                   handover_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Feature 88: Validation against knowledge checklist"""
        prioritized_docs = detection_results.get('documentation_priority', {}).get('prioritized_documentation', [])
        outlines = creation_results.get('documentation_outlines', {}).get('documentation_outlines', [])
        content_drafts = creation_results.get('content_drafting', {}).get('content_drafts', [])
        
        # Get knowledge checklist from handover if available
        knowledge_checklist = []
        if handover_data:
            kt_planning = handover_data.get('knowledge_transfer_planning', {})
            expected_artifacts = kt_planning.get('expected_artifacts', {}).get('artifact_definitions', [])
            knowledge_checklist = [a for a in expected_artifacts if any(art.get('artifact_type') == 'documentation' for art in a.get('required_artifacts', []))]
        
        validation_results = []
        
        for doc_item in prioritized_docs:
            file_path = doc_item.get('file', '')
            doc_type = doc_item.get('recommended_doc_type', 'general')
            
            # Find outline and draft
            outline = next((o for o in outlines if o.get('file') == file_path), None)
            draft = next((d for d in content_drafts if d.get('file') == file_path), None)
            
            # Validation checklist
            checklist_items = [
                {
                    'item': 'Documentation outline created',
                    'status': 'pass' if outline else 'fail',
                    'required': True
                },
                {
                    'item': 'All required sections included',
                    'status': 'pass' if outline and len(outline.get('outline', {}).get('sections', [])) >= 3 else 'fail',
                    'required': True
                },
                {
                    'item': 'Draft content created',
                    'status': 'pass' if draft else 'fail',
                    'required': True
                },
                {
                    'item': 'Code examples included',
                    'status': 'pass' if draft and any('example' in s.get('section', '').lower() for s in draft.get('draft_sections', [])) else 'fail',
                    'required': doc_type in ['api', 'usage']
                },
                {
                    'item': 'Troubleshooting section included',
                    'status': 'pass' if outline and any('troubleshooting' in s.get('section', '').lower() for s in outline.get('outline', {}).get('sections', [])) else 'fail',
                    'required': doc_type in ['runbook', 'operational']
                },
                {
                    'item': 'Architecture section included',
                    'status': 'pass' if outline and any('architecture' in s.get('section', '').lower() for s in outline.get('outline', {}).get('sections', [])) else 'fail',
                    'required': doc_type == 'architecture'
                }
            ]
            
            # Check against knowledge checklist
            knowledge_checklist_items = []
            if knowledge_checklist:
                for kc_item in knowledge_checklist:
                    if file_path in kc_item.get('file', ''):
                        knowledge_checklist_items.append({
                            'item': f"Knowledge checklist item: {kc_item.get('file', '')}",
                            'status': 'pass' if draft else 'pending',
                            'required': True
                        })
            
            # Calculate validation score
            required_items = [c for c in checklist_items if c.get('required')]
            passed_required = sum(1 for c in required_items if c.get('status') == 'pass')
            validation_score = passed_required / len(required_items) if required_items else 0
            
            validation_results.append({
                'file': file_path,
                'doc_type': doc_type,
                'checklist_items': checklist_items + knowledge_checklist_items,
                'validation_score': round(validation_score, 3),
                'validation_status': 'pass' if validation_score == 1.0 else ('partial' if validation_score > 0.5 else 'fail'),
                'required_items_passed': passed_required,
                'total_required_items': len(required_items),
                'recommendations': self._generate_validation_recommendations(checklist_items, validation_score)
            })
        
        return {
            'validation_results': validation_results,
            'total_validated': len(validation_results),
            'validation_summary': {
                'pass': len([v for v in validation_results if v.get('validation_status') == 'pass']),
                'partial': len([v for v in validation_results if v.get('validation_status') == 'partial']),
                'fail': len([v for v in validation_results if v.get('validation_status') == 'fail'])
            },
            'average_validation_score': sum(v.get('validation_score', 0) for v in validation_results) / len(validation_results) if validation_results else 0
        }
    
    def _generate_validation_recommendations(self, checklist_items: List[Dict[str, Any]], 
                                           validation_score: float) -> List[str]:
        """Generate recommendations based on validation"""
        recommendations = []
        
        failed_items = [c for c in checklist_items if c.get('status') == 'fail' and c.get('required')]
        
        for item in failed_items:
            recommendations.append(f"Complete: {item.get('item', '')}")
        
        if validation_score < 0.5:
            recommendations.append("Review documentation requirements and ensure all critical sections are included")
        
        return recommendations
    
    def _generate_followup_suggestions(self, detection_results: Dict[str, Any], 
                                      creation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 89: AI follow-up suggestions"""
        prioritized_docs = detection_results.get('documentation_priority', {}).get('prioritized_documentation', [])
        status_tracking = self._track_documentation_status(detection_results, creation_results)
        status_data = status_tracking.get('status_tracking', [])
        freshness = self._calculate_freshness_scores(detection_results)
        freshness_data = freshness.get('freshness_scores', [])
        
        followup_suggestions = []
        
        for doc_item in prioritized_docs:
            file_path = doc_item.get('file', '')
            priority = doc_item.get('priority_level', 'medium')
            
            # Get status
            status = next((s for s in status_data if s.get('file') == file_path), {})
            status_value = status.get('status', 'not_started')
            
            # Get freshness
            freshness_item = next((f for f in freshness_data if f.get('file') == file_path), {})
            freshness_level = freshness_item.get('freshness_level', 'moderate')
            
            suggestions = []
            
            # Status-based suggestions
            if status_value == 'not_started':
                suggestions.append({
                    'type': 'action',
                    'priority': 'high' if priority in ['critical', 'high'] else 'medium',
                    'suggestion': f"Start documentation for {file_path} - create outline first",
                    'action': 'create_outline',
                    'estimated_time': '1 hour'
                })
            elif status_value == 'outline_created':
                suggestions.append({
                    'type': 'action',
                    'priority': 'high',
                    'suggestion': f"Begin drafting content for {file_path}",
                    'action': 'draft_content',
                    'estimated_time': '2-4 hours'
                })
            elif status_value == 'draft_in_progress':
                suggestions.append({
                    'type': 'action',
                    'priority': 'medium',
                    'suggestion': f"Complete draft for {file_path} and submit for review",
                    'action': 'complete_draft',
                    'estimated_time': '1-2 hours'
                })
            
            # Freshness-based suggestions
            if freshness_level in ['stale', 'very_stale']:
                suggestions.append({
                    'type': 'maintenance',
                    'priority': 'medium',
                    'suggestion': f"Update documentation for {file_path} - content may be outdated",
                    'action': 'update_documentation',
                    'estimated_time': '1-2 hours'
                })
            
            # Priority-based suggestions
            if priority == 'critical':
                suggestions.append({
                    'type': 'priority',
                    'priority': 'critical',
                    'suggestion': f"Critical priority documentation - ensure comprehensive coverage",
                    'action': 'review_completeness',
                    'estimated_time': '30 minutes'
                })
            
            if suggestions:
                followup_suggestions.append({
                    'file': file_path,
                    'priority': priority,
                    'suggestions': suggestions,
                    'total_suggestions': len(suggestions),
                    'high_priority_suggestions': [s for s in suggestions if s.get('priority') in ['critical', 'high']]
                })
        
        return {
            'followup_suggestions': followup_suggestions,
            'total_files_with_suggestions': len(followup_suggestions),
            'total_suggestions': sum(len(f.get('suggestions', [])) for f in followup_suggestions),
            'suggestions_by_type': {
                'action': sum(1 for f in followup_suggestions for s in f.get('suggestions', []) if s.get('type') == 'action'),
                'maintenance': sum(1 for f in followup_suggestions for s in f.get('suggestions', []) if s.get('type') == 'maintenance'),
                'priority': sum(1 for f in followup_suggestions for s in f.get('suggestions', []) if s.get('type') == 'priority')
            }
        }

