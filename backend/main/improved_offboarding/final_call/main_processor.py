"""
Main Processor for Final Call Module
Orchestrates all Final Call features (31-52)
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .topic_identification import FinalCallTopicIdentifier
from .ai_guided_discussion import AIGuidedDiscussionGenerator
from .execution_tracking import ExecutionTracker


class FinalCallProcessor:
    """
    Main processor for Final Call features (31-52)
    """
    
    def __init__(self, output_dir: str = "backend/data/improved_offboarding/final_call"):
        """
        Initialize the Final Call processor
        
        Args:
            output_dir: Directory to save output JSON files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.topic_identifier = FinalCallTopicIdentifier()
        self.discussion_generator = AIGuidedDiscussionGenerator()
        self.execution_tracker = ExecutionTracker()
    
    def process(self, prerequisite_data: Dict[str, Any], 
                employee_username: Optional[str] = None,
                contributor_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process Final Call features for a departing employee
        
        Args:
            prerequisite_data: Complete prerequisite analysis results (filtered to contributor)
            employee_username: Username of departing employee (optional)
            contributor_context: Contributor-specific context for AI prompts (optional)
            
        Returns:
            Complete Final Call analysis results
        """
        print(f"\n{'='*80}")
        print(f"Processing Final Call Features (31-52)")
        if employee_username:
            print(f"Employee: {employee_username}")
            if contributor_context:
                owned_files = contributor_context.get('ownership', {}).get('total_files_owned', 0)
                print(f"Focus: {owned_files} files owned by this contributor")
        print(f"{'='*80}\n")
        
        # Step 1: Topic Identification (Features 31-38)
        print("📋 Step 1/3: Identifying Final Call topics (31-38)...")
        topic_results = self.topic_identifier.process(prerequisite_data, employee_username)
        print(f"   ✓ Identified {topic_results['final_call_topics']['total_topics']} topics")
        print(f"   - Critical topics: {len(topic_results['final_call_topics']['critical_topics'])}")
        print(f"   - High-risk files: {topic_results['high_risk_prioritization']['total_high_risk']}")
        
        # Step 2: AI-Guided Discussion (Features 39-45)
        print("\n🤖 Step 2/3: Generating AI-guided discussion materials (39-45)...")
        # Pass contributor context for AI prompts
        discussion_results = self.discussion_generator.process(
            topic_results, 
            prerequisite_data, 
            employee_username,
            contributor_context
        )
        agenda = discussion_results.get('final_call_agenda', {})
        print(f"   ✓ Generated Final Call agenda")
        print(f"   - Agenda items: {agenda.get('total_items', 0)}")
        print(f"   - Estimated time: {agenda.get('total_estimated_time_hours', 0)} hours")
        print(f"   - Questions generated: {discussion_results.get('questions_per_topic', {}).get('total_questions', 0)}")
        print(f"   - Stakeholders: {discussion_results.get('stakeholder_suggestions', {}).get('total_unique_stakeholders', 0)}")
        
        # Step 3: Execution & Tracking (Features 46-52)
        print("\n✅ Step 3/3: Setting up execution tracking (46-52)...")
        execution_results = self.execution_tracker.process(
            topic_results,
            discussion_results,
            employee_username
        )
        print(f"   ✓ Created execution tracking")
        print(f"   - Tasks grouped: {execution_results.get('task_grouping', {}).get('total_tasks', 0)}")
        print(f"   - Checklists created: {len(execution_results.get('completion_checklists', {}).get('checklists_by_topic', {}))}")
        print(f"   - Validation items: {execution_results.get('knowledge_validation_checklist', {}).get('validation_summary', {}).get('total_validation_items', 0)}")
        
        # Combine all results
        complete_results = {
            'metadata': {
                'employee_username': employee_username,
                'processed_at': datetime.now().isoformat(),
                'processor_version': '1.0.0',
                'features_implemented': list(range(31, 53))
            },
            'topic_identification': topic_results,
            'ai_guided_discussion': discussion_results,
            'execution_tracking': execution_results,
            'summary': self._generate_summary(topic_results, discussion_results, execution_results)
        }
        
        return complete_results
    
    def _generate_summary(self, topic_results: Dict[str, Any], 
                         discussion_results: Dict[str, Any],
                         execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        return {
            'topic_identification_summary': {
                'total_topics': topic_results.get('final_call_topics', {}).get('total_topics', 0),
                'critical_topics': len(topic_results.get('final_call_topics', {}).get('critical_topics', [])),
                'high_risk_files': topic_results.get('high_risk_prioritization', {}).get('total_high_risk', 0),
                'knowledge_units_needing_explanation': topic_results.get('knowledge_units_requiring_explanation', {}).get('total_units_needing_explanation', 0),
                'implicit_knowledge_items': topic_results.get('implicit_knowledge', {}).get('total_implicit_knowledge', 0)
            },
            'discussion_summary': {
                'agenda_items': discussion_results.get('final_call_agenda', {}).get('total_items', 0),
                'estimated_time_hours': discussion_results.get('final_call_agenda', {}).get('total_estimated_time_hours', 0),
                'total_questions': discussion_results.get('questions_per_topic', {}).get('total_questions', 0),
                'stakeholders': discussion_results.get('stakeholder_suggestions', {}).get('total_unique_stakeholders', 0)
            },
            'execution_summary': {
                'total_tasks': execution_results.get('task_grouping', {}).get('total_tasks', 0),
                'checklists_created': len(execution_results.get('completion_checklists', {}).get('checklists_by_topic', {})),
                'validation_items': execution_results.get('knowledge_validation_checklist', {}).get('validation_summary', {}).get('total_validation_items', 0),
                'topics_requiring_approval': execution_results.get('manager_approval_workflow', {}).get('total_topics_requiring_approval', 0)
            }
        }
    
    def save_results(self, results: Dict[str, Any], 
                    owner: str, repo: str, 
                    employee_username: Optional[str] = None) -> Path:
        """
        Save Final Call results to JSON file
        
        Args:
            results: Complete Final Call results
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
            filename = f"{owner}_{repo}_{employee_username}_final_call.json"
        else:
            filename = f"{owner}_{repo}_final_call.json"
        
        output_file = self.output_dir / filename
        
        serializable_results = convert_to_serializable(results)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to {output_file}")
        
        return output_file

