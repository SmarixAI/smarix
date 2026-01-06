"""
Main entry point for Documentation module
"""

import sys
import argparse
import json
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from main.improved_offboarding.documentation.main_processor import DocumentationProcessor


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Process Documentation features (74-89) for improved offboarding'
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
        '--handover-file',
        type=str,
        default=None,
        help='Path to Handover JSON file (optional)'
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
        default='backend/data/improved_offboarding/documentation',
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
    
    # Load Handover data if provided
    handover_data = None
    if args.handover_file:
        print(f"📖 Loading Handover data from {args.handover_file}...")
        try:
            with open(args.handover_file, 'r', encoding='utf-8') as f:
                handover_data = json.load(f)
            print(f"   ✓ Handover data loaded")
        except Exception as e:
            print(f"⚠️  Warning: Could not load Handover data: {e}")
    
    # Initialize processor
    processor = DocumentationProcessor(output_dir=args.output_dir)
    
    # Process Documentation
    print(f"\n🚀 Starting Documentation Processing")
    if args.employee:
        print(f"   Employee: {args.employee}\n")
    
    results = processor.process(prerequisite_data, final_call_data, handover_data, args.employee)
    
    # Extract repository info from prerequisite data
    metadata = prerequisite_data.get('metadata', {})
    repository = metadata.get('repository', 'unknown/unknown')
    owner, repo = repository.split('/') if '/' in repository else ('unknown', 'unknown')
    
    # Save results
    output_file = processor.save_results(results, owner, repo, args.employee)
    
    # Print summary
    summary = results.get('summary', {})
    print(f"\n{'='*80}")
    print("📊 DOCUMENTATION SUMMARY")
    print(f"{'='*80}")
    
    detection_summary = summary.get('detection_summary', {})
    print(f"\n🔍 Documentation Detection:")
    print(f"   - Total gaps: {detection_summary.get('total_gaps', 0)}")
    print(f"   - Critical gaps: {detection_summary.get('critical_gaps', 0)}")
    print(f"   - Existing docs: {detection_summary.get('existing_docs', 0)}")
    print(f"   - Duplicate docs: {detection_summary.get('duplicate_docs', 0)}")
    
    creation_summary = summary.get('creation_summary', {})
    print(f"\n🤖 AI-Assisted Creation:")
    print(f"   - Outlines created: {creation_summary.get('outlines_created', 0)}")
    print(f"   - Content drafts: {creation_summary.get('content_drafts', 0)}")
    print(f"   - Diagrams suggested: {creation_summary.get('diagrams_suggested', 0)}")
    print(f"   - Code mappings: {creation_summary.get('code_mappings', 0)}")
    
    management_summary = summary.get('management_summary', {})
    print(f"\n📋 Management & Quality:")
    print(f"   - Ownership assignments: {management_summary.get('ownership_assignments', 0)}")
    print(f"   - Status tracking items: {management_summary.get('status_tracking_items', 0)}")
    print(f"   - Review workflows: {management_summary.get('review_workflows', 0)}")
    print(f"   - Follow-up suggestions: {management_summary.get('followup_suggestions', 0)}")
    
    print(f"\n{'='*80}")
    print("✅ Documentation processing completed successfully!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

