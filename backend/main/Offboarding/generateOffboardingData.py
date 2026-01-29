"""
Orchestrator script to run all offboarding data generation steps in order.

Execution order:
1. Extract unique PR users and assign employee IDs
2. Extract employee changed files and calculate risk scores
3. Add criticality scores and commit details
4. Add task metadata (priority, tags, status)
5. Generate handovers from tasks
6. Generate documents from tasks
"""

import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import io
from utils.s3 import s3_manager
from utils.repo_context import get_repo_context

ctx = get_repo_context()
REPO_OWNER = ctx["owner"]
REPO_NAME = ctx["repo"]

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Base directories
BASE_DIR = Path(__file__).parent
HELPER_FUNCTIONS_DIR = BASE_DIR / "helper_functions"

# Find output directory dynamically
def find_output_dir():
    """Find the offboarding output directory"""
    repo_root = BASE_DIR.parent.parent.parent
    possible_paths = [
        repo_root / "data" / "Offboarding",
        repo_root / "backend" / "data" / "Offboarding",
        Path("../..") / "data" / "Offboarding",
        Path("data/Offboarding"),
        Path("../data/Offboarding"),
    ]
    for path in possible_paths:
        abs_path = path.resolve() if path.is_absolute() or path.exists() else repo_root / path
        if abs_path.parent.exists():
            return abs_path
    # Default to repo_root/data/Offboarding
    output_dir = repo_root / "data" / "Offboarding"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

OUTPUT_DIR = find_output_dir()

# Script execution order - mapping step IDs to script names
STEP_TO_SCRIPT = {
    "extract_users": "1extract_unique_pr_users.py",
    "extract_files": "2extract_employee_changed_files.py",
    "add_criticality": "3add_criticality_scores.py",
    "add_metadata": "4add_task_metadata.py",
    "generate_handovers": "5generate_handovers.py",
    "generate_documents": "6generate_documents.py"
}

# All scripts in order
ALL_SCRIPTS = [
    "1extract_unique_pr_users.py",
    "2extract_employee_changed_files.py",
    "3add_criticality_scores.py",
    "4add_task_metadata.py",
    "5generate_handovers.py",
    "6generate_documents.py"
]


def run_script(script_name, employee_name=None):
    """Run a single script and return success status"""
    script_path = HELPER_FUNCTIONS_DIR / script_name
    
    if not script_path.exists():
        print(f"❌ Error: Script not found: {script_path}")
        return False
    
    print(f"\n{'='*70}")
    print(f"▶️  Running: {script_name}")
    if employee_name:
        print(f"   Filtering for employee: {employee_name}")
    print(f"{'='*70}\n")
    
    try:
        # Build command
        cmd = [sys.executable, str(script_path)]
        if employee_name:
            cmd.extend(['--employee', employee_name])
        
        # Run the script
        result = subprocess.run(
            cmd,
            cwd=str(HELPER_FUNCTIONS_DIR),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✅ Successfully completed: {script_name}\n")
            return True
        else:
            print(f"\n❌ Error running {script_name} (exit code: {result.returncode})\n")
            return False
            
    except Exception as e:
        print(f"\n❌ Exception while running {script_name}: {e}\n")
        return False


def main():
    """Main orchestrator function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run offboarding data generation pipeline')
    parser.add_argument('--steps', nargs='+', help='List of step IDs to run (e.g., extract_users extract_files)')
    parser.add_argument('--employee', type=str, help='Employee name to filter for (single user mode)')
    args = parser.parse_args()
    
    # Determine which scripts to run
    if args.steps:
        # Map step IDs to script names and filter to only include valid steps
        scripts_to_run = []
        invalid_steps = []
        for step_id in args.steps:
            if step_id in STEP_TO_SCRIPT:
                script_name = STEP_TO_SCRIPT[step_id]
                # Only add if not already in list (maintain order from ALL_SCRIPTS)
                if script_name not in scripts_to_run:
                    scripts_to_run.append(script_name)
            else:
                invalid_steps.append(step_id)
        
        if invalid_steps:
            print(f"⚠️  Warning: Invalid step IDs: {invalid_steps}")
            print(f"   Valid step IDs: {', '.join(STEP_TO_SCRIPT.keys())}")
        
        # Maintain execution order by filtering ALL_SCRIPTS
        SCRIPTS = [script for script in ALL_SCRIPTS if script in scripts_to_run]
        
        if not SCRIPTS:
            print("❌ Error: No valid scripts to run")
            return 1
    else:
        # Run all scripts if no steps specified
        SCRIPTS = ALL_SCRIPTS
    
    print("="*70)
    print("🚀 Offboarding Data Generation Pipeline")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base directory: {BASE_DIR}")
    print(f"Helper functions: {HELPER_FUNCTIONS_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    if args.employee:
        print(f"👤 Employee filter: {args.employee} (single user mode)")
    print(f"Running {len(SCRIPTS)} step(s): {', '.join([s.replace('.py', '') for s in SCRIPTS])}")
    
    # Check if helper_functions directory exists
    if not HELPER_FUNCTIONS_DIR.exists():
        print(f"\n❌ Error: Helper functions directory not found: {HELPER_FUNCTIONS_DIR}")
        return 1
    
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run each script in order
    failed_scripts = []
    
    for i, script in enumerate(SCRIPTS, 1):
        print(f"\n📋 Step {i}/{len(SCRIPTS)}: {script}")
        
        # Only pass employee_name to scripts 4, 5, and 6 (final call, handovers, documents)
        # Scripts 1, 2, 3 should run for all users (as per user requirement)
        employee_filter = None
        if args.employee and script in ["4add_task_metadata.py", "5generate_handovers.py", "6generate_documents.py"]:
            employee_filter = args.employee.strip()
            print(f"   ⚠️  Single-user mode: Only processing data for '{employee_filter}'")
        
        success = run_script(script, employee_filter)
        
        if not success:
            failed_scripts.append(script)
            print(f"\n⚠️  Warning: {script} failed. Continuing with next script...")
    
    # Summary
    print("\n" + "="*70)
    print("📊 Execution Summary")
    print("="*70)
    
    if failed_scripts:
        print(f"❌ Failed scripts ({len(failed_scripts)}):")
        for script in failed_scripts:
            print(f"   - {script}")
        print(f"\n✅ Successful scripts: {len(SCRIPTS) - len(failed_scripts)}/{len(SCRIPTS)}")
        return 1
    else:
        print(f"✅ All {len(SCRIPTS)} selected script(s) completed successfully!")
        print(f"\n📁 Output files (saved to {OUTPUT_DIR}):")
        output_files = [
            "1employees_with_ids.json",
            "2employee_changed_files.json",
            "3employee_prs_with_criticality.json",
            "4employee_tasks_with_metadata_finalCallData.json",
            "5employee_handovers.json",
            "6employee_documents.json"
        ]
        for i, script in enumerate(SCRIPTS, 1):
            # Find corresponding output file
            script_num = script[0]  # Get the number from script name
            for output_file in output_files:
                if output_file.startswith(script_num):
                    print(f"   {i}. {OUTPUT_DIR / output_file}")
                    break
        print(f"\n✨ Pipeline completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

