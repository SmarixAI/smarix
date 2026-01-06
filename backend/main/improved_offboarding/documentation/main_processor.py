"""
Main Processor for Documentation Module
Orchestrates all Documentation features (74-89)
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .documentation_detection import DocumentationDetector
from .ai_assisted_creation import AIAssistedCreator
from .management_quality import ManagementQualityProcessor


class DocumentationProcessor:
    """
    Main processor for Documentation features (74-89)
    """
    
    def __init__(self, output_dir: str = "backend/data/improved_offboarding/documentation"):
        """
        Initialize the Documentation processor
        
        Args:
            output_dir: Directory to save output JSON files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.detector = DocumentationDetector()
        self.creator = AIAssistedCreator()
        self.manager = ManagementQualityProcessor()
    
    def process(self, prerequisite_data: Dict[str, Any],
                final_call_data: Optional[Dict[str, Any]] = None,
                handover_data: Optional[Dict[str, Any]] = None,
                employee_username: Optional[str] = None,
                contributor_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process Documentation features
        
        Args:
            prerequisite_data: Complete prerequisite analysis results
            final_call_data: Final Call results (optional)
            handover_data: Handover results (optional)
            employee_username: Username of departing employee (optional)
            
        Returns:
            Complete Documentation analysis results
        """
        print(f"\n{'='*80}")
        print(f"Processing Documentation Features (74-89)")
        if employee_username:
            print(f"Employee: {employee_username}")
        print(f"{'='*80}\n")
        
        # Step 1: Documentation Detection (Features 74-78)
        print("🔍 Step 1/3: Detecting documentation gaps and requirements (74-78)...")
        detection_results = self.detector.process(prerequisite_data, final_call_data, handover_data, employee_username)
        print(f"   ✓ Documentation detection completed")
        print(f"   - Documentation gaps: {detection_results['documentation_gaps']['total_gaps']}")
        print(f"   - Required doc types: {len(detection_results['required_documentation_types']['required_types'])}")
        print(f"   - Existing docs: {detection_results['existing_documentation']['total_docs']}")
        
        # Step 2: AI-Assisted Creation (Features 79-83)
        print("\n🤖 Step 2/3: Generating AI-assisted documentation (79-83)...")
        creation_results = self.creator.process(
            prerequisite_data,
            detection_results,
            final_call_data,
            handover_data,
            employee_username
        )
        print(f"   ✓ AI-assisted creation completed")
        print(f"   - Documentation outlines: {creation_results['documentation_outlines']['total_outlines']}")
        print(f"   - Content drafts: {creation_results['content_drafting']['total_drafts']}")
        print(f"   - Diagram suggestions: {creation_results['diagram_suggestions']['total_diagrams_suggested']}")
        
        # Step 3: Management & Quality (Features 84-89)
        print("\n📋 Step 3/3: Setting up management and quality tracking (84-89)...")
        management_results = self.manager.process(
            detection_results,
            creation_results,
            handover_data,
            employee_username
        )
        print(f"   ✓ Management and quality tracking completed")
        print(f"   - Ownership assignments: {management_results['documentation_ownership']['total_assignments']}")
        print(f"   - Status tracking items: {management_results['documentation_status_tracking']['total_items']}")
        print(f"   - Review workflows: {management_results['review_approval_workflow']['total_workflows']}")
        
        # Combine all results
        complete_results = {
            'metadata': {
                'employee_username': employee_username,
                'processed_at': datetime.now().isoformat(),
                'processor_version': '1.0.0',
                'features_implemented': list(range(74, 90))
            },
            'documentation_detection': detection_results,
            'ai_assisted_creation': creation_results,
            'management_quality': management_results,
            'summary': self._generate_summary(detection_results, creation_results, management_results)
        }
        
        return complete_results
    
    def _generate_summary(self, detection_results: Dict[str, Any], 
                         creation_results: Dict[str, Any],
                         management_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        return {
            'detection_summary': {
                'total_gaps': detection_results.get('documentation_gaps', {}).get('total_gaps', 0),
                'critical_gaps': len(detection_results.get('documentation_gaps', {}).get('critical_gaps', [])),
                'existing_docs': detection_results.get('existing_documentation', {}).get('total_docs', 0),
                'duplicate_docs': detection_results.get('duplicate_documentation', {}).get('total_duplicates', 0)
            },
            'creation_summary': {
                'outlines_created': creation_results.get('documentation_outlines', {}).get('total_outlines', 0),
                'content_drafts': creation_results.get('content_drafting', {}).get('total_drafts', 0),
                'diagrams_suggested': creation_results.get('diagram_suggestions', {}).get('total_diagrams_suggested', 0),
                'code_mappings': creation_results.get('code_to_doc_mapping', {}).get('total_mappings', 0)
            },
            'management_summary': {
                'ownership_assignments': management_results.get('documentation_ownership', {}).get('total_assignments', 0),
                'status_tracking_items': management_results.get('documentation_status_tracking', {}).get('total_items', 0),
                'review_workflows': management_results.get('review_approval_workflow', {}).get('total_workflows', 0),
                'followup_suggestions': management_results.get('ai_followup_suggestions', {}).get('total_suggestions', 0)
            }
        }
    
    def save_results(self, results: Dict[str, Any], 
                    owner: str, repo: str, 
                    employee_username: Optional[str] = None) -> Path:
        """
        Save Documentation results to JSON file
        
        Args:
            results: Complete Documentation results
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
            filename = f"{owner}_{repo}_{employee_username}_documentation.json"
        else:
            filename = f"{owner}_{repo}_documentation.json"
        
        output_file = self.output_dir / filename
        
        serializable_results = convert_to_serializable(results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to {output_file}")
        
        return output_file

