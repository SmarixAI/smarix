"""
Smart Assignment Module
Implements features 58-62: Capability-based recommendations, contribution matching, etc.
"""

from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
import math


class SmartAssignmentProcessor:
    """
    Processes smart assignment features (58-62)
    """
    
    def __init__(self):
        self.assignments = []
        self.candidate_scores = {}
    
    def process(self, prerequisite_data: Dict[str, Any], 
                ownership_identification_results: Dict[str, Any],
                employee_username: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all smart assignment features
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            ownership_identification_results: Results from ownership identification
            employee_username: Departing employee username
            
        Returns:
            Dictionary with all smart assignment results
        """
        results = {
            'capability_based_recommendations': self._recommend_by_capability(prerequisite_data, ownership_identification_results, employee_username),
            'contribution_based_matching': self._match_by_contributions(prerequisite_data, ownership_identification_results, employee_username),
            'context_proximity_scoring': self._score_context_proximity(prerequisite_data, ownership_identification_results, employee_username),
            'role_aware_assignment': self._assign_role_aware(prerequisite_data, ownership_identification_results, employee_username),
            'load_balanced_assignment': self._balance_load_with_risk(prerequisite_data, ownership_identification_results, employee_username)
        }
        
        return results
    
    def _recommend_by_capability(self, prerequisite_data: Dict[str, Any], 
                                 ownership_results: Dict[str, Any],
                                 employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 58: Capability-based successor recommendation"""
        data_collection = prerequisite_data.get('data_collection', {})
        ai_intelligence = prerequisite_data.get('ai_intelligence', {})
        
        contributors = data_collection.get('multi_repo_contribution', {}).get('contributors', {})
        roles = ai_intelligence.get('role_detection', {}).get('detected_roles', {})
        successor_requirements = ownership_results.get('successor_requirements', {}).get('successor_requirements', [])
        
        recommendations = []
        
        for requirement in successor_requirements:
            file_path = requirement.get('file', '')
            required_capabilities = requirement.get('required_capabilities', [])
            requirement_type = requirement.get('requirement_type', 'primary_successor')
            
            # Score each candidate
            candidate_scores = []
            
            for contributor_name, contributor_data in contributors.items():
                if contributor_name == employee_username:
                    continue  # Skip departing employee
                
                score = 0.0
                capability_matches = []
                
                # Check file contributions
                files_modified = contributor_data.get('files_modified', [])
                if file_path in files_modified:
                    score += 0.4
                    capability_matches.append('file_contribution')
                
                # Check technology capabilities from role
                role_data = roles.get(contributor_name, {})
                role_indicators = role_data.get('role_indicators', {})
                
                # Match capabilities
                for capability in required_capabilities:
                    if capability in ['python', 'javascript', 'java', 'go', 'rust', 'c_cpp']:
                        # Check if contributor has worked with this tech
                        tech_files = [f for f in files_modified if f'.{capability.split("_")[0]}' in f.lower()]
                        if tech_files:
                            score += 0.2
                            capability_matches.append(capability)
                    elif capability == 'devops':
                        if role_indicators.get('devops_engineer', 0) > 0:
                            score += 0.3
                            capability_matches.append('devops')
                    elif capability == 'operational_knowledge':
                        if role_indicators.get('devops_engineer', 0) > 0:
                            score += 0.3
                            capability_matches.append('operational')
                
                # Contribution activity
                total_contributions = contributor_data.get('prs', 0) + contributor_data.get('commits', 0)
                if total_contributions > 10:
                    score += 0.1
                
                if score > 0:
                    candidate_scores.append({
                        'candidate': contributor_name,
                        'score': score,
                        'capability_matches': capability_matches,
                        'total_contributions': total_contributions,
                        'files_contributed': len(files_modified),
                        'role': role_data.get('primary_role', 'contributor')
                    })
            
            # Sort by score
            candidate_scores.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Generate recommendation
            if candidate_scores:
                top_candidate = candidate_scores[0]
                recommendations.append({
                    'requirement_id': requirement.get('requirement_id', ''),
                    'file': file_path,
                    'requirement_type': requirement_type,
                    'recommended_candidate': top_candidate.get('candidate'),
                    'recommendation_score': top_candidate.get('score'),
                    'confidence': 'high' if top_candidate.get('score', 0) > 0.6 else ('medium' if top_candidate.get('score', 0) > 0.3 else 'low'),
                    'capability_matches': top_candidate.get('capability_matches', []),
                    'all_candidates': candidate_scores[:5],  # Top 5
                    'rationale': self._generate_recommendation_rationale(top_candidate, requirement)
                })
            else:
                recommendations.append({
                    'requirement_id': requirement.get('requirement_id', ''),
                    'file': file_path,
                    'requirement_type': requirement_type,
                    'recommended_candidate': None,
                    'recommendation_score': 0.0,
                    'confidence': 'none',
                    'rationale': 'No suitable candidates found based on capabilities'
                })
        
        return {
            'recommendations': recommendations,
            'total_recommendations': len(recommendations),
            'high_confidence_recommendations': [r for r in recommendations if r.get('confidence') == 'high'],
            'recommendations_by_type': self._group_recommendations_by_type(recommendations)
        }
    
    def _generate_recommendation_rationale(self, candidate: Dict[str, Any], 
                                          requirement: Dict[str, Any]) -> str:
        """Generate rationale for recommendation"""
        candidate_name = candidate.get('candidate', '')
        score = candidate.get('score', 0)
        matches = candidate.get('capability_matches', [])
        
        rationale = f"Recommended {candidate_name} (score: {score:.2f}) because: "
        
        if matches:
            rationale += f"matches capabilities: {', '.join(matches)}. "
        
        if candidate.get('files_contributed', 0) > 0:
            rationale += f"Has contributed to {candidate.get('files_contributed')} files. "
        
        if candidate.get('total_contributions', 0) > 10:
            rationale += f"Active contributor with {candidate.get('total_contributions')} contributions."
        
        return rationale
    
    def _group_recommendations_by_type(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group recommendations by type"""
        by_type = defaultdict(list)
        for rec in recommendations:
            by_type[rec.get('requirement_type', 'unknown')].append(rec)
        return dict(by_type)
    
    def _match_by_contributions(self, prerequisite_data: Dict[str, Any], 
                                ownership_results: Dict[str, Any],
                                employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 59: Past contribution-based matching"""
        data_collection = prerequisite_data.get('data_collection', {})
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        contributors = data_collection.get('multi_repo_contribution', {}).get('contributors', {})
        successor_requirements = ownership_results.get('successor_requirements', {}).get('successor_requirements', [])
        
        matches = []
        
        for requirement in successor_requirements:
            file_path = requirement.get('file', '')
            
            # Find contributors who have worked on this file
            history = ownership_history.get(file_path, [])
            file_contributors = {}
            
            for change in history:
                author = change.get('author', '')
                if author and author != employee_username:
                    if author not in file_contributors:
                        file_contributors[author] = {
                            'contribution_count': 0,
                            'first_contribution': change.get('date'),
                            'last_contribution': change.get('date')
                        }
                    file_contributors[author]['contribution_count'] += 1
                    if change.get('date'):
                        if not file_contributors[author]['first_contribution'] or change.get('date') < file_contributors[author]['first_contribution']:
                            file_contributors[author]['first_contribution'] = change.get('date')
                        if not file_contributors[author]['last_contribution'] or change.get('date') > file_contributors[author]['last_contribution']:
                            file_contributors[author]['last_contribution'] = change.get('date')
            
            # Score contributors
            contributor_scores = []
            for contributor_name, contrib_data in file_contributors.items():
                contributor_info = contributors.get(contributor_name, {})
                
                score = contrib_data['contribution_count'] * 0.5  # Contribution count weight
                
                # Recency bonus
                if contrib_data.get('last_contribution'):
                    # Simple recency check (would need date parsing in real implementation)
                    score += 0.2
                
                # Overall activity
                total_contributions = contributor_info.get('prs', 0) + contributor_info.get('commits', 0)
                if total_contributions > 5:
                    score += 0.1
                
                contributor_scores.append({
                    'candidate': contributor_name,
                    'score': score,
                    'contribution_count': contrib_data['contribution_count'],
                    'first_contribution': contrib_data.get('first_contribution'),
                    'last_contribution': contrib_data.get('last_contribution'),
                    'total_repo_contributions': total_contributions
                })
            
            contributor_scores.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            matches.append({
                'requirement_id': requirement.get('requirement_id', ''),
                'file': file_path,
                'matched_candidates': contributor_scores,
                'top_match': contributor_scores[0] if contributor_scores else None,
                'match_confidence': 'high' if contributor_scores and contributor_scores[0].get('score', 0) > 1.0 else 'medium'
            })
        
        return {
            'contribution_matches': matches,
            'total_matches': len(matches),
            'high_confidence_matches': [m for m in matches if m.get('match_confidence') == 'high'],
            'matches_with_candidates': [m for m in matches if m.get('top_match')]
        }
    
    def _score_context_proximity(self, prerequisite_data: Dict[str, Any], 
                                 ownership_results: Dict[str, Any],
                                 employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 60: Context proximity scoring"""
        data_collection = prerequisite_data.get('data_collection', {})
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        dependencies = data_collection.get('dependencies', {}).get('file_dependencies', {})
        directory_structure = data_collection.get('dependencies', {}).get('directory_structure', {})
        contributors = data_collection.get('multi_repo_contribution', {}).get('contributors', {})
        successor_requirements = ownership_results.get('successor_requirements', {}).get('successor_requirements', [])
        
        proximity_scores = {}
        
        for requirement in successor_requirements:
            file_path = requirement.get('file', '')
            
            # Get file context
            file_directory = '/'.join(file_path.split('/')[:-1]) if '/' in file_path else '.'
            file_dependencies = dependencies.get(file_path, [])
            
            # Score each candidate based on proximity
            candidate_proximity = {}
            
            for contributor_name, contributor_data in contributors.items():
                if contributor_name == employee_username:
                    continue
                
                proximity_score = 0.0
                proximity_factors = []
                
                # Factor 1: Same directory files
                files_modified = contributor_data.get('files_modified', [])
                same_dir_files = [f for f in files_modified if f.startswith(file_directory) or file_directory in f]
                if same_dir_files:
                    proximity_score += 0.3
                    proximity_factors.append(f"Works in same directory ({len(same_dir_files)} files)")
                
                # Factor 2: Dependent files
                dependent_files = [f for f in files_modified if any(dep in f for dep in file_dependencies)]
                if dependent_files:
                    proximity_score += 0.25
                    proximity_factors.append(f"Works on dependent files ({len(dependent_files)} files)")
                
                # Factor 3: Related files (same subsystem)
                # Find subsystem
                for directory, files in directory_structure.items():
                    if file_path in files:
                        subsystem_files = [f for f in files_modified if f in files]
                        if subsystem_files:
                            proximity_score += 0.2
                            proximity_factors.append(f"Works in same subsystem ({len(subsystem_files)} files)")
                        break
                
                # Factor 4: Direct file contribution
                if file_path in files_modified:
                    proximity_score += 0.25
                    proximity_factors.append('Direct file contribution')
                
                if proximity_score > 0:
                    candidate_proximity[contributor_name] = {
                        'candidate': contributor_name,
                        'proximity_score': proximity_score,
                        'proximity_level': 'high' if proximity_score > 0.5 else ('medium' if proximity_score > 0.3 else 'low'),
                        'proximity_factors': proximity_factors
                    }
            
            # Sort by proximity
            sorted_proximity = sorted(candidate_proximity.values(), key=lambda x: x.get('proximity_score', 0), reverse=True)
            
            proximity_scores[requirement.get('requirement_id', '')] = {
                'requirement_id': requirement.get('requirement_id', ''),
                'file': file_path,
                'candidate_proximity': sorted_proximity,
                'top_proximity_candidate': sorted_proximity[0] if sorted_proximity else None
            }
        
        return {
            'proximity_scores': proximity_scores,
            'total_requirements_scored': len(proximity_scores),
            'high_proximity_candidates': sum(
                1 for req_data in proximity_scores.values()
                if req_data.get('top_proximity_candidate') and 
                req_data.get('top_proximity_candidate').get('proximity_level') == 'high'
            )
        }
    
    def _assign_role_aware(self, prerequisite_data: Dict[str, Any], 
                         ownership_results: Dict[str, Any],
                         employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 61: Role-aware but capability-first assignment"""
        data_collection = prerequisite_data.get('data_collection', {})
        ai_intelligence = prerequisite_data.get('ai_intelligence', {})
        
        roles = ai_intelligence.get('role_detection', {}).get('detected_roles', {})
        capability_recommendations = self._recommend_by_capability(prerequisite_data, ownership_results, employee_username)
        recommendations = capability_recommendations.get('recommendations', [])
        
        role_aware_assignments = []
        
        for recommendation in recommendations:
            file_path = recommendation.get('file', '')
            candidate = recommendation.get('recommended_candidate')
            requirement_type = recommendation.get('requirement_type', '')
            
            if not candidate:
                continue
            
            # Get candidate role
            candidate_role = roles.get(candidate, {}).get('primary_role', 'contributor')
            
            # Determine if role is appropriate
            role_appropriate = True
            role_notes = []
            
            # Check role appropriateness based on requirement type
            if requirement_type == 'operational_successor':
                if candidate_role not in ['devops_engineer', 'maintainer']:
                    role_appropriate = False
                    role_notes.append(f"Role {candidate_role} may not be ideal for operational responsibilities")
                else:
                    role_notes.append(f"Role {candidate_role} is appropriate for operational work")
            
            elif 'backend' in file_path.lower() or any(ext in file_path for ext in ['.py', '.java', '.go']):
                if candidate_role in ['frontend_developer']:
                    role_appropriate = False
                    role_notes.append(f"Role {candidate_role} may not match backend file requirements")
            
            elif 'frontend' in file_path.lower() or any(ext in file_path for ext in ['.js', '.ts', '.jsx', '.tsx']):
                if candidate_role in ['backend_developer']:
                    role_appropriate = False
                    role_notes.append(f"Role {candidate_role} may not match frontend file requirements")
            
            # Capability-first: if capabilities match, role is secondary
            capability_score = recommendation.get('recommendation_score', 0)
            if capability_score > 0.5:
                role_notes.append("High capability match - role consideration secondary")
            
            role_aware_assignments.append({
                'requirement_id': recommendation.get('requirement_id', ''),
                'file': file_path,
                'assigned_candidate': candidate,
                'candidate_role': candidate_role,
                'capability_score': capability_score,
                'role_appropriate': role_appropriate,
                'role_notes': role_notes,
                'assignment_confidence': 'high' if capability_score > 0.5 and role_appropriate else ('medium' if capability_score > 0.3 else 'low'),
                'rationale': f"Assigned {candidate} ({candidate_role}) based on capabilities (score: {capability_score:.2f}). " + ' '.join(role_notes)
            })
        
        return {
            'role_aware_assignments': role_aware_assignments,
            'total_assignments': len(role_aware_assignments),
            'high_confidence_assignments': [a for a in role_aware_assignments if a.get('assignment_confidence') == 'high'],
            'role_appropriate_assignments': [a for a in role_aware_assignments if a.get('role_appropriate')],
            'assignments_by_role': self._group_assignments_by_role(role_aware_assignments)
        }
    
    def _group_assignments_by_role(self, assignments: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group assignments by candidate role"""
        by_role = defaultdict(list)
        for assignment in assignments:
            role = assignment.get('candidate_role', 'unknown')
            by_role[role].append(assignment)
        return dict(by_role)
    
    def _balance_load_with_risk(self, prerequisite_data: Dict[str, Any], 
                                ownership_results: Dict[str, Any],
                                employee_username: Optional[str]) -> Dict[str, Any]:
        """Feature 62: Load-balanced assignment with risk override"""
        role_aware_assignments = self._assign_role_aware(prerequisite_data, ownership_results, employee_username)
        assignments = role_aware_assignments.get('role_aware_assignments', [])
        ownership_risks = ownership_results.get('ownership_risk_scoring', {}).get('ownership_risks', {})
        
        # Count current assignments per candidate
        candidate_load = defaultdict(int)
        candidate_risk_load = defaultdict(float)
        
        for assignment in assignments:
            candidate = assignment.get('assigned_candidate')
            if candidate:
                candidate_load[candidate] += 1
                file_path = assignment.get('file', '')
                risk_data = ownership_risks.get(file_path, {})
                risk_score = risk_data.get('ownership_risk_score', 0)
                candidate_risk_load[candidate] += risk_score
        
        # Rebalance if needed (risk override: critical files always assigned)
        balanced_assignments = []
        
        for assignment in assignments:
            candidate = assignment.get('assigned_candidate')
            file_path = assignment.get('file', '')
            risk_data = ownership_risks.get(file_path, {})
            risk_level = risk_data.get('ownership_risk_level', 'low')
            
            # Risk override: critical/high risk files must be assigned
            if risk_level in ['critical', 'high']:
                # Keep assignment even if load is high
                balanced_assignments.append({
                    **assignment,
                    'load_balanced': False,
                    'risk_override': True,
                    'rationale': f"Risk override: {risk_level} risk file must be assigned"
                })
            else:
                # Check if candidate is overloaded
                current_load = candidate_load.get(candidate, 0)
                risk_load = candidate_risk_load.get(candidate, 0)
                
                if current_load > 5 or risk_load > 3.0:  # Thresholds
                    # Consider reassignment (in real implementation, would find alternative)
                    balanced_assignments.append({
                        **assignment,
                        'load_balanced': False,
                        'risk_override': False,
                        'load_warning': True,
                        'current_load': current_load,
                        'risk_load': risk_load,
                        'rationale': f"Candidate has high load ({current_load} files, {risk_load:.2f} risk score)"
                    })
                else:
                    balanced_assignments.append({
                        **assignment,
                        'load_balanced': True,
                        'risk_override': False,
                        'current_load': current_load,
                        'risk_load': risk_load
                    })
        
        # Calculate load distribution
        final_load = defaultdict(int)
        for assignment in balanced_assignments:
            candidate = assignment.get('assigned_candidate')
            if candidate:
                final_load[candidate] += 1
        
        return {
            'balanced_assignments': balanced_assignments,
            'load_distribution': dict(final_load),
            'load_statistics': {
                'total_assignments': len(balanced_assignments),
                'average_load': sum(final_load.values()) / len(final_load) if final_load else 0,
                'max_load': max(final_load.values()) if final_load else 0,
                'min_load': min(final_load.values()) if final_load else 0,
                'overloaded_candidates': [c for c, load in final_load.items() if load > 5]
            },
            'risk_overrides': [a for a in balanced_assignments if a.get('risk_override')],
            'load_warnings': [a for a in balanced_assignments if a.get('load_warning')]
        }

