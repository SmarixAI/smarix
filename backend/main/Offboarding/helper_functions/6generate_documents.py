"""
Generate documents from employee tasks with metadata.

This script:
- Reads employee tasks with metadata
- Creates documents for each task based on file types and task properties
- Generates document metadata (name, status, priority, etc.)
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
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
OUTPUT_FILE = OUTPUT_DIR / "6employee_documents.json"

# ================= HELPERS =================

def generate_document_name(task):
    """Generate document name based on task properties"""
    title = task.get("title", "Untitled Task")
    
    # Extract key components from title
    title_lower = title.lower()
    
    # Document name templates based on task content
    document_templates = []
    
    # Check file types in changed files
    changed_files = task.get("changed_files", [])
    file_paths = [f.lower() for f in changed_files]
    
    # Determine document type based on files
    if any("config" in f or "setting" in f for f in file_paths):
        document_templates.append("Configuration Guide")
    if any("api" in f or "service" in f or "endpoint" in f for f in file_paths):
        document_templates.append("API Documentation")
    if any("auth" in f or "security" in f or "permission" in f for f in file_paths):
        document_templates.append("Security Documentation")
    if any("database" in f or "db" in f or "model" in f for f in file_paths):
        document_templates.append("Database Schema")
    if any("workflow" in f or "ci" in f or "deploy" in f for f in file_paths):
        document_templates.append("Deployment Guide")
    if any("test" in f for f in file_paths):
        document_templates.append("Testing Guide")
    
    # Check tags for additional context
    tags = task.get("tags", [])
    if "Frontend" in tags:
        document_templates.append("Frontend Architecture")
    if "Backend" in tags:
        document_templates.append("Backend Architecture")
    if "Infra" in tags:
        document_templates.append("Infrastructure Setup")
    
    # Check task title keywords
    if "fix" in title_lower or "bug" in title_lower:
        document_templates.append("Bug Fix Documentation")
    if "feature" in title_lower or "add" in title_lower:
        document_templates.append("Feature Documentation")
    if "refactor" in title_lower:
        document_templates.append("Refactoring Notes")
    
    # Default templates
    default_templates = [
        "System Overview",
        "Architecture Diagram",
        "Code Documentation",
        "Setup Guide",
        "User Manual",
        "Technical Specification",
        "Runbook",
        "Troubleshooting Guide"
    ]
    
    # Combine and select
    all_templates = document_templates + default_templates
    
    if all_templates:
        # Prefer task-specific templates, fallback to defaults
        if document_templates:
            base_name = random.choice(document_templates)
        else:
            base_name = random.choice(default_templates)
        
        # Add task context if available
        if len(changed_files) > 0:
            # Try to extract a meaningful component name
            first_file = changed_files[0]
            if "/" in first_file:
                parts = first_file.split("/")
                if len(parts) > 1:
                    component = parts[-2].replace("_", " ").title()
                    return f"{base_name} - {component}"
        
        return base_name
    
    return "System Documentation"


def determine_document_status(task, priority):
    """Determine document status based on task properties"""
    # Higher priority tasks more likely to have missing docs
    if priority == "High":
        return random.choices(
            ["Missing", "Partial", "Complete"],
            weights=[0.5, 0.3, 0.2]
        )[0]
    elif priority == "Medium":
        return random.choices(
            ["Missing", "Partial", "Complete"],
            weights=[0.4, 0.4, 0.2]
        )[0]
    else:
        return random.choices(
            ["Missing", "Partial", "Complete"],
            weights=[0.3, 0.4, 0.3]
        )[0]


def determine_ai_followup(task):
    """Determine if AI follow-up is needed"""
    priority = task.get("priority", "Medium")
    criticality = task.get("criticality_score", 0)
    status = task.get("status", "active")
    
    # High priority or critical tasks more likely to need AI follow-up
    if priority == "High" or criticality >= 70:
        return random.choices([True, False], weights=[0.7, 0.3])[0]
    elif priority == "Medium" or criticality >= 50:
        return random.choices([True, False], weights=[0.5, 0.5])[0]
    else:
        return random.choices([True, False], weights=[0.3, 0.7])[0]


def generate_last_updated(status):
    """Generate last updated timestamp based on status"""
    if status == "Missing":
        return "Never"
    elif status == "Partial":
        return random.choice(["1 week ago", "2 weeks ago", "1 month ago", "Yesterday"])
    elif status == "Complete":
        return random.choice(["Yesterday", "2 days ago", "1 week ago"])
    else:
        return "Never"


def main():
    """Main function to generate documents"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate documents from employee tasks')
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
    
    print("\n🔧 Generating documents from tasks...")
    
    documents_output = {
        "generated_at": datetime.now().isoformat(),
        "total_employees": 0,
        "employees": []
    }
    
    for emp in employees:
        employee_id = emp.get("employeeId")
        employee_name = emp.get("name", "Unknown")
        
        tasks = emp.get("tasks", {})
        ai_tasks = tasks.get("ai", [])
        
        if not ai_tasks:
            continue
        
        documents = []
        document_counter = 1
        
        # Group tasks by type to avoid duplicate documents
        processed_docs = set()
        
        for task in ai_tasks:
            # Generate document name
            doc_name = generate_document_name(task)
            
            # Avoid exact duplicates for same employee
            if doc_name in processed_docs:
                # Add variation
                doc_name = f"{doc_name} (v{document_counter})"
            
            processed_docs.add(doc_name)
            
            priority = task.get("priority", "Medium")
            status = determine_document_status(task, priority)
            ai_followup = determine_ai_followup(task)
            last_updated = generate_last_updated(status)
            
            # Create document
            document = {
                "id": f"d{document_counter}",
                "name": doc_name,
                "status": status,
                "priority": priority,
                "owner": employee_name,
                "aiFollowUp": ai_followup,
                "lastUpdated": last_updated
            }
            
            documents.append(document)
            document_counter += 1
        
        if documents:
            documents_output["employees"].append({
                "employeeId": employee_id,
                "documents": documents
            })
    
    documents_output["total_employees"] = len(documents_output["employees"])
    
    # If filtering for a single employee, merge with existing data
    if args.employee and OUTPUT_FILE.exists() and documents_output["employees"]:
        print(f"\n📝 Merging with existing data for single employee mode...")
        existing_data = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        existing_employees = existing_data.get("employees", [])
        
        # Get the employeeId from the new data
        new_employee_id = documents_output["employees"][0].get("employeeId")
        
        print(f"  Removing existing entries for employeeId: {new_employee_id}")
        original_count = len(existing_employees)
        
        # Remove old entry for this employee if exists
        existing_employees = [
            emp for emp in existing_employees
            if emp.get("employeeId") != new_employee_id
        ]
        
        removed_count = original_count - len(existing_employees)
        print(f"  Removed {removed_count} existing entry/entries")
        
        # Add new documents data
        existing_employees.extend(documents_output["employees"])
        
        documents_output = {
            "generated_at": datetime.now().isoformat(),
            "total_employees": len(existing_employees),
            "employees": existing_employees
        }
        print(f"  Final count: {len(existing_employees)} employees in output file")
    
    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(documents_output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    
    print(f"\n✅ Documents generated successfully!")
    print(f"   Output: {OUTPUT_FILE}")
    print(f"\n📊 Summary:")
    if args.employee:
        print(f"   Mode: Single employee mode (filtered for '{args.employee}')")
        print(f"   Employees processed: {len(documents_output['employees'])}")
        if documents_output['employees']:
            for emp in documents_output['employees']:
                print(f"     - Employee ID: {emp.get('employeeId', 'N/A')} ({len(emp.get('documents', []))} documents)")
    else:
        print(f"   Mode: All employees mode")
        print(f"   Total employees with documents: {documents_output['total_employees']}")
    
    total_documents = sum(len(emp["documents"]) for emp in documents_output["employees"])
    print(f"   Total documents: {total_documents}")
    
    # Count by status
    all_documents = [d for emp in documents_output["employees"] for d in emp["documents"]]
    missing = sum(1 for d in all_documents if d["status"] == "Missing")
    partial = sum(1 for d in all_documents if d["status"] == "Partial")
    complete = sum(1 for d in all_documents if d["status"] == "Complete")
    
    print(f"   Missing: {missing}")
    print(f"   Partial: {partial}")
    print(f"   Complete: {complete}")
    
    ai_followup_count = sum(1 for d in all_documents if d["aiFollowUp"])
    print(f"   AI Follow-up needed: {ai_followup_count}")


if __name__ == "__main__":
    exit_code = main()
    if exit_code:
        exit(exit_code)

