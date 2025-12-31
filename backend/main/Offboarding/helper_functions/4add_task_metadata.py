
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ================= PATHS =================

# Base directory
# Find output directory dynamically
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "Offboarding"
if not OUTPUT_DIR.exists():
    # Try alternative paths
    possible_paths = [
        BASE_DIR / "backend" / "data" / "Offboarding",
        Path(r"C:\Users\vishalke\Desktop\AI007\super-employee\backend\data\Offboarding"),
        Path("data/Offboarding"),
        Path("../data/Offboarding"),
    ]
    for path in possible_paths:
        if path.exists() or path.parent.exists():
            OUTPUT_DIR = path
            break
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "3employee_prs_with_criticality.json"
OUTPUT_FILE = OUTPUT_DIR / "4employee_tasks_with_metadata_finalCallData.json"

# ================= HELPERS =================

def determine_priority(criticality_score):
    """Determine priority based on criticality score"""
    if criticality_score >= 70:
        return "High"
    elif criticality_score >= 30:
        return "Medium"
    else:
        return "Low"

def categorize_file(path: str) -> str:
    """Categorize file by path"""
    p = path.lower()
    if p.startswith(("frontend/", "lib/", "web/", "src/screens", "src/components", "ui/")):
        return "frontend"
    if p.startswith(("backend/", "server/", "api/", "service/")):
        return "backend"
    if p.startswith(("android/", "ios/", ".github/", "infra/", "docker", "pubspec", ".gitignore", "workflow", "ci/", "cd/")):
        return "infra"
    if p.endswith((".md", ".txt")) or "readme" in p or "doc" in p:
        return "docs"
    if "test" in p or p.endswith(("_test.dart", ".test.js", "test.py")):
        return "test"
    return "other"

def is_critical_file(path: str) -> bool:
    """Check if file is critical"""
    keywords = ["auth", "notification", "config", "security", "permission", "api", "database", "payment", "billing"]
    return any(k in path.lower() for k in keywords)

def generate_tags(task):
    """Generate tags based on task properties"""
    tags = set()
    
    # Get file categories from changed_files
    changed_files = task.get("changed_files", [])
    file_categories = set()
    has_critical_files = False
    has_single_owner = len(task.get("single_owner_files", [])) > 0
    
    for file_path in changed_files:
        category = categorize_file(file_path)
        file_categories.add(category)
        if is_critical_file(file_path):
            has_critical_files = True
    
    # Add category tags (capitalize first letter)
    for cat in file_categories:
        if cat in ["backend", "frontend", "infra", "docs", "test"]:
            tags.add(cat.capitalize())
    
    # Add special tags
    if has_critical_files:
        tags.add("Risk")
    
    if has_single_owner:
        tags.add("Ownership")
    
    # Add tags based on criticality score
    criticality_score = task.get("criticality_score", 0)
    if criticality_score >= 70:
        tags.add("Critical")
    elif criticality_score >= 50:
        tags.add("Important")
    
    # Add tags based on file count
    total_files = len(changed_files)
    if total_files > 15:
        tags.add("Large Change")
    elif total_files > 5:
        tags.add("Medium Change")
    
    # Add tags based on PR state
    state = task.get("state", "").lower()
    if state == "merged":
        tags.add("Merged")
    elif state == "closed":
        tags.add("Closed")
    
    # Add tags based on duration
    duration_days = task.get("duration_days", 0)
    if duration_days > 14:
        tags.add("Long Duration")
    elif duration_days > 7:
        tags.add("Extended")
    
    # Add tags based on commits
    commit_summary = task.get("commit_summary", {})
    total_commits = commit_summary.get("total_commits", 0)
    if total_commits > 10:
        tags.add("Multiple Iterations")
    elif total_commits > 5:
        tags.add("Iterative")
    
    # Convert to sorted list
    return sorted(list(tags))

