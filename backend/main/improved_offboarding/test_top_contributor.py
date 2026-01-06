"""
Test script to verify top contributor detection
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main.improved_offboarding.top_contributor import find_top_contributor, get_top_contributor_info

# Load prerequisite data
prereq_file = Path("backend/data/improved_offboarding/torvalds_test-tlb_prerequisites.json")

if not prereq_file.exists():
    print(f"❌ Prerequisite file not found: {prereq_file}")
    sys.exit(1)

with open(prereq_file, 'r', encoding='utf-8') as f:
    prereq_data = json.load(f)

# Find top contributor
top_contributor = find_top_contributor(prereq_data)
top_info = get_top_contributor_info(prereq_data)

print("="*60)
print("TOP CONTRIBUTOR DETECTION TEST")
print("="*60)

if top_contributor:
    print(f"\n✅ Top Contributor: {top_contributor}")
    if top_info:
        print(f"\n📊 Contribution Details:")
        print(f"   - PRs: {top_info.get('prs', 0)}")
        print(f"   - Commits: {top_info.get('commits', 0)}")
        print(f"   - Files modified: {top_info.get('files_modified', 0)}")
        print(f"   - Contribution score: {top_info.get('score', 0)}")
        print(f"   - Files: {', '.join(top_info.get('files', [])[:5])}")
else:
    print("\n❌ No top contributor found")

print("\n" + "="*60)

