"""
Knowledge Transfer Planning Module
Implements features 63-67: KT type recommendation, agenda generation, etc.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta


class KnowledgeTransferPlanner:
    """
    Plans knowledge transfer activities (Features 63-67)
    """
    
    def __init__(self):
        self.kt_plans = []
    
    def process(self, prerequisite_data: Dict[str, Any], 
                ownership_results: Dict[str, Any],
                assignment_results: Dict[str, Any],
                final_call_data: Optional[Dict[str, Any]] = None,
                employee_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all knowledge transfer planning features
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            ownership_results: Results from ownership identification
            assignment_results: Results from smart assignment
            final_call_data: Final Call results (optional)
            employee_username: Departing employee username
            
        Returns:
            Dictionary with all knowledge transfer planning results
        """
        results = {
            'kt_type_recommendations': self._recommend_kt_types(ownership_results, assignment_results),
            'handover_agenda': self._generate_handover_agenda(ownership_results, assignment_results, final_call_data),
            'expected_artifacts': self._define_expected_artifacts(ownership_results, assignment_results),
            'kt_time_estimation': self._estimate_kt_time(ownership_results, assignment_results),
            'kt_dependency_ordering': self._order_kt_dependencies(ownership_results, assignment_results)
        }
        
        return results
    
    def _recommend_kt_types(self, ownership_results: Dict[str, Any], 
                           assignment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 63: Knowledge transfer type recommendation"""
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        ownership_risks = ownership_results.get('ownership_risk_scoring', {}).get('ownership_risks', {})
        
        kt_recommendations = []
        
        for assignment in assignments:
            file_path = assignment.get('file', '')
            candidate = assignment.get('assigned_candidate', '')
            risk_level = ownership_risks.get(file_path, {}).get('ownership_risk_level', 'low')
            capability_score = assignment.get('capability_score', 0)
            
            # Determine KT type based on risk and capability
            kt_types = []
            
            if risk_level == 'critical':
                kt_types.append({
                    'type': 'intensive_hands_on',
                    'priority': 'required',
                    'description': 'Intensive hands-on session required for critical risk file',
                    'duration_hours': 4,
                    'format': 'in_person_or_video',
                    'follow_up_sessions': 2
                })
                kt_types.append({
                    'type': 'documentation',
                    'priority': 'required',
                    'description': 'Comprehensive documentation required',
                    'duration_hours': 2,
                    'format': 'written'
                })
            elif risk_level == 'high':
                kt_types.append({
                    'type': 'hands_on_session',
                    'priority': 'recommended',
                    'description': 'Hands-on session recommended',
                    'duration_hours': 2,
                    'format': 'in_person_or_video',
                    'follow_up_sessions': 1
                })
                kt_types.append({
                    'type': 'documentation',
                    'priority': 'recommended',
                    'description': 'Documentation recommended',
                    'duration_hours': 1,
                    'format': 'written'
                })
            else:
                kt_types.append({
                    'type': 'documentation',
                    'priority': 'recommended',
                    'description': 'Documentation sufficient for low-risk file',
                    'duration_hours': 1,
                    'format': 'written'
                })
            
            # Adjust based on capability score
            if capability_score < 0.3:
                # Low capability match - needs more intensive KT
                for kt_type in kt_types:
                    if kt_type.get('type') in ['hands_on_session', 'intensive_hands_on']:
                        kt_type['duration_hours'] = int(kt_type.get('duration_hours', 0) * 1.5)
                        kt_type['follow_up_sessions'] = (kt_type.get('follow_up_sessions', 0) + 1)
            
            kt_recommendations.append({
                'file': file_path,
                'candidate': candidate,
                'risk_level': risk_level,
                'recommended_kt_types': kt_types,
                'primary_kt_type': kt_types[0] if kt_types else None,
                'total_estimated_hours': sum(kt.get('duration_hours', 0) for kt in kt_types)
            })
        
        return {
            'kt_recommendations': kt_recommendations,
            'total_kt_sessions': sum(1 for r in kt_recommendations if any(kt.get('type') in ['hands_on_session', 'intensive_hands_on'] for kt in r.get('recommended_kt_types', []))),
            'kt_types_summary': {
                'intensive_hands_on': sum(1 for r in kt_recommendations if any(kt.get('type') == 'intensive_hands_on' for kt in r.get('recommended_kt_types', []))),
                'hands_on_session': sum(1 for r in kt_recommendations if any(kt.get('type') == 'hands_on_session' for kt in r.get('recommended_kt_types', []))),
                'documentation': sum(1 for r in kt_recommendations if any(kt.get('type') == 'documentation' for kt in r.get('recommended_kt_types', [])))
            }
        }
    
    def _generate_handover_agenda(self, ownership_results: Dict[str, Any], 
                                 assignment_results: Dict[str, Any],
                                 final_call_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Feature 64: Handover agenda generation"""
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        ownership_risks = ownership_results.get('ownership_risk_scoring', {}).get('ownership_risks', {})
        kt_recommendations = self._recommend_kt_types(ownership_results, assignment_results)
        kt_recs = kt_recommendations.get('kt_recommendations', [])
        
        # Group assignments by candidate
        assignments_by_candidate = defaultdict(list)
        for assignment in assignments:
            candidate = assignment.get('assigned_candidate')
            if candidate:
                assignments_by_candidate[candidate].append(assignment)
        
        agenda_items = []
        
        for candidate, candidate_assignments in assignments_by_candidate.items():
            # Create agenda for this candidate
            candidate_agenda = []
            
            for assignment in candidate_assignments:
                file_path = assignment.get('file', '')
                risk_level = ownership_risks.get(file_path, {}).get('ownership_risk_level', 'low')
                
                # Find KT recommendation for this file
                kt_rec = next((r for r in kt_recs if r.get('file') == file_path), None)
                
                if kt_rec:
                    primary_kt = kt_rec.get('primary_kt_type', {})
                    
                    candidate_agenda.append({
                        'file': file_path,
                        'risk_level': risk_level,
                        'kt_type': primary_kt.get('type', 'documentation'),
                        'estimated_duration_hours': primary_kt.get('duration_hours', 1),
                        'format': primary_kt.get('format', 'written'),
                        'topics': self._generate_kt_topics(file_path, assignment, ownership_risks.get(file_path, {})),
                        'priority': 'high' if risk_level in ['critical', 'high'] else 'medium'
                    })
            
            # Sort by priority
            candidate_agenda.sort(key=lambda x: ('critical' if x.get('risk_level') == 'critical' else ('high' if x.get('risk_level') == 'high' else 'medium')), reverse=True)
            
            # Calculate total time
            total_time = sum(item.get('estimated_duration_hours', 0) for item in candidate_agenda)
            
            agenda_items.append({
                'candidate': candidate,
                'agenda_items': candidate_agenda,
                'total_items': len(candidate_agenda),
                'total_estimated_hours': total_time,
                'suggested_schedule': self._suggest_schedule(candidate_agenda)
            })
        
        return {
            'handover_agenda': agenda_items,
            'total_candidates': len(agenda_items),
            'total_agenda_items': sum(len(a.get('agenda_items', [])) for a in agenda_items),
            'total_estimated_hours': sum(a.get('total_estimated_hours', 0) for a in agenda_items)
        }
    
    def _generate_kt_topics(self, file_path: str, assignment: Dict[str, Any], 
                            risk_data: Dict[str, Any]) -> List[str]:
        """Generate topics for knowledge transfer"""
        topics = [
            f"Overview of {file_path}",
            "Key functionality and purpose",
            "Dependencies and integration points",
            "Common issues and troubleshooting",
            "Testing and validation procedures"
        ]
        
        if risk_data.get('ownership_risk_level') in ['critical', 'high']:
            topics.extend([
                "Critical decision points and rationale",
                "Known failure scenarios and workarounds",
                "Operational procedures if applicable"
            ])
        
        return topics
    
    def _suggest_schedule(self, agenda_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Suggest schedule for agenda items"""
        # Group by KT type
        by_type = defaultdict(list)
        for item in agenda_items:
            by_type[item.get('kt_type', 'documentation')].append(item)
        
        schedule = {
            'sessions': [],
            'total_sessions': 0,
            'estimated_days': 0
        }
        
        # Schedule intensive sessions first
        intensive_items = by_type.get('intensive_hands_on', [])
        for item in intensive_items:
            schedule['sessions'].append({
                'type': 'intensive_hands_on',
                'files': [item.get('file')],
                'duration_hours': item.get('estimated_duration_hours', 4),
                'priority': 'high'
            })
        
        # Schedule regular hands-on sessions
        hands_on_items = by_type.get('hands_on_session', [])
        # Group multiple files into single session if possible
        if hands_on_items:
            schedule['sessions'].append({
                'type': 'hands_on_session',
                'files': [item.get('file') for item in hands_on_items[:3]],  # Group up to 3 files
                'duration_hours': sum(item.get('estimated_duration_hours', 2) for item in hands_on_items[:3]),
                'priority': 'medium'
            })
        
        schedule['total_sessions'] = len(schedule['sessions'])
        schedule['estimated_days'] = max(1, int(sum(s.get('duration_hours', 0) for s in schedule['sessions']) / 4))  # Assume 4 hours per day
        
        return schedule
    
    def _define_expected_artifacts(self, ownership_results: Dict[str, Any], 
                                  assignment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 65: Expected knowledge artifacts definition"""
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        ownership_risks = ownership_results.get('ownership_risk_scoring', {}).get('ownership_risks', {})
        
        artifact_definitions = []
        
        for assignment in assignments:
            file_path = assignment.get('file', '')
            risk_level = ownership_risks.get(file_path, {}).get('ownership_risk_level', 'low')
            
            # Define required artifacts based on risk
            artifacts = []
            
            if risk_level in ['critical', 'high']:
                artifacts.extend([
                    {
                        'artifact_type': 'documentation',
                        'description': f"Comprehensive documentation for {file_path}",
                        'required': True,
                        'format': 'markdown_or_wiki',
                        'sections': ['overview', 'architecture', 'usage', 'troubleshooting', 'examples']
                    },
                    {
                        'artifact_type': 'code_walkthrough',
                        'description': f"Code walkthrough video or transcript for {file_path}",
                        'required': True,
                        'format': 'video_or_transcript',
                        'duration_minutes': 30
                    },
                    {
                        'artifact_type': 'runbook',
                        'description': f"Operational runbook for {file_path}",
                        'required': risk_level == 'critical',
                        'format': 'markdown',
                        'sections': ['deployment', 'monitoring', 'troubleshooting', 'escalation']
                    }
                ])
            else:
                artifacts.append({
                    'artifact_type': 'documentation',
                    'description': f"Basic documentation for {file_path}",
                    'required': True,
                    'format': 'markdown',
                    'sections': ['overview', 'usage']
                })
            
            artifact_definitions.append({
                'file': file_path,
                'risk_level': risk_level,
                'required_artifacts': artifacts,
                'total_artifacts': len(artifacts),
                'required_artifacts_count': sum(1 for a in artifacts if a.get('required'))
            })
        
        return {
            'artifact_definitions': artifact_definitions,
            'total_artifacts_required': sum(a.get('required_artifacts_count', 0) for a in artifact_definitions),
            'artifacts_by_type': {
                'documentation': sum(1 for a in artifact_definitions if any(art.get('artifact_type') == 'documentation' for art in a.get('required_artifacts', []))),
                'code_walkthrough': sum(1 for a in artifact_definitions if any(art.get('artifact_type') == 'code_walkthrough' for art in a.get('required_artifacts', []))),
                'runbook': sum(1 for a in artifact_definitions if any(art.get('artifact_type') == 'runbook' for art in a.get('required_artifacts', [])))
            }
        }
    
    def _estimate_kt_time(self, ownership_results: Dict[str, Any], 
                         assignment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 66: Estimated KT time per handover"""
        kt_recommendations = self._recommend_kt_types(ownership_results, assignment_results)
        kt_recs = kt_recommendations.get('kt_recommendations', [])
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        
        # Group by candidate
        time_by_candidate = defaultdict(float)
        time_by_file = {}
        
        for kt_rec in kt_recs:
            file_path = kt_rec.get('file', '')
            candidate = kt_rec.get('candidate', '')
            total_hours = kt_rec.get('total_estimated_hours', 0)
            
            time_by_candidate[candidate] += total_hours
            time_by_file[file_path] = {
                'candidate': candidate,
                'estimated_hours': total_hours,
                'kt_types': [kt.get('type') for kt in kt_rec.get('recommended_kt_types', [])]
            }
        
        return {
            'time_by_candidate': dict(time_by_candidate),
            'time_by_file': time_by_file,
            'total_kt_hours': sum(time_by_candidate.values()),
            'average_kt_hours_per_candidate': sum(time_by_candidate.values()) / len(time_by_candidate) if time_by_candidate else 0,
            'max_kt_hours_per_candidate': max(time_by_candidate.values()) if time_by_candidate else 0,
            'kt_time_breakdown': {
                'hands_on_sessions': sum(
                    sum(kt.get('duration_hours', 0) for kt in rec.get('recommended_kt_types', []) 
                        if kt.get('type') in ['hands_on_session', 'intensive_hands_on'])
                    for rec in kt_recs
                ),
                'documentation': sum(
                    sum(kt.get('duration_hours', 0) for kt in rec.get('recommended_kt_types', []) 
                        if kt.get('type') == 'documentation')
                    for rec in kt_recs
                )
            }
        }
    
    def _order_kt_dependencies(self, ownership_results: Dict[str, Any], 
                              assignment_results: Dict[str, Any]) -> Dict[str, Any]:
        """Feature 67: KT dependency ordering"""
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        prerequisite_data = {}  # Would need to pass this in real implementation
        # For now, use ownership risks for ordering
        
        ownership_risks = ownership_results.get('ownership_risk_scoring', {}).get('ownership_risks', {})
        
        # Order by risk level and dependencies
        ordered_kt = []
        
        for assignment in assignments:
            file_path = assignment.get('file', '')
            risk_data = ownership_risks.get(file_path, {})
            risk_level = risk_data.get('ownership_risk_level', 'low')
            risk_score = risk_data.get('ownership_risk_score', 0)
            
            ordered_kt.append({
                'file': file_path,
                'candidate': assignment.get('assigned_candidate', ''),
                'risk_level': risk_level,
                'risk_score': risk_score,
                'order': 0,  # Will be set after sorting
                'dependencies': [],  # Would be populated from actual dependency analysis
                'can_start_immediately': risk_level in ['critical', 'high']
            })
        
        # Sort by risk (critical first) and score
        risk_order = {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}
        ordered_kt.sort(key=lambda x: (risk_order.get(x.get('risk_level', 'low'), 0), x.get('risk_score', 0)), reverse=True)
        
        # Assign order numbers
        for i, kt_item in enumerate(ordered_kt):
            kt_item['order'] = i + 1
        
        return {
            'ordered_kt': ordered_kt,
            'total_items': len(ordered_kt),
            'critical_first': [kt for kt in ordered_kt if kt.get('risk_level') == 'critical'],
            'dependency_chain': self._build_dependency_chain(ordered_kt)
        }
    
    def _build_dependency_chain(self, ordered_kt: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build dependency chain for KT ordering"""
        # Simple implementation - in real system would analyze actual file dependencies
        chain = []
        for kt_item in ordered_kt:
            chain.append({
                'step': kt_item.get('order', 0),
                'file': kt_item.get('file', ''),
                'can_start_after': kt_item.get('order', 1) - 1,  # Previous step
                'estimated_completion': kt_item.get('order', 1)  # Days
            })
        return chain