def determine_status(task):
    """Determine status based on task properties"""
    # Default to active, but could be based on PR state
    state = task.get("state", "").lower()
    
    if state == "closed" or state == "merged":
        return "completed"
    elif state == "open":
        return "active"
    else:
        # Default to active for all tasks
        return "active"

def main():
    """Main execution function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Add task metadata to employee PRs')
    parser.add_argument('--employee', type=str, help='Employee name to filter for (single user mode)')
    args = parser.parse_args()
    
    # ================= LOAD DATA =================
    
    print("📂 Loading data file...")
    
    input_data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    
    print(f"✓ Loaded data with {input_data.get('total_employees', 0)} employees")
    
    # Filter for specific employee if provided
    employees_to_process = input_data.get("employees", [])
    if args.employee:
        employee_name_lower = args.employee.lower().strip()
        print(f"\n🔍 Searching for employee: '{args.employee}' (case-insensitive)...")
        print(f"   Total employees in input: {len(employees_to_process)}")
        
        # Try to get employeeId from users.json for better matching
        employee_id_from_users = None
        try:
            BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
            USERS_FILE = BASE_DIR / "data" / "Admin" / "users.json"
            if not USERS_FILE.exists():
                possible_paths = [
                    BASE_DIR / "backend" / "data" / "Admin" / "users.json",
                    Path(r"C:\Users\vishalke\Desktop\AI007\super-employee\backend\data\Admin\users.json"),
                ]
                for path in possible_paths:
                    if path.exists():
                        USERS_FILE = path
                        break
            
            if USERS_FILE.exists():
                users_data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
                for user in users_data.get("users", []):
                    if user.get("name", "").lower() == employee_name_lower or \
                       user.get("username", "").lower() == employee_name_lower:
                        employee_id_from_users = user.get("employeeId")
                        print(f"   Found in users.json: employeeId = {employee_id_from_users}")
                        break
        except Exception as e:
            print(f"   Warning: Could not read users.json: {e}")
        
        # Try multiple matching strategies
        matched_employees = []
        for emp in employees_to_process:
            emp_name = emp.get("name", "").strip()
            emp_username = emp.get("username", "").strip()
            emp_id = emp.get("employeeId")
            
            # Case-insensitive name matching or employeeId matching
            if (emp_name.lower() == employee_name_lower or 
                emp_username.lower() == employee_name_lower or
                (employee_id_from_users and emp_id == employee_id_from_users)):
                matched_employees.append(emp)
                print(f"  ✓ Found match: '{emp_name}' (employeeId: {emp_id})")
        
        if not matched_employees:
            print(f"❌ Error: Employee '{args.employee}' not found in input data")
            print(f"   Available employees (first 10):")
            for i, emp in enumerate(employees_to_process[:10], 1):
                print(f"     {i}. {emp.get('name', 'N/A')} (ID: {emp.get('employeeId', 'N/A')})")
            return 1
        
        employees_to_process = matched_employees
        print(f"👤 Filtering for employee: {args.employee} ({len(employees_to_process)} found)")
        print(f"   Will process only this employee's data")
    
    # ================= ENRICH WITH METADATA =================
    
    print("\n🔧 Adding priority, tags, and status to tasks...")
    
    enriched_employees = []
    
    for emp_data in employees_to_process:
        employee_id = emp_data.get("employeeId")
        tasks_data = emp_data.get("tasks", {})
        ai_tasks = tasks_data.get("ai", [])
        
        enriched_ai_tasks = []
        
        for task in ai_tasks:
            # Create enriched task with metadata
            enriched_task = {
                **task,  # Keep all existing fields
                "priority": determine_priority(task.get("criticality_score", 0)),
                "tags": generate_tags(task),
                "status": determine_status(task)
            }
            enriched_ai_tasks.append(enriched_task)
        
        # Preserve all employee metadata including dummy data
        enriched_employees.append({
            "employeeId": employee_id,
            "name": emp_data.get("name", "Unknown"),  # Changed from "login" to "name"
            "role": emp_data.get("role", "Engineer"),
            "risk": emp_data.get("risk", "medium"),
            "status": emp_data.get("status", "active"),
            "lastDay": emp_data.get("lastDay"),
            "tasks": {
                "ai": enriched_ai_tasks
            }
        })
        
        # Show stats
        high_priority = sum(1 for t in enriched_ai_tasks if t["priority"] == "High")
        medium_priority = sum(1 for t in enriched_ai_tasks if t["priority"] == "Medium")
        low_priority = sum(1 for t in enriched_ai_tasks if t["priority"] == "Low")
        
        print(f"  ✓ {employee_id}: {len(enriched_ai_tasks)} tasks | High: {high_priority} | Medium: {medium_priority} | Low: {low_priority}")
    
    # ================= BUILD FINAL OUTPUT =================
    
    # If filtering for a single employee, merge with existing data
    if args.employee and OUTPUT_FILE.exists():
        print(f"\n📝 Merging with existing data for single employee mode...")
        existing_data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        existing_employees = existing_data.get("employees", [])
        
        # Get the employeeId(s) from the enriched data to match
        enriched_employee_ids = {emp.get("employeeId") for emp in enriched_employees}
        enriched_employee_names = {emp.get("name", "").lower().strip() for emp in enriched_employees}
        
        print(f"  Removing existing entries for employeeId(s): {enriched_employee_ids}")
        print(f"  Removing existing entries for name(s): {enriched_employee_names}")
        
        # Remove old entries for this employee (match by employeeId or name)
        original_count = len(existing_employees)
        existing_employees = [
            emp for emp in existing_employees
            if emp.get("employeeId") not in enriched_employee_ids 
            and emp.get("name", "").lower().strip() not in enriched_employee_names
        ]
        removed_count = original_count - len(existing_employees)
        print(f"  Removed {removed_count} existing entry/entries")
        
        # Add new enriched data
        existing_employees.extend(enriched_employees)
        
        final_output = {
            "generated_at": datetime.now().isoformat(),
            "total_employees": len(existing_employees),
            "employees": existing_employees
        }
        print(f"  Final count: {len(existing_employees)} employees in output file")
    else:
        final_output = {
            "generated_at": datetime.now().isoformat(),
            "total_employees": len(enriched_employees),
            "employees": enriched_employees
        }
    
    # ================= WRITE OUTPUT =================
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(final_output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print(f"\n✅ Enriched data with metadata written to:")
    print(f"   {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    if args.employee:
        print(f"   Mode: Single employee mode (filtered for '{args.employee}')")
        print(f"   Employees processed: {len(enriched_employees)}")
        if enriched_employees:
            for emp in enriched_employees:
                print(f"     - {emp.get('name', 'Unknown')} (ID: {emp.get('employeeId', 'N/A')})")
    else:
        print(f"   Mode: All employees mode")
        print(f"   Total employees: {len(enriched_employees)}")
    
    # Calculate overall stats
    all_tasks = [t for emp in enriched_employees for t in emp["tasks"].get("ai", [])]
    if all_tasks:
        high_count = sum(1 for t in all_tasks if t["priority"] == "High")
        medium_count = sum(1 for t in all_tasks if t["priority"] == "Medium")
        low_count = sum(1 for t in all_tasks if t["priority"] == "Low")
        active_count = sum(1 for t in all_tasks if t["status"] == "active")
        completed_count = sum(1 for t in all_tasks if t["status"] == "completed")
        
        print(f"   Total tasks: {len(all_tasks)}")
        print(f"   High priority: {high_count}")
        print(f"   Medium priority: {medium_count}")
        print(f"   Low priority: {low_count}")
        print(f"   Active: {active_count}")
        print(f"   Completed: {completed_count}")
    
        print(f"\n💡 Metadata added:")
        print(f"   - Priority: Based on criticality_score (High >=70, Medium 30-69, Low <30)")
        print(f"   - Tags: Based on file categories, criticality, ownership, and other factors")
        print(f"   - Status: Based on PR state (active/completed)")


if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        exit(exit_code)

