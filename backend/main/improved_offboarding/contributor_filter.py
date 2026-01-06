"""
Contributor Data Filter
Filters all analysis data to focus only on a specific contributor's work
"""

from typing import Dict, Any, List, Optional, Set


class ContributorDataFilter:
    """
    Filters repository and analysis data to focus on a specific contributor
    """
    
    def __init__(self, employee_username: str):
        """
        Initialize filter for a specific employee
        
        Args:
            employee_username: Username of the contributor to filter for
        """
        self.employee_username = employee_username
        self.employee_files: Set[str] = set()
        self.employee_prs: List[Dict[str, Any]] = []
        self.employee_commits: List[Dict[str, Any]] = []
    
    def filter_prerequisite_data(self, prerequisite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter prerequisite data to only include the contributor's work
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            
        Returns:
            Filtered prerequisite data focused on the contributor
        """
        data_collection = prerequisite_data.get('data_collection', {})
        
        # Get contributor's files from multi_repo_contribution
        contributors = data_collection.get('multi_repo_contribution', {}).get('contributors', {})
        contributor_data = contributors.get(self.employee_username, {})
        
        # Get files owned/modified by this contributor
        self.employee_files = set(contributor_data.get('files_modified', []))
        
        # Get file ownership history
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        current_owners = data_collection.get('file_ownership_history', {}).get('current_owners', {})
        
        # Add files currently owned by this contributor
        for file_path, owner in current_owners.items():
            if owner == self.employee_username:
                self.employee_files.add(file_path)
        
        # Add files from ownership history
        for file_path, history in ownership_history.items():
            for entry in history:
                if entry.get('author') == self.employee_username:
                    self.employee_files.add(file_path)
        
        # Create filtered data structure
        filtered_data = {
            'metadata': prerequisite_data.get('metadata', {}),
            'data_collection': self._filter_data_collection(data_collection),
            'risk_analysis': self._filter_risk_analysis(prerequisite_data.get('risk_analysis', {})),
            'ai_intelligence': self._filter_ai_intelligence(prerequisite_data.get('ai_intelligence', {})),
            'contributor_info': {
                'username': self.employee_username,
                'files_owned': list(self.employee_files),
                'total_files': len(self.employee_files),
                'prs': contributor_data.get('prs', 0),
                'commits': contributor_data.get('commits', 0),
                'files_modified_count': contributor_data.get('files_modified_count', 0),
                'first_contribution': contributor_data.get('first_contribution'),
                'last_contribution': contributor_data.get('last_contribution')
            }
        }
        
        return filtered_data
    
    def _filter_data_collection(self, data_collection: Dict[str, Any]) -> Dict[str, Any]:
        """Filter data collection to contributor's files"""
        filtered = {}
        
        # Filter file ownership history
        ownership_history = data_collection.get('file_ownership_history', {}).get('ownership_history', {})
        filtered_ownership = {}
        filtered_current_owners = {}
        
        for file_path in self.employee_files:
            if file_path in ownership_history:
                filtered_ownership[file_path] = ownership_history[file_path]
            
            current_owners = data_collection.get('file_ownership_history', {}).get('current_owners', {})
            if file_path in current_owners:
                filtered_current_owners[file_path] = current_owners[file_path]
        
        filtered['file_ownership_history'] = {
            'ownership_history': filtered_ownership,
            'current_owners': filtered_current_owners,
            'total_files_tracked': len(filtered_ownership)
        }
        
        # Filter file activity
        file_activity = data_collection.get('file_activity', {})
        filtered_file_activity = {}
        for file_path in self.employee_files:
            if file_path in file_activity:
                filtered_file_activity[file_path] = file_activity[file_path]
        
        filtered['file_activity'] = filtered_file_activity
        filtered['total_files'] = len(filtered_file_activity)
        
        # Filter change frequency
        change_frequency = data_collection.get('change_frequency', {})
        file_churn = change_frequency.get('file_churn', {})
        filtered_churn = {}
        for file_path in self.employee_files:
            if file_path in file_churn:
                filtered_churn[file_path] = file_churn[file_path]
        
        filtered['change_frequency'] = {
            'file_churn': filtered_churn,
            'high_churn_files': [f for f in change_frequency.get('high_churn_files', []) if f in self.employee_files],
            'total_files_with_changes': len(filtered_churn)
        }
        
        # Keep contributor info (only this contributor)
        contributors = data_collection.get('multi_repo_contribution', {}).get('contributors', {})
        filtered['multi_repo_contribution'] = {
            'total_contributors': 1,
            'contributors': {
                self.employee_username: contributors.get(self.employee_username, {})
            }
        }
        
        # Filter critical subsystems
        critical_subsystems = data_collection.get('critical_subsystems', {}).get('critical_subsystems', [])
        filtered_subsystems = [
            cs for cs in critical_subsystems 
            if any(f in self.employee_files for f in cs.get('files', []))
        ]
        
        filtered['critical_subsystems'] = {
            'critical_subsystems': filtered_subsystems,
            'total_subsystems': len(filtered_subsystems)
        }
        
        # Keep other data as-is (PR activity, commit timeline, etc.)
        filtered['pr_activity'] = data_collection.get('pr_activity', {})
        filtered['commit_timeline'] = data_collection.get('commit_timeline', {})
        filtered['dependencies'] = data_collection.get('dependencies', {})
        
        return filtered
    
    def _filter_risk_analysis(self, risk_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Filter risk analysis to contributor's files"""
        filtered = {}
        
        # Filter knowledge loss risk
        knowledge_loss_risk = risk_analysis.get('knowledge_loss_risk', {})
        file_risk_scores = knowledge_loss_risk.get('file_risk_scores', {})
        filtered_risk_scores = {
            f: score for f, score in file_risk_scores.items() 
            if f in self.employee_files
        }
        filtered_high_risk = [
            f for f in knowledge_loss_risk.get('high_risk_files', [])
            if f in self.employee_files
        ]
        
        filtered['knowledge_loss_risk'] = {
            'file_risk_scores': filtered_risk_scores,
            'high_risk_files': filtered_high_risk,
            'total_high_risk': len(filtered_high_risk)
        }
        
        # Filter single owner detection
        single_owners = risk_analysis.get('single_owner_detection', {}).get('single_owner_files', [])
        filtered_single_owners = [
            so for so in single_owners 
            if so.get('file') in self.employee_files and so.get('owner') == self.employee_username
        ]
        
        filtered['single_owner_detection'] = {
            'single_owner_files': filtered_single_owners,
            'total_single_owner_files': len(filtered_single_owners)
        }
        
        # Filter bus factor
        bus_factor = risk_analysis.get('bus_factor_analysis', {}).get('bus_factors', {})
        filtered_bus_factor = {
            f: bf for f, bf in bus_factor.items()
            if f in self.employee_files
        }
        
        avg_bus_factor = sum(bf.get('bus_factor', 0) for bf in filtered_bus_factor.values()) / len(filtered_bus_factor) if filtered_bus_factor else 0
        
        filtered['bus_factor_analysis'] = {
            'bus_factors': filtered_bus_factor,
            'average_bus_factor': avg_bus_factor,
            'high_risk_files': [f for f, bf in filtered_bus_factor.items() if bf.get('risk_level') == 'high']
        }
        
        # Filter knowledge hotspots
        hotspots = risk_analysis.get('knowledge_hotspots', {}).get('knowledge_hotspots', [])
        filtered_hotspots = [
            h for h in hotspots
            if h.get('file') in self.employee_files
        ]
        
        filtered['knowledge_hotspots'] = {
            'knowledge_hotspots': filtered_hotspots,
            'total_hotspots': len(filtered_hotspots)
        }
        
        # Filter operational ownership
        operational = risk_analysis.get('operational_ownership', {}).get('operational_files', [])
        filtered_operational = [
            op for op in operational
            if op.get('file') in self.employee_files and op.get('current_owner') == self.employee_username
        ]
        
        filtered['operational_ownership'] = {
            'operational_files': filtered_operational,
            'total_operational_files': len(filtered_operational)
        }
        
        # Filter criticality scoring
        criticality = risk_analysis.get('criticality_scoring', {}).get('critical_files', [])
        filtered_criticality = [
            c for c in criticality
            if c.get('file') in self.employee_files
        ]
        
        filtered['criticality_scoring'] = {
            'critical_files': filtered_criticality,
            'critical_files_count': len(filtered_criticality)
        }
        
        # Keep other risk analysis data
        filtered['cross_module_impact'] = risk_analysis.get('cross_module_impact', {})
        filtered['hidden_dependencies'] = risk_analysis.get('hidden_dependencies', {})
        filtered['on_call_responsibility'] = risk_analysis.get('on_call_responsibility', {})
        
        return filtered
    
    def _filter_ai_intelligence(self, ai_intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Filter AI intelligence to contributor's files"""
        filtered = {}
        
        # Filter knowledge units
        knowledge_units = ai_intelligence.get('knowledge_unit_identification', {}).get('knowledge_units', {})
        filtered_units = {}
        for unit_type, units in knowledge_units.items():
            filtered_units[unit_type] = [
                u for u in units
                if any(f in self.employee_files for f in u.get('files', []))
            ]
        
        filtered['knowledge_unit_identification'] = {
            'knowledge_units': filtered_units,
            'total_systems': len(filtered_units.get('systems', [])),
            'total_modules': len(filtered_units.get('modules', [])),
            'total_features': len(filtered_units.get('features', []))
        }
        
        # Filter role detection (only this contributor)
        role_detection = ai_intelligence.get('role_detection', {})
        detected_roles = role_detection.get('detected_roles', {})
        filtered_roles = {
            self.employee_username: detected_roles.get(self.employee_username, {})
        } if self.employee_username in detected_roles else {}
        
        filtered['role_detection'] = {
            'detected_roles': filtered_roles,
            'total_contributors_analyzed': 1 if filtered_roles else 0
        }
        
        # Keep other AI intelligence data
        filtered['semantic_pr_clustering'] = ai_intelligence.get('semantic_pr_clustering', {})
        filtered['knowledge_gap_detection'] = ai_intelligence.get('knowledge_gap_detection', {})
        
        return filtered
    
    def get_contributor_context(self, prerequisite_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive context about the contributor for AI prompts
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            
        Returns:
            Dictionary with contributor-specific context
        """
        data_collection = prerequisite_data.get('data_collection', {})
        risk_analysis = prerequisite_data.get('risk_analysis', {})
        contributors = data_collection.get('multi_repo_contribution', {}).get('contributors', {})
        contributor_data = contributors.get(self.employee_username, {})
        
        # Get files owned
        current_owners = data_collection.get('file_ownership_history', {}).get('current_owners', {})
        owned_files = [f for f, owner in current_owners.items() if owner == self.employee_username]
        
        # Get high-risk files owned
        knowledge_loss_risk = risk_analysis.get('knowledge_loss_risk', {})
        high_risk_files = knowledge_loss_risk.get('high_risk_files', [])
        owned_high_risk = [f for f in high_risk_files if f in owned_files]
        
        # Get single-owner files
        single_owners = risk_analysis.get('single_owner_detection', {}).get('single_owner_files', [])
        owned_single_owner = [so.get('file') for so in single_owners if so.get('owner') == self.employee_username]
        
        # Get operational files
        operational = risk_analysis.get('operational_ownership', {}).get('operational_files', [])
        owned_operational = [op.get('file') for op in operational if op.get('current_owner') == self.employee_username]
        
        return {
            'username': self.employee_username,
            'contribution_stats': {
                'prs': contributor_data.get('prs', 0),
                'commits': contributor_data.get('commits', 0),
                'files_modified': contributor_data.get('files_modified_count', 0),
                'files_list': contributor_data.get('files_modified', [])
            },
            'ownership': {
                'total_files_owned': len(owned_files),
                'owned_files': owned_files,
                'high_risk_files_owned': owned_high_risk,
                'single_owner_files_owned': owned_single_owner,
                'operational_files_owned': owned_operational
            },
            'timeline': {
                'first_contribution': contributor_data.get('first_contribution'),
                'last_contribution': contributor_data.get('last_contribution')
            },
            'risk_summary': {
                'high_risk_count': len(owned_high_risk),
                'single_owner_count': len(owned_single_owner),
                'operational_count': len(owned_operational)
            }
        }

