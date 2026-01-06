"""Test script for Handover module"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from main.improved_offboarding.handover.main_processor import HandoverProcessor

# Find prerequisite file
prereq_file = Path('backend/backend/data/improved_offboarding/torvalds_test-tlb_prerequisites.json')
if not prereq_file.exists():
    prereq_file = Path('backend/data/improved_offboarding/torvalds_test-tlb_prerequisites.json')

print(f"Loading prerequisite data from {prereq_file}...")
with open(prereq_file, 'r', encoding='utf-8') as f:
    prereq_data = json.load(f)

# Try to load Final Call data
final_call_file = Path('backend/data/improved_offboarding/final_call/torvalds_test-tlb_torvalds_final_call.json')
final_call_data = None
if final_call_file.exists():
    print(f"Loading Final Call data from {final_call_file}...")
    with open(final_call_file, 'r', encoding='utf-8') as f:
        final_call_data = json.load(f)

print("Processing Handover...")
processor = HandoverProcessor()
results = processor.process(prereq_data, final_call_data, 'torvalds')
processor.save_results(results, 'torvalds', 'test-tlb', 'torvalds')

print('\n✅ Handover processing completed!')

