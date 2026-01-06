"""
Quick test to verify path resolution works from any directory
"""

from data_reader import DataReader
from main_processor import ImprovedOffboardingProcessor

print("Testing path resolution...")
print("=" * 60)

# Test DataReader
print("\n1. Testing DataReader:")
dr = DataReader()
print(f"   Base path: {dr.base_path}")
print(f"   Exists: {dr.base_path.exists()}")

# Test reading repo data
print("\n2. Testing repo data read:")
repo_data = dr.read_repo_data("torvalds", "test-tlb")
if repo_data:
    print(f"   ✓ Successfully loaded repo data")
    print(f"   - PRs: {len(repo_data.get('prs', []))}")
    print(f"   - Commits: {len(repo_data.get('commits', []))}")
    print(f"   - Files: {len(repo_data.get('code_files', []))}")
else:
    print(f"   ❌ Failed to load repo data")

# Test ImprovedOffboardingProcessor
print("\n3. Testing ImprovedOffboardingProcessor:")
proc = ImprovedOffboardingProcessor()
print(f"   Output dir: {proc.output_dir}")
print(f"   Exists: {proc.output_dir.exists()}")

print("\n" + "=" * 60)
print("✅ Path resolution test complete!")

