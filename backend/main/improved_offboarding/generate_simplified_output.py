"""
Script to generate simplified output from existing analysis results
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add to path
sys.path.insert(0, str(Path(__file__).parent))
from simplified_output import SimplifiedOutputFormatter


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load JSON file"""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None


def main():
    """Main function to generate simplified output"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate simplified offboarding output')
    parser.add_argument('--owner', required=True, help='Repository owner')
    parser.add_argument('--repo', required=True, help='Repository name')
    parser.add_argument('--employee', required=True, help='Employee username')
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print(f"Generating Simplified Output")
    print(f"Repository: {args.owner}/{args.repo}")
    print(f"Employee: {args.employee}")
    print(f"{'='*80}\n")
    
    # Load prerequisite data
    prereq_file = Path(f"backend/data/improved_offboarding/{args.owner}_{args.repo}_prerequisites.json")
    print(f"📂 Loading prerequisite data...")
    prerequisite_data = load_json_file(prereq_file)
    if not prerequisite_data:
        print("❌ Failed to load prerequisite data")
        return
    
    # Load final call data
    final_call_file = Path(f"backend/data/improved_offboarding/final_call/{args.owner}_{args.repo}_{args.employee}_final_call.json")
    print(f"📂 Loading Final Call data...")
    final_call_data = load_json_file(final_call_file)
    if not final_call_data:
        print("⚠️  Final Call data not found. Generating without it...")
        final_call_data = {}
    
    # Load handover data (optional)
    handover_file = Path(f"backend/data/improved_offboarding/handover/{args.owner}_{args.repo}_{args.employee}_handover.json")
    print(f"📂 Loading Handover data...")
    handover_data = load_json_file(handover_file)
    
    # Load documentation data (optional)
    doc_file = Path(f"backend/data/improved_offboarding/documentation/{args.owner}_{args.repo}_{args.employee}_documentation.json")
    print(f"📂 Loading Documentation data...")
    documentation_data = load_json_file(doc_file)
    
    # Generate simplified output
    print(f"\n🤖 Generating simplified output with AI...")
    formatter = SimplifiedOutputFormatter()
    
    simplified_output = formatter.generate_simplified_output(
        prerequisite_data=prerequisite_data,
        final_call_data=final_call_data,
        handover_data=handover_data,
        documentation_data=documentation_data,
        employee_username=args.employee
    )
    
    # Save output
    output_file = formatter.save_simplified_output(
        simplified_output,
        args.owner,
        args.repo,
        args.employee
    )
    
    print(f"\n✅ Simplified output generated successfully!")
    print(f"\n📊 Summary:")
    print(f"   - High-risk files analyzed: {len(simplified_output.get('detailed_analysis', {}).get('high_risk_files', []))}")
    print(f"   - Topics extracted: {len(simplified_output.get('detailed_analysis', {}).get('topic_extractions', []))}")
    print(f"   - Critical questions: {simplified_output.get('knowledge_transfer_summary', {}).get('what_manager_must_ask_before_day0', {}).get('total_critical', 0)}")
    print(f"   - Immediate actions: {len(simplified_output.get('action_items', {}).get('immediate_actions', []))}")
    
    print(f"\n💡 Key Questions Answered:")
    kt_summary = simplified_output.get('knowledge_transfer_summary', {})
    print(f"   ✓ What they know: {len(kt_summary.get('what_they_know_that_others_dont', {}).get('unique_knowledge_items', []))} unique knowledge items")
    print(f"   ✓ What could break: {len(kt_summary.get('what_could_break_after_they_leave', {}).get('systems_at_risk', []))} systems at risk")
    print(f"   ✓ Must ask questions: {kt_summary.get('what_manager_must_ask_before_day0', {}).get('total_critical', 0)} critical questions")
    
    print(f"\n📄 Output saved to: {output_file}")


if __name__ == '__main__':
    main()

