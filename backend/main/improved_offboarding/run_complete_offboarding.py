"""
Complete Offboarding Runner
Runs all 4 modules sequentially for a complete offboarding analysis
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main.improved_offboarding.main_processor import ImprovedOffboardingProcessor
from main.improved_offboarding.final_call.main_processor import FinalCallProcessor
from main.improved_offboarding.handover.main_processor import HandoverProcessor
from main.improved_offboarding.documentation.main_processor import DocumentationProcessor
from main.improved_offboarding.simplified_output import SimplifiedOutputFormatter
from main.improved_offboarding.top_contributor import find_top_contributor, get_top_contributor_info
from main.improved_offboarding.contributor_filter import ContributorDataFilter


def run_complete_offboarding(owner: str, repo: str, employee: str = None):
    """
    Run complete offboarding process for a repository
    
    Args:
        owner: Repository owner (e.g., 'CCExtractor')
        repo: Repository name (e.g., 'taskwarrior-flutter')
        employee: Employee username (optional, auto-detects top contributor if None)
    """
    # Step 1: Run Prerequisites first to get contributor data
    print("\n" + "="*80)
    print("🚀 COMPLETE IMPROVED OFFBOARDING SYSTEM")
    print("="*80)
    print(f"Repository: {owner}/{repo}")
    print("="*80 + "\n")
    
    # Step 1: Prerequisites (needed to find top contributor)
    print("="*80)
    print("STEP 1/4: PREREQUISITES (Features 1-30)")
    print("="*80)
    prereq_processor = ImprovedOffboardingProcessor()
    prereq_results = prereq_processor.process_repository(owner, repo)
    
    if 'error' in prereq_results:
        print(f"❌ Error in prerequisites: {prereq_results['error']}")
        return
    
    # Auto-detect top contributor if employee not specified
    if employee is None:
        top_contributor = find_top_contributor(prereq_results)
        if top_contributor:
            employee = top_contributor
            top_info = get_top_contributor_info(prereq_results)
            print(f"\n🔍 Auto-detected top contributor: {employee}")
            if top_info:
                print(f"   - PRs: {top_info.get('prs', 0)}")
                print(f"   - Commits: {top_info.get('commits', 0)}")
                print(f"   - Files modified: {top_info.get('files_modified', 0)}")
                print(f"   - Contribution score: {top_info.get('score', 0)}")
        else:
            employee = owner
            print(f"\n⚠️  Could not detect top contributor, using owner: {employee}")
    else:
        print(f"\n👤 Using specified employee: {employee}")
    
    prereq_file = prereq_processor.output_dir / f"{owner}_{repo}_prerequisites.json"
    print(f"\n✅ Prerequisites completed. Output: {prereq_file}")
    print(f"📋 Employee selected: {employee}")
    print("="*80 + "\n")
    
    # Filter data to focus only on this contributor
    print("🔍 Filtering data to focus on top contributor's work...")
    contributor_filter = ContributorDataFilter(employee)
    filtered_prereq_data = contributor_filter.filter_prerequisite_data(prereq_results)
    contributor_context = contributor_filter.get_contributor_context(prereq_results)
    
    print(f"   ✓ Filtered to {contributor_context.get('ownership', {}).get('total_files_owned', 0)} files owned by {employee}")
    print(f"   ✓ High-risk files: {len(contributor_context.get('ownership', {}).get('high_risk_files_owned', []))}")
    print(f"   ✓ Single-owner files: {len(contributor_context.get('ownership', {}).get('single_owner_files_owned', []))}")
    print("="*80 + "\n")
    
    # Step 2: Final Call (using filtered data)
    print("\n" + "="*80)
    print("STEP 2/4: FINAL CALL (Features 31-52)")
    print("="*80)
    final_call_processor = FinalCallProcessor()
    # Pass both filtered data and contributor context
    final_call_results = final_call_processor.process(filtered_prereq_data, employee, contributor_context)
    final_call_file = final_call_processor.save_results(final_call_results, owner, repo, employee)
    print(f"\n✅ Final Call completed. Output: {final_call_file}")
    
    # Step 3: Handover (using filtered data)
    print("\n" + "="*80)
    print("STEP 3/4: HANDOVER (Features 53-73)")
    print("="*80)
    handover_processor = HandoverProcessor()
    handover_results = handover_processor.process(filtered_prereq_data, final_call_results, employee, contributor_context)
    handover_file = handover_processor.save_results(handover_results, owner, repo, employee)
    print(f"\n✅ Handover completed. Output: {handover_file}")
    
    # Step 4: Documentation (using filtered data)
    print("\n" + "="*80)
    print("STEP 4/4: DOCUMENTATION (Features 74-89)")
    print("="*80)
    doc_processor = DocumentationProcessor()
    doc_results = doc_processor.process(filtered_prereq_data, final_call_results, handover_results, employee, contributor_context)
    doc_file = doc_processor.save_results(doc_results, owner, repo, employee)
    print(f"\n✅ Documentation completed. Output: {doc_file}")
    
    # Final Summary
    print("\n" + "="*80)
    print("🎉 COMPLETE OFFBOARDING ANALYSIS FINISHED")
    print("="*80)
    
    # Print summaries
    print("\n📊 PREREQUISITES SUMMARY:")
    prereq_summary = prereq_results.get('summary', {})
    dc_summary = prereq_summary.get('data_collection_summary', {})
    ra_summary = prereq_summary.get('risk_analysis_summary', {})
    ai_summary = prereq_summary.get('ai_intelligence_summary', {})
    print(f"   - PRs: {dc_summary.get('total_prs', 0)}")
    print(f"   - Commits: {dc_summary.get('total_commits', 0)}")
    print(f"   - Files: {dc_summary.get('total_files', 0)}")
    print(f"   - High-risk files: {ra_summary.get('high_risk_files', 0)}")
    print(f"   - Knowledge gaps: {ai_summary.get('knowledge_gaps', 0)}")
    
    print("\n📋 FINAL CALL SUMMARY:")
    fc_summary = final_call_results.get('summary', {})
    fc_topic = fc_summary.get('topic_identification_summary', {})
    fc_disc = fc_summary.get('discussion_summary', {})
    print(f"   - Topics: {fc_topic.get('total_topics', 0)}")
    print(f"   - Agenda items: {fc_disc.get('agenda_items', 0)}")
    print(f"   - Estimated time: {fc_disc.get('estimated_time_hours', 0)} hours")
    print(f"   - Questions: {fc_disc.get('total_questions', 0)}")
    
    print("\n👥 HANDOVER SUMMARY:")
    ho_summary = handover_results.get('summary', {})
    ho_own = ho_summary.get('ownership_summary', {})
    ho_assign = ho_summary.get('assignment_summary', {})
    ho_kt = ho_summary.get('kt_planning_summary', {})
    print(f"   - Ownership gaps: {ho_own.get('total_gaps', 0)}")
    print(f"   - Assignments: {ho_assign.get('total_assignments', 0)}")
    print(f"   - KT hours: {ho_kt.get('total_kt_hours', 0):.1f}")
    
    print("\n📚 DOCUMENTATION SUMMARY:")
    doc_summary = doc_results.get('summary', {})
    doc_det = doc_summary.get('detection_summary', {})
    doc_creat = doc_summary.get('creation_summary', {})
    print(f"   - Documentation gaps: {doc_det.get('total_gaps', 0)}")
    print(f"   - Outlines created: {doc_creat.get('outlines_created', 0)}")
    print(f"   - Content drafts: {doc_creat.get('content_drafts', 0)}")
    
    # Step 5: Generate Simplified Output
    print("\n" + "="*80)
    print("STEP 5/5: SIMPLIFIED OUTPUT (AI-Driven Summary)")
    print("="*80)
    print("🤖 Generating simplified output with AI analysis...")
    formatter = SimplifiedOutputFormatter()
    simplified_output = formatter.generate_simplified_output(
        prerequisite_data=prereq_results,
        final_call_data=final_call_results,
        handover_data=handover_results,
        documentation_data=doc_results,
        employee_username=employee
    )
    simplified_file = formatter.save_simplified_output(simplified_output, owner, repo, employee)
    print(f"\n✅ Simplified output completed. Output: {simplified_file}")
    
    # Print simplified summary
    print("\n💡 KEY KNOWLEDGE TRANSFER QUESTIONS ANSWERED:")
    kt_summary = simplified_output.get('knowledge_transfer_summary', {})
    what_they_know = kt_summary.get('what_they_know_that_others_dont', {})
    what_could_break = kt_summary.get('what_could_break_after_they_leave', {})
    must_ask = kt_summary.get('what_manager_must_ask_before_day0', {})
    print(f"   ✓ What they know: {len(what_they_know.get('unique_knowledge_items', []))} unique items")
    print(f"   ✓ What could break: {len(what_could_break.get('systems_at_risk', []))} systems at risk")
    print(f"   ✓ Must ask questions: {must_ask.get('total_critical', 0)} critical questions")
    
    print("\n" + "="*80)
    print("📁 ALL OUTPUT FILES:")
    print("="*80)
    print(f"   1. Prerequisites: {prereq_file}")
    print(f"   2. Final Call:    {final_call_file}")
    print(f"   3. Handover:      {handover_file}")
    print(f"   4. Documentation: {doc_file}")
    print(f"   5. Simplified:    {simplified_file} ⭐")
    print("="*80 + "\n")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run complete offboarding analysis')
    parser.add_argument('--owner', type=str, default='CCExtractor', help='Repository owner')
    parser.add_argument('--repo', type=str, default='taskwarrior-flutter', help='Repository name')
    parser.add_argument('--employee', type=str, default=None, help='Employee username (defaults to owner)')
    
    args = parser.parse_args()
    
    run_complete_offboarding(args.owner, args.repo, args.employee)

