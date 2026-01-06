"""
Main Processor for Handover Module
Orchestrates all Handover features (53-73)
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .ownership_identification import OwnershipIdentifier
from .smart_assignment import SmartAssignmentProcessor
from .knowledge_transfer_planning import KnowledgeTransferPlanner
from .execution_validation import ExecutionValidator


class HandoverProcessor:
    """
    Main processor for Handover features (53-73)
    """
    
    def __init__(self, output_dir: str = "backend/data/improved_offboarding/handover"):
        """
        Initialize the Handover processor
        
        Args:
            output_dir: Directory to save output JSON files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.ownership_identifier = OwnershipIdentifier()
        self.assignment_processor = SmartAssignmentProcessor()
        self.kt_planner = KnowledgeTransferPlanner()
        self.execution_validator = ExecutionValidator()
    
    def process(self, prerequisite_data: Dict[str, Any], 
                final_call_data: Optional[Dict[str, Any]] = None,
                employee_username: Optional[str] = None,
                contributor_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process Handover features for a departing employee
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            final_call_data: Final Call results (optional)
            employee_username: Username of departing employee (optional)
            
        Returns:
            Complete Handover analysis results
        """
        print(f"\n{'='*80}")
        print(f"Processing Handover Features (53-73)")
        if employee_username:
            print(f"Employee: {employee_username}")
        print(f"{'='*80}\n")
        
        # Step 1: Ownership Identification (Features 53-57)
        print("🔍 Step 1/4: Identifying ownership gaps and requirements (53-57)...")
        ownership_results = self.ownership_identifier.process(prerequisite_data, final_call_data, employee_username)
        print(f"   ✓ Ownership identification completed")
        print(f"   - Ownership gaps: {ownership_results['ownership_gaps']['total_gaps']}")
        print(f"   - Successor requirements: {ownership_results['successor_requirements']['total_requirements']}")
        print(f"   - Critical risk files: {len(ownership_results['ownership_risk_scoring']['critical_risk_files'])}")
        
        # Step 2: Smart Assignment (Features 58-62)
        print("\n👥 Step 2/4: Processing smart assignment (58-62)...")
        assignment_results = self.assignment_processor.process(
            prerequisite_data,
            ownership_results,
            employee_username
        )
        print(f"   ✓ Smart assignment completed")
        assignments = assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])
        print(f"   - Total assignments: {len(assignments)}")
        print(f"   - High confidence: {len(assignment_results.get('role_aware_assignment', {}).get('high_confidence_assignments', []))}")
        
        # Step 3: Knowledge Transfer Planning (Features 63-67)
        print("\n📚 Step 3/4: Planning knowledge transfer (63-67)...")
        kt_planning_results = self.kt_planner.process(
            prerequisite_data,
            ownership_results,
            assignment_results,
            final_call_data,
            employee_username
        )
        print(f"   ✓ Knowledge transfer planning completed")
        agenda = kt_planning_results.get('handover_agenda', {})
        print(f"   - Handover agenda items: {agenda.get('total_agenda_items', 0)}")
        print(f"   - Estimated KT hours: {kt_planning_results.get('kt_time_estimation', {}).get('total_kt_hours', 0):.1f}")
        
        # Step 4: Execution & Validation (Features 68-73)
        print("\n✅ Step 4/4: Setting up execution tracking (68-73)...")
        execution_results = self.execution_validator.process(
            ownership_results,
            assignment_results,
            kt_planning_results,
            employee_username
        )
        print(f"   ✓ Execution tracking completed")
        print(f"   - Acceptance workflows: {execution_results.get('ownership_acceptance_workflow', {}).get('total_workflows', 0)}")
        print(f"   - SLA tracking items: {execution_results.get('sla_due_date_tracking', {}).get('total_sla_items', 0)}")
        
        # Combine all results
        complete_results = {
            'metadata': {
                'employee_username': employee_username,
                'processed_at': datetime.now().isoformat(),
                'processor_version': '1.0.0',
                'features_implemented': list(range(53, 74))
            },
            'ownership_identification': ownership_results,
            'smart_assignment': assignment_results,
            'knowledge_transfer_planning': kt_planning_results,
            'execution_validation': execution_results,
            'summary': self._generate_summary(ownership_results, assignment_results, kt_planning_results, execution_results)
        }
        
        return complete_results
    
    def _generate_summary(self, ownership_results: Dict[str, Any], 
                         assignment_results: Dict[str, Any],
                         kt_planning_results: Dict[str, Any],
                         execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        return {
            'ownership_summary': {
                'total_gaps': ownership_results.get('ownership_gaps', {}).get('total_gaps', 0),
                'successor_requirements': ownership_results.get('successor_requirements', {}).get('total_requirements', 0),
                'critical_risk_files': len(ownership_results.get('ownership_risk_scoring', {}).get('critical_risk_files', [])),
                'backup_requirements': ownership_results.get('backup_owner_requirements', {}).get('total_backup_requirements', 0)
            },
            'assignment_summary': {
                'total_assignments': len(assignment_results.get('load_balanced_assignment', {}).get('balanced_assignments', [])),
                'high_confidence_assignments': len(assignment_results.get('role_aware_assignment', {}).get('high_confidence_assignments', [])),
                'unique_candidates': len(assignment_results.get('load_balanced_assignment', {}).get('load_distribution', {}))
            },
            'kt_planning_summary': {
                'total_kt_sessions': kt_planning_results.get('kt_type_recommendations', {}).get('total_kt_sessions', 0),
                'total_kt_hours': kt_planning_results.get('kt_time_estimation', {}).get('total_kt_hours', 0),
                'agenda_items': kt_planning_results.get('handover_agenda', {}).get('total_agenda_items', 0),
                'required_artifacts': kt_planning_results.get('expected_artifacts', {}).get('total_artifacts_required', 0)
            },
            'execution_summary': {
                'acceptance_workflows': execution_results.get('ownership_acceptance_workflow', {}).get('total_workflows', 0),
                'kt_completion_items': execution_results.get('kt_completion_tracking', {}).get('total_kt_items', 0),
                'sla_tracking_items': execution_results.get('sla_due_date_tracking', {}).get('total_sla_items', 0),
                'approval_workflows': execution_results.get('manager_approval_flow', {}).get('total_workflows', 0)
            }
        }
    
    def save_results(self, results: Dict[str, Any], 
                    owner: str, repo: str, 
                    employee_username: Optional[str] = None) -> Path:
        """
        Save Handover results to JSON file
        
        Args:
            results: Complete Handover results
            owner: Repository owner
            repo: Repository name
            employee_username: Employee username (optional)
            
        Returns:
            Path to saved file
        """
        def convert_to_serializable(obj):
            """Convert objects to JSON-serializable format"""
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, set):
                return list(obj)
            elif hasattr(obj, '__dict__'):
                return convert_to_serializable(obj.__dict__)
            else:
                return obj
        
        # Generate filename
        if employee_username:
            filename = f"{owner}_{repo}_{employee_username}_handover.json"
        else:
            filename = f"{owner}_{repo}_handover.json"
        
        output_file = self.output_dir / filename
        
        serializable_results = convert_to_serializable(results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to {output_file}")
        
        return output_file

