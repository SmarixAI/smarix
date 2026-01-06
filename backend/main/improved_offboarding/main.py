"""
Main entry point for Improved Offboarding Prerequisites
Run this script to process repository data and generate prerequisite analysis
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main.improved_offboarding.main_processor import ImprovedOffboardingProcessor


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Process repository data for improved offboarding prerequisites'
    )
    parser.add_argument(
        '--owner',
        type=str,
        default='torvalds',
        help='Repository owner (default: torvalds)'
    )
    parser.add_argument(
        '--repo',
        type=str,
        default='test-tlb',
        help='Repository name (default: test-tlb)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='backend/data/improved_offboarding',
        help='Output directory for JSON results (default: backend/data/improved_offboarding)'
    )
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = ImprovedOffboardingProcessor(output_dir=args.output_dir)
    
    # Process repository
    print(f"\n🚀 Starting Improved Offboarding Prerequisites Analysis")
    print(f"   Repository: {args.owner}/{args.repo}\n")
    
    results = processor.process_repository(args.owner, args.repo)
    
    if 'error' in results:
        print(f"\n❌ Processing failed: {results['error']}")
        sys.exit(1)
    
    # Print summary
    summary = results.get('summary', {})
    print(f"\n{'='*80}")
    print("📊 EXECUTIVE SUMMARY")
    print(f"{'='*80}")
    
    dc_summary = summary.get('data_collection_summary', {})
    print(f"\n📈 Data Collection:")
    print(f"   - PRs: {dc_summary.get('total_prs', 0)}")
    print(f"   - Commits: {dc_summary.get('total_commits', 0)}")
    print(f"   - Files: {dc_summary.get('total_files', 0)}")
    print(f"   - Contributors: {dc_summary.get('total_contributors', 0)}")
    
    ra_summary = summary.get('risk_analysis_summary', {})
    print(f"\n⚠️  Risk Analysis:")
    print(f"   - High-risk files: {ra_summary.get('high_risk_files', 0)}")
    print(f"   - Single-owner files: {ra_summary.get('single_owner_files', 0)}")
    print(f"   - Average bus factor: {ra_summary.get('average_bus_factor', 0):.2f}")
    print(f"   - Knowledge hotspots: {ra_summary.get('knowledge_hotspots', 0)}")
    
    ai_summary = summary.get('ai_intelligence_summary', {})
    print(f"\n🤖 AI Intelligence:")
    print(f"   - PR clusters: {ai_summary.get('pr_clusters', 0)}")
    ku = ai_summary.get('knowledge_units', {})
    print(f"   - Knowledge units: {ku.get('systems', 0)} systems, {ku.get('modules', 0)} modules, {ku.get('features', 0)} features")
    print(f"   - Roles detected: {ai_summary.get('roles_detected', 0)}")
    print(f"   - Knowledge gaps: {ai_summary.get('knowledge_gaps', 0)}")
    
    print(f"\n{'='*80}")
    print("✅ Processing completed successfully!")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()

