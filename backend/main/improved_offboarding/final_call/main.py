"""
Main entry point for Final Call module
"""

import sys
import argparse
import json
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from main.improved_offboarding.final_call.main_processor import FinalCallProcessor


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Process Final Call features (31-52) for improved offboarding'
    )
    parser.add_argument(
        '--prerequisite-file',
        type=str,
        required=True,
        help='Path to prerequisite JSON file (from improved_offboarding module)'
    )
    parser.add_argument(
        '--employee',
        type=str,
        default=None,
        help='Username of departing employee (optional)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='backend/data/improved_offboarding/final_call',
        help='Output directory for JSON results'
    )
    
    args = parser.parse_args()
    
    # Load prerequisite data
    print(f"\n📖 Loading prerequisite data from {args.prerequisite_file}...")
    try:
        with open(args.prerequisite_file, 'r', encoding='utf-8') as f:
            prerequisite_data = json.load(f)
        print(f"   ✓ Prerequisite data loaded")
    except Exception as e:
        print(f"❌ Error loading prerequisite data: {e}")
        sys.exit(1)
    
    # Initialize processor
    processor = FinalCallProcessor(output_dir=args.output_dir)
    
    # Process Final Call
    print(f"\n🚀 Starting Final Call Processing")
    if args.employee:
        print(f"   Employee: {args.employee}\n")
    
    results = processor.process(prerequisite_data, args.employee)
    
    # Extract repository info from prerequisite data
    metadata = prerequisite_data.get('metadata', {})
    repository = metadata.get('repository', 'unknown/unknown')
    owner, repo = repository.split('/') if '/' in repository else ('unknown', 'unknown')
    
    # Save results
    output_file = processor.save_results(results, owner, repo, args.employee)
    
    # Print summary
    summary = results.get('summary', {})
    print(f"\n{'='*80}")
    print("📊 FINAL CALL SUMMARY")
    print(f"{'='*80}")
    
    topic_summary = summary.get('topic_identification_summary', {})
    print(f"\n📋 Topic Identification:")
    print(f"   - Total topics: {topic_summary.get('total_topics', 0)}")
    print(f"   - Critical topics: {topic_summary.get('critical_topics', 0)}")
    print(f"   - High-risk files: {topic_summary.get('high_risk_files', 0)}")
    print(f"   - Knowledge units: {topic_summary.get('knowledge_units_needing_explanation', 0)}")
    
    discussion_summary = summary.get('discussion_summary', {})
    print(f"\n🤖 AI-Guided Discussion:")
    print(f"   - Agenda items: {discussion_summary.get('agenda_items', 0)}")
    print(f"   - Estimated time: {discussion_summary.get('estimated_time_hours', 0)} hours")
    print(f"   - Questions: {discussion_summary.get('total_questions', 0)}")
    print(f"   - Stakeholders: {discussion_summary.get('stakeholders', 0)}")
    
    execution_summary = summary.get('execution_summary', {})
    print(f"\n✅ Execution & Tracking:")
    print(f"   - Tasks: {execution_summary.get('total_tasks', 0)}")
    print(f"   - Checklists: {execution_summary.get('checklists_created', 0)}")
    print(f"   - Validation items: {execution_summary.get('validation_items', 0)}")
    
    print(f"\n{'='*80}")
    print("✅ Final Call processing completed successfully!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

