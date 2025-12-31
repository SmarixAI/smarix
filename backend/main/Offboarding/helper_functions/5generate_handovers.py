"""
Generate handovers from employee tasks with metadata.

This script:
- Reads employee tasks with metadata
- Creates handovers for each task
- Assigns new owners based on role matching with even distribution
- Generates handover metadata (ktType, lastUpdated, etc.)
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import random
from collections import defaultdict

# ================= PATHS =================

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

INPUT_FILE = OUTPUT_DIR / "4employee_tasks_with_metadata_finalCallData.json"
OUTPUT_FILE = OUTPUT_DIR / "5employee_handovers.json"

# ================= HELPERS =================

def generate_kt_types(task):
    """Generate knowledge transfer types based on task properties"""
    kt_types = []
    
    # Always include at least one type
    base_types = ["Docs", "Code Walkthrough", "Call", "Runbook"]
    
    # Add types based on task properties
    if task.get("tags"):
        tags = task.get("tags", [])
        if "Frontend" in tags or "Backend" in tags:
            kt_types.append("Code Walkthrough")
        if "Infra" in tags or "CI/CD" in tags:
            kt_types.append("Runbook")
        if "Security" in tags or "Critical" in tags:
            kt_types.append("Call")
    
    # Add based on file count
    changed_files = task.get("changed_files", [])
    if len(changed_files) > 5:
        kt_types.append("Code Walkthrough")
    
    # Add based on criticality
    criticality = task.get("criticality_score", 0)
    if criticality >= 70:
        kt_types.append("Call")
    
    # Ensure at least 2 types, max 3
    while len(kt_types) < 2:
        remaining = [t for t in base_types if t not in kt_types]
        if remaining:
            kt_types.append(random.choice(remaining))
        else:
            break
    
    return kt_types[:3] if len(kt_types) > 3 else kt_types


def generate_last_updated():
    """Generate a dummy 'lastUpdated' string"""
    options = [
        "Just now",
        "1 hour ago",
        "2 hours ago",
        "Yesterday",
        "2 days ago",
        "3 days ago",
        "1 week ago"
    ]
    # Weight towards recent updates
    weights = [0.2, 0.2, 0.15, 0.15, 0.1, 0.1, 0.1]
    return random.choices(options, weights=weights)[0]


def determine_handover_status(task_status, priority):
    """Determine handover status based on task status and priority"""
    if task_status == "completed":
        return random.choice(["Completed", "In Progress"])
    elif priority == "High":
        return random.choice(["Pending", "In Progress"])
    else:
        return random.choice(["Pending", "In Progress", "Not Started"])


def build_role_to_employees_map(employees):
    """Build a map of role -> list of employees with that role"""
    role_map = defaultdict(list)
    for emp in employees:
        role = emp.get("role", "Engineer")
        role_map[role].append(emp)
    return role_map


def get_next_owner_for_role(role_map, role, current_owner_id, assignment_counter):
    """Get the next owner for a role, ensuring even distribution"""
    if role not in role_map or not role_map[role]:
        return None
    
    # Filter out the current owner
    available_owners = [e for e in role_map[role] if e.get("employeeId") != current_owner_id]
    
    if not available_owners:
        # If no other owners available, use any from the role
        available_owners = role_map[role]
    
    # Use round-robin distribution based on assignment counter
    if role not in assignment_counter:
        assignment_counter[role] = 0
    
    owner_index = assignment_counter[role] % len(available_owners)
    assignment_counter[role] += 1
    
    return available_owners[owner_index]


def main():
    """Main function to generate handovers"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate handovers from employee tasks')
    parser.add_argument('--employee', type=str, help='Employee name to filter for (single user mode)')
    args = parser.parse_args()
    
    print("📂 Loading employee tasks data...")
    
    if not INPUT_FILE.exists():
        print(f"❌ Error: Input file not found: {INPUT_FILE}")
        return 1
    
    input_data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    employees = input_data.get("employees", [])
    
    # Filter for specific employee if provided
    if args.employee:
        employee_name_lower = args.employee.lower().strip()
        print(f"\n🔍 Searching for employee: '{args.employee}' (case-insensitive)...")
        
        # Try multiple matching strategies
        matched_employees = []
        for emp in employees:
            emp_name = emp.get("name", "").strip()
            
            # Case-insensitive name matching
            if emp_name.lower() == employee_name_lower:
                matched_employees.append(emp)
                print(f"  ✓ Found match: '{emp_name}' (employeeId: {emp.get('employeeId', 'N/A')})")
        
        if not matched_employees:
            print(f"❌ Error: Employee '{args.employee}' not found in input data")
            print(f"   Available employees: {[e.get('name', 'N/A') for e in employees[:10]]}...")
            return 1
        
        employees = matched_employees
        print(f"👤 Filtering for employee: {args.employee} ({len(employees)} found)")
    
    print(f"✓ Loaded {len(employees)} employees")
    
    # Build role mapping for owner assignment
    role_to_employees = build_role_to_employees_map(employees)
    
    # Track assignments for even distribution
    assignment_counter = defaultdict(int)
    
    print("\n🔧 Generating handovers from tasks...")
    
    handovers_output = {
        "generated_at": datetime.now().isoformat(),
        "total_employees": 0,
        "employees": []
    }
    
    for emp in employees:
        employee_id = emp.get("employeeId")
        employee_name = emp.get("name", "Unknown")
        employee_role = emp.get("role", "Engineer")
        
        tasks = emp.get("tasks", {})
        ai_tasks = tasks.get("ai", [])
        
        if not ai_tasks:
            continue
        
        handovers = []
        handover_counter = 1
        
        for task in ai_tasks:
            # Get new owner with same role (distributed evenly)
            new_owner = get_next_owner_for_role(
                role_to_employees,
                employee_role,
                employee_id,
                assignment_counter
            )
            
            if not new_owner:
                # Fallback: use first available employee
                all_employees = [e for e in employees if e.get("employeeId") != employee_id]
                if all_employees:
                    new_owner = all_employees[0]
                else:
                    continue
            
            # Create handover
            handover = {
                "id": f"h{handover_counter}",
                "item": task.get("title", "Untitled Task"),
                "currentOwner": employee_name,
                "newOwner": new_owner.get("name", "Unknown"),
                "priority": task.get("priority", "Medium"),
                "status": determine_handover_status(
                    task.get("status", "active"),
                    task.get("priority", "Medium")
                ),
                "ktType": generate_kt_types(task),
                "lastUpdated": generate_last_updated()
            }
            
            handovers.append(handover)
            handover_counter += 1
        
        if handovers:
            handovers_output["employees"].append({
                "employeeId": employee_id,
                "handovers": handovers
            })
    
    handovers_output["total_employees"] = len(handovers_output["employees"])
    
    # If filtering for a single employee, merge with existing data
    if args.employee and OUTPUT_FILE.exists() and handovers_output["employees"]:
        print(f"\n📝 Merging with existing data for single employee mode...")
        existing_data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        existing_employees = existing_data.get("employees", [])
        
        # Get the employeeId from the new data
        new_employee_id = handovers_output["employees"][0].get("employeeId")
        
        print(f"  Removing existing entries for employeeId: {new_employee_id}")
        original_count = len(existing_employees)
        
        # Remove old entry for this employee if exists
        existing_employees = [
            emp for emp in existing_employees
            if emp.get("employeeId") != new_employee_id
        ]
        
        removed_count = original_count - len(existing_employees)
        print(f"  Removed {removed_count} existing entry/entries")
        
        # Add new handovers data
        existing_employees.extend(handovers_output["employees"])
        
        handovers_output = {
            "generated_at": datetime.now().isoformat(),
            "total_employees": len(existing_employees),
            "employees": existing_employees
        }
        print(f"  Final count: {len(existing_employees)} employees in output file")
    
    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(handovers_output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print(f"\n✅ Handovers generated successfully!")
    print(f"   Output: {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    if args.employee:
        print(f"   Mode: Single employee mode (filtered for '{args.employee}')")
        print(f"   Employees processed: {len(handovers_output['employees'])}")
        if handovers_output['employees']:
            for emp in handovers_output['employees']:
                print(f"     - Employee ID: {emp.get('employeeId', 'N/A')} ({len(emp.get('handovers', []))} handovers)")
    else:
        print(f"   Mode: All employees mode")
        print(f"   Total employees with handovers: {handovers_output['total_employees']}")
    
    total_handovers = sum(len(emp["handovers"]) for emp in handovers_output["employees"])
    print(f"   Total handovers: {total_handovers}")
    
    # Count by priority
    all_handovers = [h for emp in handovers_output["employees"] for h in emp["handovers"]]
    high_priority = sum(1 for h in all_handovers if h["priority"] == "High")
    medium_priority = sum(1 for h in all_handovers if h["priority"] == "Medium")
    low_priority = sum(1 for h in all_handovers if h["priority"] == "Low")
    
    print(f"   High priority: {high_priority}")
    print(f"   Medium priority: {medium_priority}")
    print(f"   Low priority: {low_priority}")


if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        exit(exit_code)

