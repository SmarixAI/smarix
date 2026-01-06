"""
Execution & Tracking Module
Implements features 46-52: Task grouping, checklists, validation, approval, etc.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
import json


class ExecutionTracker:
    """
    Tracks Final Call execution and completion (Features 46-52)
    """
    
    def __init__(self):
        self.tasks = []
        self.checklists = {}
        self.completion_status = {}
    
    def process(self, topic_results: Dict[str, Any], 
               discussion_results: Dict[str, Any],
               employee_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all execution and tracking features
        
        Args:
            topic_results: Results from topic identification
            discussion_results: Results from AI-guided discussion
            employee_username: Departing employee username
            
        Returns:
            Dictionary with all execution tracking results
        """
        results = {
            'task_grouping': self._group_tasks_by_knowledge_unit(topic_results, discussion_results),
            'completion_checklists': self._create_completion_checklists(topic_results, discussion_results),
            'recording_linkage': self._setup_recording_linkage(topic_results),
            'knowledge_validation_checklist': self._create_validation_checklist(topic_results, discussion_results),
            'manager_approval_workflow': self._setup_manager_approval_workflow(topic_results),
            'partial_completion_tracking': self._setup_partial_completion_tracking(topic_results),
            'escalation_workflow': self._setup_escalation_workflow(topic_results)
        }
        
        return results
    
    def _group_tasks_by_knowledge_unit(self, topic_results: Dict[str, Any], 
                                       discussion_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 46: Final Call task grouping by knowledge unit"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        agenda = discussion_results.get('final_call_agenda', {}).get('agenda_items', [])
        
        # Group tasks by knowledge unit (category)
        tasks_by_unit = defaultdict(list)
        
        for topic in topics:
            category = topic.get('category', 'other')
            topic_id = topic.get('topic_id', '')
            
            # Find corresponding agenda item
            agenda_item = next((a for a in agenda if a.get('topic_id') == topic_id), None)
            
            task = {
                'task_id': f"task_{topic_id}",
                'topic_id': topic_id,
                'title': topic.get('title', ''),
                'category': category,
                'priority': topic.get('priority', 'medium'),
                'knowledge_unit': category,
                'related_files': topic.get('related_files', [])[:5],
                'estimated_time': agenda_item.get('estimated_time_minutes', 0) if agenda_item else 0,
                'discussion_points': agenda_item.get('discussion_points', []) if agenda_item else [],
                'status': 'pending',
                'assigned_to': None,
                'due_date': None
            }
            
            tasks_by_unit[category].append(task)
            self.tasks.append(task)
        
        # Create summary
        unit_summary = {}
        for unit, tasks in tasks_by_unit.items():
            unit_summary[unit] = {
                'task_count': len(tasks),
                'total_estimated_time': sum(t.get('estimated_time', 0) for t in tasks),
                'critical_tasks': [t for t in tasks if t.get('priority') == 'critical'],
                'high_priority_tasks': [t for t in tasks if t.get('priority') in ['critical', 'high']]
            }
        
        return {
            'tasks_by_knowledge_unit': dict(tasks_by_unit),
            'unit_summary': unit_summary,
            'total_tasks': len(self.tasks),
            'tasks_by_priority': {
                'critical': [t for t in self.tasks if t.get('priority') == 'critical'],
                'high': [t for t in self.tasks if t.get('priority') == 'high'],
                'medium': [t for t in self.tasks if t.get('priority') == 'medium'],
                'low': [t for t in self.tasks if t.get('priority') == 'low']
            }
        }
    
    def _create_completion_checklists(self, topic_results: Dict[str, Any], 
                                     discussion_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 47: Completion checklist per topic"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        agenda = discussion_results.get('final_call_agenda', {}).get('agenda_items', [])
        questions = discussion_results.get('questions_per_topic', {}).get('questions_by_topic', {})
        
        checklists = {}
        
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            agenda_item = next((a for a in agenda if a.get('topic_id') == topic_id), None)
            topic_questions = questions.get(topic_id, {}).get('questions', [])
            
            # Create checklist items
            checklist_items = []
            
            # Item 1: Topic discussed
            checklist_items.append({
                'item_id': f"{topic_id}_discussed",
                'description': f"Topic '{topic.get('title', '')}' has been discussed",
                'type': 'discussion',
                'required': True,
                'status': 'pending'
            })
            
            # Item 2: Key questions answered
            critical_questions = [q for q in topic_questions if q.get('priority') == 'critical']
            for i, question in enumerate(critical_questions[:5]):  # Top 5 critical questions
                checklist_items.append({
                    'item_id': f"{topic_id}_question_{i+1}",
                    'description': f"Question answered: {question.get('question', '')[:100]}",
                    'type': 'question',
                    'required': True,
                    'status': 'pending',
                    'question': question.get('question', '')
                })
            
            # Item 3: Related files reviewed
            related_files = topic.get('related_files', [])
            for file_path in related_files[:3]:  # Top 3 files
                checklist_items.append({
                    'item_id': f"{topic_id}_file_{file_path.replace('/', '_')}",
                    'description': f"File reviewed: {file_path}",
                    'type': 'file_review',
                    'required': len(related_files) <= 3,  # Required if few files
                    'status': 'pending',
                    'file_path': file_path
                })
            
            # Item 4: Documentation created/updated
            checklist_items.append({
                'item_id': f"{topic_id}_documentation",
                'description': f"Documentation created or updated for '{topic.get('title', '')}'",
                'type': 'documentation',
                'required': topic.get('priority') in ['critical', 'high'],
                'status': 'pending'
            })
            
            # Item 5: Knowledge transfer confirmed
            checklist_items.append({
                'item_id': f"{topic_id}_knowledge_transfer",
                'description': f"Knowledge transfer confirmed for '{topic.get('title', '')}'",
                'type': 'knowledge_transfer',
                'required': True,
                'status': 'pending'
            })
            
            checklists[topic_id] = {
                'topic_id': topic_id,
                'topic_title': topic.get('title', ''),
                'checklist_items': checklist_items,
                'total_items': len(checklist_items),
                'required_items': [item for item in checklist_items if item.get('required')],
                'completion_status': {
                    'total': len(checklist_items),
                    'completed': 0,
                    'pending': len(checklist_items),
                    'percentage': 0.0
                }
            }
        
        self.checklists = checklists
        
        return {
            'checklists_by_topic': checklists,
            'total_checklist_items': sum(len(c.get('checklist_items', [])) for c in checklists.values()),
            'required_items_count': sum(
                len(c.get('required_items', [])) 
                for c in checklists.values()
            ),
            'completion_summary': {
                'topics_with_checklists': len(checklists),
                'total_items': sum(len(c.get('checklist_items', [])) for c in checklists.values()),
                'all_pending': True  # Initially all pending
            }
        }
    
    def _setup_recording_linkage(self, topic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 48: Recording & transcript linkage"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        
        recording_structure = {}
        
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            
            recording_structure[topic_id] = {
                'topic_id': topic_id,
                'topic_title': topic.get('title', ''),
                'recording_metadata': {
                    'recording_id': None,  # To be filled when recording is created
                    'recording_url': None,
                    'recording_date': None,
                    'recording_duration_minutes': None,
                    'recording_format': 'video',  # or 'audio'
                    'transcript_available': False,
                    'transcript_url': None,
                    'transcript_quality': None
                },
                'timestamps': {
                    'start_time': None,
                    'end_time': None,
                    'key_moments': []  # List of timestamps for important moments
                },
                'linked_resources': {
                    'related_files': topic.get('related_files', [])[:5],
                    'documentation_links': [],
                    'code_references': []
                }
            }
        
        return {
            'recording_structure': recording_structure,
            'total_topics_to_record': len(recording_structure),
            'recording_requirements': {
                'format': 'video preferred, audio acceptable',
                'quality': 'HD video or high-quality audio',
                'transcription': 'Required for all critical and high-priority topics',
                'storage': 'Secure, accessible location'
            }
        }
    
    def _create_validation_checklist(self, topic_results: Dict[str, Any], 
                                     discussion_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 49: Knowledge validation checklist"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        questions = discussion_results.get('questions_per_topic', {}).get('questions_by_topic', {})
        
        validation_checklist = {
            'validation_criteria': [],
            'validation_by_topic': {}
        }
        
        # General validation criteria
        general_criteria = [
            {
                'criterion_id': 'knowledge_transferred',
                'description': 'Knowledge has been successfully transferred to at least one other person',
                'validation_method': 'Confirm with knowledge recipient',
                'required': True
            },
            {
                'criterion_id': 'documentation_created',
                'description': 'Key knowledge has been documented',
                'validation_method': 'Review documentation artifacts',
                'required': True
            },
            {
                'criterion_id': 'questions_answered',
                'description': 'All critical questions have been answered',
                'validation_method': 'Review discussion transcript or notes',
                'required': True
            },
            {
                'criterion_id': 'stakeholders_informed',
                'description': 'Relevant stakeholders have been informed',
                'validation_method': 'Confirm stakeholder attendance or access to materials',
                'required': True
            },
            {
                'criterion_id': 'backup_owner_identified',
                'description': 'Backup owner has been identified for critical knowledge',
                'validation_method': 'Confirm backup owner assignment',
                'required': False  # Only for critical topics
            }
        ]
        
        validation_checklist['validation_criteria'] = general_criteria
        
        # Topic-specific validation
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            topic_questions = questions.get(topic_id, {}).get('questions', [])
            critical_questions = [q for q in topic_questions if q.get('priority') == 'critical']
            
            topic_validation = {
                'topic_id': topic_id,
                'topic_title': topic.get('title', ''),
                'validation_items': [],
                'required_validations': [],
                'optional_validations': []
            }
            
            # Add general criteria
            for criterion in general_criteria:
                if criterion.get('required') or topic.get('priority') == 'critical':
                    topic_validation['required_validations'].append(criterion.get('criterion_id'))
            
            # Add question-specific validation
            for question in critical_questions:
                topic_validation['validation_items'].append({
                    'item_id': f"{topic_id}_question_{question.get('question', '')[:50]}",
                    'description': f"Question answered: {question.get('question', '')[:100]}",
                    'validation_method': 'Review discussion transcript',
                    'required': True
                })
            
            validation_checklist['validation_by_topic'][topic_id] = topic_validation
        
        return {
            'validation_checklist': validation_checklist,
            'total_validation_criteria': len(general_criteria),
            'topics_with_validation': len(validation_checklist['validation_by_topic']),
            'validation_summary': {
                'required_validations': sum(
                    len(v.get('required_validations', [])) 
                    for v in validation_checklist['validation_by_topic'].values()
                ),
                'total_validation_items': sum(
                    len(v.get('validation_items', [])) 
                    for v in validation_checklist['validation_by_topic'].values()
                )
            }
        }
    
    def _setup_manager_approval_workflow(self, topic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 50: Manager approval for completion"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        
        approval_workflow = {
            'approval_stages': [
                {
                    'stage': 'topic_discussion',
                    'description': 'All topics have been discussed',
                    'approver_role': 'manager',
                    'required': True
                },
                {
                    'stage': 'knowledge_transfer',
                    'description': 'Knowledge transfer has been completed',
                    'approver_role': 'manager',
                    'required': True
                },
                {
                    'stage': 'documentation',
                    'description': 'Documentation has been created/updated',
                    'approver_role': 'manager',
                    'required': True
                },
                {
                    'stage': 'validation',
                    'description': 'Knowledge validation checklist completed',
                    'approver_role': 'manager',
                    'required': True
                },
                {
                    'stage': 'final_approval',
                    'description': 'Final Call completion approved',
                    'approver_role': 'manager',
                    'required': True
                }
            ],
            'approval_by_topic': {}
        }
        
        # Setup approval for each topic
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            priority = topic.get('priority', 'medium')
            
            approval_workflow['approval_by_topic'][topic_id] = {
                'topic_id': topic_id,
                'topic_title': topic.get('title', ''),
                'priority': priority,
                'approval_required': priority in ['critical', 'high'],
                'approval_status': 'pending',
                'approver': None,
                'approval_date': None,
                'approval_notes': None,
                'approval_stages': [
                    {
                        'stage': 'discussion_complete',
                        'status': 'pending',
                        'approver': None,
                        'approved_at': None
                    },
                    {
                        'stage': 'knowledge_transferred',
                        'status': 'pending',
                        'approver': None,
                        'approved_at': None
                    }
                ]
            }
        
        return {
            'approval_workflow': approval_workflow,
            'total_topics_requiring_approval': sum(
                1 for t in approval_workflow['approval_by_topic'].values() 
                if t.get('approval_required')
            ),
            'approval_summary': {
                'stages': len(approval_workflow['approval_stages']),
                'topics': len(approval_workflow['approval_by_topic']),
                'all_pending': True
            }
        }
    
    def _setup_partial_completion_tracking(self, topic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 51: Partial completion tracking"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        
        partial_tracking = {}
        
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            
            partial_tracking[topic_id] = {
                'topic_id': topic_id,
                'topic_title': topic.get('title', ''),
                'completion_status': 'not_started',  # not_started, in_progress, partially_complete, complete
                'completion_percentage': 0.0,
                'completed_components': [],
                'pending_components': [
                    'discussion',
                    'questions_answered',
                    'documentation',
                    'knowledge_transfer'
                ],
                'partial_completion_notes': [],
                'last_updated': None,
                'estimated_remaining_time_minutes': None
            }
        
        return {
            'partial_completion_tracking': partial_tracking,
            'completion_summary': {
                'total_topics': len(partial_tracking),
                'not_started': len([t for t in partial_tracking.values() if t.get('completion_status') == 'not_started']),
                'in_progress': len([t for t in partial_tracking.values() if t.get('completion_status') == 'in_progress']),
                'partially_complete': len([t for t in partial_tracking.values() if t.get('completion_status') == 'partially_complete']),
                'complete': len([t for t in partial_tracking.values() if t.get('completion_status') == 'complete']),
                'overall_completion_percentage': 0.0
            }
        }
    
    def _setup_escalation_workflow(self, topic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 52: Escalation for missed Final Calls"""
        topics = topic_results.get('final_call_topics', {}).get('topics', [])
        
        escalation_workflow = {
            'escalation_triggers': [
                {
                    'trigger': 'final_call_not_scheduled',
                    'description': 'Final Call has not been scheduled within 2 weeks of departure notice',
                    'escalation_level': 'manager',
                    'action': 'Notify manager to schedule Final Call'
                },
                {
                    'trigger': 'final_call_missed',
                    'description': 'Scheduled Final Call was missed or cancelled',
                    'escalation_level': 'manager',
                    'action': 'Reschedule and escalate to manager'
                },
                {
                    'trigger': 'critical_topic_not_discussed',
                    'description': 'Critical priority topic was not discussed in Final Call',
                    'escalation_level': 'manager',
                    'action': 'Schedule follow-up session for critical topics'
                },
                {
                    'trigger': 'knowledge_transfer_incomplete',
                    'description': 'Knowledge transfer validation failed',
                    'escalation_level': 'manager',
                    'action': 'Review and complete knowledge transfer'
                },
                {
                    'trigger': 'documentation_missing',
                    'description': 'Required documentation not created',
                    'escalation_level': 'tech_lead',
                    'action': 'Create missing documentation'
                }
            ],
            'escalation_paths': {
                'level_1': {
                    'role': 'tech_lead',
                    'description': 'Technical lead reviews and addresses issue'
                },
                'level_2': {
                    'role': 'manager',
                    'description': 'Manager reviews and takes action'
                },
                'level_3': {
                    'role': 'director',
                    'description': 'Director review for critical issues'
                }
            },
            'escalation_by_topic': {}
        }
        
        # Setup escalation for critical topics
        for topic in topics:
            topic_id = topic.get('topic_id', '')
            priority = topic.get('priority', 'medium')
            
            if priority in ['critical', 'high']:
                escalation_workflow['escalation_by_topic'][topic_id] = {
                    'topic_id': topic_id,
                    'topic_title': topic.get('title', ''),
                    'priority': priority,
                    'escalation_required_if_missed': True,
                    'escalation_level': 'manager' if priority == 'critical' else 'tech_lead',
                    'escalation_triggers': [
                        'topic_not_discussed',
                        'knowledge_transfer_incomplete',
                        'documentation_missing'
                    ],
                    'escalation_actions': [
                        'Schedule follow-up session',
                        'Assign backup owner',
                        'Create emergency documentation'
                    ]
                }
        
        return {
            'escalation_workflow': escalation_workflow,
            'topics_with_escalation': len(escalation_workflow['escalation_by_topic']),
            'escalation_summary': {
                'total_triggers': len(escalation_workflow['escalation_triggers']),
                'escalation_levels': len(escalation_workflow['escalation_paths']),
                'critical_topics_requiring_escalation': len([
                    t for t in escalation_workflow['escalation_by_topic'].values() 
                    if t.get('priority') == 'critical'
                ])
            }
        }

