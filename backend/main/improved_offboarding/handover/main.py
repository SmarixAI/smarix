"""
Main entry point for Handover module
"""

import sys
import argparse
import json
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from main.improved_offboarding.handover.main_processor import HandoverProcessor


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Process Handover features (53-73) for improved offboarding'
    )
    parser.add_argument(
        '--prerequisite-file',
        type=str,
        required=True,
        help='Path to prerequisite JSON file (from improved_offboarding module)'
    )
    parser.add_argument(
        '--final-call-file',
        type=str,
        default=None,
        help='Path to Final Call JSON file (optional)'
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
        default='backend/data/improved_offboarding/handover',
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
    
    # Load Final Call data if provided
    final_call_data = None
    if args.final_call_file:
        print(f"📖 Loading Final Call data from {args.final_call_file}...")
        try:
            with open(args.final_call_file, 'r', encoding='utf-8') as f:
                final_call_data = json.load(f)
            print(f"   ✓ Final Call data loaded")
        except Exception as e:
            print(f"⚠️  Warning: Could not load Final Call data: {e}")
    
    # Initialize processor
    processor = HandoverProcessor(output_dir=args.output_dir)
    
    # Process Handover
    print(f"\n🚀 Starting Handover Processing")
    if args.employee:
        print(f"   Employee: {args.employee}\n")
    
    results = processor.process(prerequisite_data, final_call_data, args.employee)
    
    # Extract repository info from prerequisite data
    metadata = prerequisite_data.get('metadata', {})
    repository = metadata.get('repository', 'unknown/unknown')
    owner, repo = repository.split('/') if '/' in repository else ('unknown', 'unknown')
    
    # Save results
    output_file = processor.save_results(results, owner, repo, args.employee)
    
    # Print summary
    summary = results.get('summary', {})
    print(f"\n{'='*80}")
    print("📊 HANDOVER SUMMARY")
    print(f"{'='*80}")
    
    ownership_summary = summary.get('ownership_summary', {})
    print(f"\n🔍 Ownership Identification:")
    print(f"   - Ownership gaps: {ownership_summary.get('total_gaps', 0)}")
    print(f"   - Successor requirements: {ownership_summary.get('successor_requirements', 0)}")
    print(f"   - Critical risk files: {ownership_summary.get('critical_risk_files', 0)}")
    print(f"   - Backup requirements: {ownership_summary.get('backup_requirements', 0)}")
    
    assignment_summary = summary.get('assignment_summary', {})
    print(f"\n👥 Smart Assignment:")
    print(f"   - Total assignments: {assignment_summary.get('total_assignments', 0)}")
    print(f"   - High confidence: {assignment_summary.get('high_confidence_assignments', 0)}")
    print(f"   - Unique candidates: {assignment_summary.get('unique_candidates', 0)}")
    
    kt_summary = summary.get('kt_planning_summary', {})
    print(f"\n📚 Knowledge Transfer Planning:")
    print(f"   - KT sessions: {kt_summary.get('total_kt_sessions', 0)}")
    print(f"   - Estimated hours: {kt_summary.get('total_kt_hours', 0):.1f}")
    print(f"   - Agenda items: {kt_summary.get('agenda_items', 0)}")
    print(f"   - Required artifacts: {kt_summary.get('required_artifacts', 0)}")
    
    execution_summary = summary.get('execution_summary', {})
    print(f"\n✅ Execution & Validation:")
    print(f"   - Acceptance workflows: {execution_summary.get('acceptance_workflows', 0)}")
    print(f"   - KT completion items: {execution_summary.get('kt_completion_items', 0)}")
    print(f"   - SLA tracking items: {execution_summary.get('sla_tracking_items', 0)}")
    print(f"   - Approval workflows: {execution_summary.get('approval_workflows', 0)}")
    
    print(f"\n{'='*80}")
    print("✅ Handover processing completed successfully!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

