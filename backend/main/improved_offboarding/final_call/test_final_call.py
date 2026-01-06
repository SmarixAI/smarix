"""Test script for Final Call module"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from main.improved_offboarding.final_call.main_processor import FinalCallProcessor

# Find prerequisite file
prereq_file = Path('backend/backend/data/improved_offboarding/torvalds_test-tlb_prerequisites.json')
if not prereq_file.exists():
    prereq_file = Path('backend/data/improved_offboarding/torvalds_test-tlb_prerequisites.json')

print(f"Loading prerequisite data from {prereq_file}...")
with open(prereq_file, 'r', encoding='utf-8') as f:
    prereq_data = json.load(f)

print("Processing Final Call...")
processor = FinalCallProcessor()
results = processor.process(prereq_data, 'torvalds')
processor.save_results(results, 'torvalds', 'test-tlb', 'torvalds')

print('\n✅ Final Call processing completed!')

