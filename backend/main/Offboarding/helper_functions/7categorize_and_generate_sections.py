"""
Categorize PRs/tasks into Final Call, Handover, and Documentation sections.

This script:
- Reads employee PRs with criticality data
- Uses LLM to analyze each task for better categorization
- Detects employee roles based on PRs they worked on
- Generates Final Call tasks, Handovers, and Documents
- Uses intelligent categorization for accurate section assignment
"""

import json
import os
from pathlib import Path
from datetime import datetime
import random
from collections import defaultdict
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        openai_client = OpenAI(api_key=api_key)
    else:
        print("⚠️  Warning: OPENAI_API_KEY not found in environment. Falling back to rule-based categorization.")
        OPENAI_AVAILABLE = False
        openai_client = None
except ImportError:
    print("⚠️  Warning: OpenAI package not installed. Install with: pip install openai")
    OPENAI_AVAILABLE = False
    openai_client = None

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

INPUT_FILE = OUTPUT_DIR / "3employee_prs_with_criticality.json"
FINAL_CALL_OUTPUT = OUTPUT_DIR / "4employee_tasks_with_metadata_finalCallData.json"
HANDOVER_OUTPUT = OUTPUT_DIR / "5employee_handovers.json"
DOCUMENTATION_OUTPUT = OUTPUT_DIR / "6employee_documents.json"

# ================= LLM HELPER FUNCTIONS =================

def call_llm(prompt: str, system_prompt: str = None, model: str = "gpt-4o-mini", temperature: float = 0.3) -> Optional[str]:
    """Call OpenAI API with error handling and fallback"""
    if not OPENAI_AVAILABLE or not openai_client:
        return None
    
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️  LLM call failed: {e}")
        return None

def detect_role_from_prs(employee: Dict[str, Any]) -> str:
    """Use LLM to detect employee role based on PRs they worked on"""
    tasks = employee.get("tasks", {}).get("ai", [])
    if not tasks:
        return employee.get("role", "Engineer")
    
    # Collect PR information
    pr_summaries = []
    for task in tasks[:10]:  # Limit to first 10 PRs for context
        title = task.get("title", "")
        changed_files = task.get("changed_files", [])
        file_types = [f.split('.')[-1] if '.' in f else 'unknown' for f in changed_files[:10]]
        
        pr_summaries.append({
            "title": title,
            "file_count": len(changed_files),
            "file_types": list(set(file_types)),
            "file_paths": changed_files[:5]  # First 5 files
        })
    
    # Create prompt for role detection
    prompt = f"""Based on the following PRs worked on by an employee, determine their most likely role.

PRs Summary:
{json.dumps(pr_summaries, indent=2)}

Common roles include: Mobile Developer, Backend Developer, Frontend Developer, Full Stack Engineer, DevOps Engineer, QA Engineer, Data Engineer, etc.

Respond with ONLY the role name (e.g., "Mobile Developer" or "Backend Developer"). No explanation needed."""

    system_prompt = "You are an expert at analyzing developer contributions to determine their role. Be precise and concise."
    
    detected_role = call_llm(prompt, system_prompt, temperature=0.2)
    
    if detected_role:
        # Clean up the response
        detected_role = detected_role.strip().strip('"').strip("'")
        # Validate it's a reasonable role
        if len(detected_role) < 50 and any(keyword in detected_role.lower() for keyword in 
            ['developer', 'engineer', 'architect', 'specialist', 'analyst', 'qa', 'devops']):
            return detected_role
    
    # Fallback to existing role or default
    return employee.get("role", "Engineer")

def categorize_task_with_llm(task: Dict[str, Any]) -> Dict[str, Any]:
    """Use LLM to categorize a task into sections"""
    title = task.get("title", "")
    changed_files = task.get("changed_files", [])
    criticality = task.get("criticality_score", 0)
    single_owner_files = task.get("single_owner_files", [])
    state = task.get("state", "closed")
    
    # Create context for LLM
    context = {
        "title": title,
        "criticality_score": criticality,
        "file_count": len(changed_files),
        "has_single_owner_files": len(single_owner_files) > 0,
        "state": state,
        "sample_files": changed_files[:5]
    }
    
    prompt = f"""Analyze this task and determine which sections it should belong to:

Task: {title}
Criticality Score: {criticality}/100
File Count: {len(changed_files)}
State: {state}
Has Single Owner Files: {len(single_owner_files) > 0}
Sample Files: {', '.join(changed_files[:5])}

Sections:
1. Final Call - Tasks requiring explanation, walkthrough, or knowledge transfer discussion
2. Handover - Tasks requiring ownership transfer to another team member
3. Documentation - Tasks requiring documentation creation or updates

Respond with a JSON object:
{{
  "final_call": true/false,
  "handover": true/false,
  "documentation": true/false,
  "reasoning": "brief explanation"
}}"""

    system_prompt = """You are an expert at categorizing development tasks for employee offboarding. 
    - Final Call: Complex tasks, high criticality, or tasks needing explanation
    - Handover: Active tasks, ownership concerns, or tasks needing reassignment
    - Documentation: Tasks that created/modified significant features or need documentation"""
    
    result = call_llm(prompt, system_prompt, temperature=0.3)
    
    if result:
        try:
            # Try to parse JSON from response
            json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "final_call": parsed.get("final_call", False),
                    "handover": parsed.get("handover", True),
                    "documentation": parsed.get("documentation", True),
                    "reasoning": parsed.get("reasoning", "")
                }
        except:
            pass
    
    # Fallback to rule-based
    return {
        "final_call": should_be_final_call(task),
        "handover": should_be_handover(task),
        "documentation": should_be_documentation(task),
        "reasoning": "Rule-based fallback"
    }

def generate_document_name_with_llm(task: Dict[str, Any]) -> str:
    """Use LLM to generate a better document name"""
    title = task.get("title", "")
    changed_files = task.get("changed_files", [])
    criticality = task.get("criticality_score", 0)
    
    prompt = f"""Generate a concise, professional document name for this task:

Task Title: {title}
Changed Files: {', '.join(changed_files[:10])}
Criticality: {criticality}/100

The document name should be:
- Clear and descriptive
- Professional (e.g., "API Documentation", "Deployment Guide", "Feature Specification")
- Specific to the task (not generic)

Respond with ONLY the document name. No quotes, no explanation."""

    system_prompt = "You are an expert at creating technical documentation names. Be concise and professional."
    
    doc_name = call_llm(prompt, system_prompt, temperature=0.4)
    
    if doc_name:
        doc_name = doc_name.strip().strip('"').strip("'")
        if len(doc_name) > 5 and len(doc_name) < 100:
            return doc_name
    
    # Fallback to rule-based
    return generate_document_name(task)

def generate_kt_types_with_llm(task: Dict[str, Any]) -> List[str]:
    """Use LLM to generate appropriate knowledge transfer types"""
    title = task.get("title", "")
    changed_files = task.get("changed_files", [])
    criticality = task.get("criticality_score", 0)
    
    prompt = f"""Determine the appropriate knowledge transfer types for this task:

Task: {title}
Files Changed: {len(changed_files)}
Criticality: {criticality}/100
Sample Files: {', '.join(changed_files[:5])}

Available KT Types:
- Code Walkthrough: For code changes
- Runbook: For infrastructure/config/deployment changes
- Call: For high-criticality or complex tasks
- Docs: For documentation needs

Respond with a JSON array of 2-3 most appropriate types, e.g., ["Code Walkthrough", "Call"]"""

    system_prompt = "You are an expert at determining knowledge transfer requirements. Select the most appropriate types."
    
    result = call_llm(prompt, system_prompt, temperature=0.3)
    
    if result:
        try:
            json_match = re.search(r'\[[^\]]+\]', result)
            if json_match:
                kt_types = json.loads(json_match.group())
                if isinstance(kt_types, list) and len(kt_types) >= 2:
                    return kt_types[:3]
        except:
            pass
    
    # Fallback to rule-based
    return generate_kt_types_for_handover(task)

# ================= RULE-BASED FALLBACKS =================

# Keywords for categorization
DOCUMENTATION_KEYWORDS = [
    "document", "documentation", "doc", "guide", "tutorial", "how-to",
    "runbook", "playbook", "readme", "wiki", "spec", "specification",
    "diagram", "architecture", "comment", "annotate"
]

HANDOVER_KEYWORDS = [
    "assign", "assignment", "owner", "ownership", "transfer", "handover",
    "hand off", "reassign", "reassignment", "take over", "new owner",
    "maintain", "maintenance", "on-call", "oncall", "responsibility", "responsible"
]

FINAL_CALL_KEYWORDS = [
    "explain", "explanation", "walkthrough", "discuss", "discussion",
    "meeting", "call", "review", "walk through", "clarify", "clarification",
    "q&a", "questions", "context", "background", "troubleshoot", "troubleshooting"
]

# File patterns
DOCUMENTATION_FILE_PATTERNS = [".md", ".mdx", ".txt", ".rst", ".drawio", ".png", ".svg"]
DOCUMENTATION_DIR_PATTERNS = ["docs/", "documentation/", "wiki/"]

# Priority mapping based on criticality
def map_criticality_to_priority(criticality_score):
    """Map criticality score to priority level"""
    if criticality_score >= 70:
        return "High"
    elif criticality_score >= 40:
        return "Medium"
    else:
        return "Low"

# Tag generation based on task properties
def generate_tags(task):
    """Generate tags based on task properties"""
    tags = []
    title = task.get("title", "").lower()
    changed_files = task.get("changed_files", [])
    file_paths = [f.lower() for f in changed_files]
    
    # State tags
    state = task.get("state", "").lower()
    if state == "closed":
        tags.append("Closed")
    elif state == "open":
        tags.append("Open")
    
    # File type tags
    if any("frontend" in f or "view" in f or "widget" in f or "ui" in f for f in file_paths):
        tags.append("Frontend")
    if any("backend" in f or "api" in f or "service" in f or "controller" in f for f in file_paths):
        tags.append("Backend")
    if any("infra" in f or "config" in f or "deploy" in f or "ci" in f or "gradle" in f for f in file_paths):
        tags.append("Infra")
    
    # Mobile-specific tags
    if any(".dart" in f or "flutter" in f or "android/" in f or "ios/" in f for f in file_paths):
        tags.append("Mobile")
    
    # Change size tags
    if len(changed_files) > 20:
        tags.append("Large Change")
    elif len(changed_files) > 5:
        tags.append("Medium Change")
    else:
        tags.append("Small Change")
    
    # Ownership tags
    if task.get("single_owner_files"):
        tags.append("Ownership")
    
    # Risk tags
    risk_score = task.get("risk_score", 0)
    if risk_score >= 80:
        tags.append("Risk")
    
    # Criticality tags
    criticality = task.get("criticality_score", 0)
    if criticality >= 70:
        tags.append("Critical")
    
    return tags if tags else ["General"]

# ================= FINAL CALL CATEGORIZATION =================

def should_be_final_call(task):
    """Determine if task should be in Final Call section"""
    title = task.get("title", "").lower()
    changed_files = task.get("changed_files", [])
    criticality = task.get("criticality_score", 0)
    single_owner_files = task.get("single_owner_files", [])
    
    # High criticality tasks often need explanation
    if criticality >= 70:
        return True
    
    # Tasks with single owner files need knowledge transfer
    if single_owner_files:
        return True
    
    # Check for keywords
    title_text = " ".join([title] + [f.lower() for f in changed_files[:5]])
    if any(keyword in title_text for keyword in FINAL_CALL_KEYWORDS):
        return True
    
    # Complex changes (many files) may need walkthrough
    if len(changed_files) > 15:
        return True
    
    # Check for critical files
    files_agg = task.get("files_aggregated", {})
    critical_files = files_agg.get("critical_files", [])
    if critical_files:
        return True
    
    return False

def enhance_final_call_task(task, employee_name):
    """Enhance task for Final Call section"""
    enhanced = task.copy()
    
    # Add priority based on criticality
    enhanced["priority"] = map_criticality_to_priority(task.get("criticality_score", 0))
    
    # Add tags
    enhanced["tags"] = generate_tags(task)
    
    # Add status
    state = task.get("state", "").lower()
    if state == "closed":
        enhanced["status"] = "completed"
    else:
        enhanced["status"] = "active"
    
    return enhanced

# ================= HANDOVER CATEGORIZATION =================

def should_be_handover(task):
    """Determine if task should be in Handover section"""
    # Most tasks with ownership concerns should be handovers
    single_owner_files = task.get("single_owner_files", [])
    if single_owner_files:
        return True
    
    # Active/open tasks need ownership transfer
    state = task.get("state", "").lower()
    if state == "open":
        return True
    
    # High criticality tasks need clear ownership
    criticality = task.get("criticality_score", 0)
    if criticality >= 50:
        return True
    
    return True  # Most tasks need handover

def generate_handover_from_task(task, employee_name, employee_id, employee_role, role_to_employees, assignment_counter, all_employees=None):
    """Generate handover item from task"""
    # Get new owner
    new_owner = get_next_owner_for_role(
        role_to_employees,
        employee_role,
        employee_id,
        assignment_counter,
        all_employees
    )
    
    if not new_owner:
        return None
    
    # Generate KT types (use LLM if available)
    kt_types = generate_kt_types_with_llm(task) if OPENAI_AVAILABLE else generate_kt_types_for_handover(task)
    
    # Determine status
    state = task.get("state", "").lower()
    priority = map_criticality_to_priority(task.get("criticality_score", 0))
    status = determine_handover_status(state, priority)
    
    return {
        "item": task.get("title", "Untitled Task"),
        "currentOwner": employee_name,
        "newOwner": new_owner.get("name", "Unknown"),
        "priority": priority,
        "status": status,
        "ktType": kt_types,
        "lastUpdated": generate_last_updated_for_handover()
    }

def generate_kt_types_for_handover(task):
    """Generate knowledge transfer types for handover (rule-based fallback)"""
    kt_types = []
    changed_files = task.get("changed_files", [])
    file_paths = [f.lower() for f in changed_files]
    criticality = task.get("criticality_score", 0)
    
    # Always include Code Walkthrough for code changes
    if any(f.endswith((".dart", ".py", ".js", ".ts", ".java", ".cpp", ".c")) for f in changed_files):
        kt_types.append("Code Walkthrough")
    
    # Add Runbook for infrastructure/config changes
    if any("infra" in f or "config" in f or "deploy" in f or "ci" in f or "gradle" in f for f in file_paths):
        kt_types.append("Runbook")
    
    # Add Call for critical tasks
    if criticality >= 70:
        kt_types.append("Call")
    
    # Ensure at least 2 types
    base_types = ["Code Walkthrough", "Runbook", "Call", "Docs"]
    while len(kt_types) < 2:
        remaining = [t for t in base_types if t not in kt_types]
        if remaining:
            kt_types.append(random.choice(remaining))
        else:
            break
    
    return kt_types[:3] if len(kt_types) > 3 else kt_types

def determine_handover_status(state, priority):
    """Determine handover status"""
    if state == "closed":
        return random.choice(["Completed", "In Progress"])
    elif priority == "High":
        return random.choice(["Pending", "In Progress"])
    else:
        return random.choice(["Pending", "In Progress", "Not Started"])

def generate_last_updated_for_handover():
    """Generate last updated timestamp for handover"""
    options = ["Just now", "1 hour ago", "2 hours ago", "Yesterday", "2 days ago", "3 days ago", "1 week ago"]
    weights = [0.2, 0.2, 0.15, 0.15, 0.1, 0.1, 0.1]
    return random.choices(options, weights=weights)[0]

# ================= DOCUMENTATION CATEGORIZATION =================

def should_be_documentation(task):
    """Determine if task should generate documentation"""
    # Most tasks need some documentation
    changed_files = task.get("changed_files", [])
    if not changed_files:
        return False
    
    # Check for documentation-related files
    if any(any(pattern in f.lower() for pattern in DOCUMENTATION_FILE_PATTERNS) for f in changed_files):
        return True
    
    # Check for documentation directories
    if any(any(pattern in f.lower() for pattern in DOCUMENTATION_DIR_PATTERNS) for f in changed_files):
        return True
    
    # Complex changes need documentation
    if len(changed_files) > 10:
        return True
    
    # High criticality tasks need documentation
    if task.get("criticality_score", 0) >= 50:
        return True
    
    return True  # Most tasks need documentation

def generate_document_from_task(task, employee_name):
    """Generate document item from task"""
    # Use LLM if available, otherwise fallback
    doc_name = generate_document_name_with_llm(task) if OPENAI_AVAILABLE else generate_document_name(task)
    priority = map_criticality_to_priority(task.get("criticality_score", 0))
    status = determine_document_status(task, priority)
    ai_followup = determine_ai_followup(task)
    last_updated = generate_last_updated_for_doc(status)
    
    return {
        "name": doc_name,
        "status": status,
        "priority": priority,
        "owner": employee_name,
        "aiFollowUp": ai_followup,
        "lastUpdated": last_updated
    }

def generate_document_name(task):
    """Generate document name based on task properties (rule-based fallback)"""
    title = task.get("title", "Untitled Task").lower()
    changed_files = task.get("changed_files", [])
    file_paths = [f.lower() for f in changed_files]
    
    document_templates = []
    
    # Check file types and paths
    if any("config" in f or "setting" in f for f in file_paths):
        document_templates.append("Configuration Guide")
    if any("api" in f or "service" in f or "endpoint" in f for f in file_paths):
        document_templates.append("API Documentation")
    if any("database" in f or "db" in f or "model" in f for f in file_paths):
        document_templates.append("Database Schema")
    if any("workflow" in f or "ci" in f or "deploy" in f for f in file_paths):
        document_templates.append("Deployment Guide")
    if any("test" in f for f in file_paths):
        document_templates.append("Testing Guide")
    
    # Mobile-specific
    if any(".dart" in f or "flutter" in f or "android/" in f or "ios/" in f for f in file_paths):
        document_templates.append("Mobile App Documentation")
    
    # Check task title
    if "fix" in title or "bug" in title:
        document_templates.append("Bug Fix Documentation")
    if "feat" in title or "feature" in title or "add" in title:
        document_templates.append("Feature Documentation")
    if "refactor" in title:
        document_templates.append("Refactoring Notes")
    
    # Check for frontend/backend indicators
    if any("frontend" in f or "view" in f or "widget" in f or "ui" in f for f in file_paths):
        document_templates.append("Frontend Architecture")
    if any("infra" in f or "config" in f or "deploy" in f for f in file_paths):
        document_templates.append("Infrastructure Setup")
    
    # Select base name
    if document_templates:
        base_name = random.choice(document_templates)
    else:
        base_name = random.choice([
            "System Overview", "Architecture Diagram", "Code Documentation",
            "Setup Guide", "Technical Specification", "Runbook"
        ])
    
    # Add component name if available
    if changed_files:
        first_file = changed_files[0]
        if "/" in first_file:
            parts = first_file.split("/")
            if len(parts) > 1:
                component = parts[-2].replace("_", " ").title()
                return f"{base_name} - {component}"
    
    return base_name

def determine_document_status(task, priority):
    """Determine document status"""
    if priority == "High":
        return random.choices(["Missing", "Partial", "Complete"], weights=[0.5, 0.3, 0.2])[0]
    elif priority == "Medium":
        return random.choices(["Missing", "Partial", "Complete"], weights=[0.4, 0.4, 0.2])[0]
    else:
        return random.choices(["Missing", "Partial", "Complete"], weights=[0.3, 0.4, 0.3])[0]

def determine_ai_followup(task):
    """Determine if AI follow-up is needed"""
    priority = map_criticality_to_priority(task.get("criticality_score", 0))
    criticality = task.get("criticality_score", 0)
    
    if priority == "High" or criticality >= 70:
        return random.choices([True, False], weights=[0.7, 0.3])[0]
    elif priority == "Medium" or criticality >= 50:
        return random.choices([True, False], weights=[0.5, 0.5])[0]
    else:
        return random.choices([True, False], weights=[0.3, 0.7])[0]

def generate_last_updated_for_doc(status):
    """Generate last updated timestamp for document"""
    if status == "Missing":
        return "Never"
    elif status == "Partial":
        return random.choice(["1 week ago", "2 weeks ago", "1 month ago", "Yesterday"])
    elif status == "Complete":
        return random.choice(["Yesterday", "2 days ago", "1 week ago"])
    else:
        return "Never"

# ================= OWNER ASSIGNMENT HELPERS =================

def build_role_to_employees_map(employees):
    """Build a map of role -> list of employees with that role"""
    role_map = defaultdict(list)
    for emp in employees:
        role = emp.get("role", "Engineer")
        role_map[role].append(emp)
    return role_map

def get_next_owner_for_role(role_map, role, current_owner_id, assignment_counter, all_employees=None):
    """Get the next owner for a role, ensuring even distribution"""
    # Try to find owner with same role
    if role in role_map and role_map[role]:
        # Filter out the current owner if provided
        available_owners = [e for e in role_map[role] if e.get("employeeId") != current_owner_id] if current_owner_id else role_map[role]
        
        if not available_owners:
            available_owners = role_map[role]
        
        # Use round-robin distribution
        if role not in assignment_counter:
            assignment_counter[role] = 0
        
        owner_index = assignment_counter[role] % len(available_owners)
        assignment_counter[role] += 1
        
        return available_owners[owner_index]
    
    # Fallback: use any available employee
    if all_employees:
        available = [e for e in all_employees if e.get("employeeId") != current_owner_id] if current_owner_id else all_employees
        if available:
            return random.choice(available)
    
    return None

# ================= MAIN PROCESSING =================

def main():
    """Main function to categorize and generate sections"""
    print("📂 Loading employee PRs with criticality data...")
    
    if not INPUT_FILE.exists():
        print(f"❌ Error: Input file not found: {INPUT_FILE}")
        return
    
    input_data = json.loads(INPUT_FILE.read_text(encoding="utf-8"))
    employees = input_data.get("employees", [])
    
    print(f"✓ Loaded {len(employees)} employees")
    
    if OPENAI_AVAILABLE:
        print("🤖 Using LLM for enhanced categorization and role detection...")
    else:
        print("⚠️  Using rule-based categorization (LLM not available)")
    
    # Detect and update roles based on PRs
    print("\n🔍 Detecting employee roles from PRs...")
    for emp in employees:
        detected_role = detect_role_from_prs(emp)
        original_role = emp.get("role", "Engineer")
        if detected_role != original_role:
            print(f"  {emp.get('name', 'Unknown')}: {original_role} → {detected_role}")
            emp["role"] = detected_role
    
    # Build role mapping for owner assignment
    role_to_employees = build_role_to_employees_map(employees)
    assignment_counter = defaultdict(int)
    
    print("\n🔧 Processing tasks and categorizing into sections...")
    
    # Initialize output structures
    final_call_output = {
        "generated_at": datetime.now().isoformat(),
        "total_employees": 0,
        "employees": []
    }
    
    handover_output = {
        "generated_at": datetime.now().isoformat(),
        "total_employees": 0,
        "employees": []
    }
    
    documentation_output = {
        "generated_at": datetime.now().isoformat(),
        "total_employees": 0,
        "employees": []
    }
    
    # Process each employee
    total_tasks = 0
    for idx, emp in enumerate(employees, 1):
        employee_id = emp.get("employeeId")
        employee_name = emp.get("name", "Unknown")
        employee_role = emp.get("role", "Engineer")
        
        tasks = emp.get("tasks", {})
        ai_tasks = tasks.get("ai", [])
        
        if not ai_tasks:
            continue
        
        total_tasks += len(ai_tasks)
        print(f"  Processing {employee_name} ({idx}/{len(employees)}): {len(ai_tasks)} tasks")
        
        # Initialize section lists
        final_call_tasks = []
        handovers = []
        documents = []
        
        handover_counter = 1
        document_counter = 1
        processed_doc_names = set()
        
        # Process each task
        for task in ai_tasks:
            # Use LLM categorization if available
            if OPENAI_AVAILABLE:
                categorization = categorize_task_with_llm(task)
                should_final_call = categorization["final_call"]
                should_handover = categorization["handover"]
                should_doc = categorization["documentation"]
            else:
                should_final_call = should_be_final_call(task)
                should_handover = should_be_handover(task)
                should_doc = should_be_documentation(task)
            
            # Final Call: Enhance existing task
            if should_final_call:
                enhanced_task = enhance_final_call_task(task, employee_name)
                final_call_tasks.append(enhanced_task)
            
            # Handover: Generate handover item
            if should_handover:
                handover = generate_handover_from_task(
                    task, employee_name, employee_id, employee_role,
                    role_to_employees, assignment_counter, employees
                )
                if handover:
                    handover["id"] = f"h{handover_counter}"
                    handovers.append(handover)
                    handover_counter += 1
            
            # Documentation: Generate document item
            if should_doc:
                doc = generate_document_from_task(task, employee_name)
                doc_name = doc["name"]
                
                # Avoid exact duplicates
                if doc_name in processed_doc_names:
                    doc_name = f"{doc_name} (v{document_counter})"
                    doc["name"] = doc_name
                
                processed_doc_names.add(doc_name)
                doc["id"] = f"d{document_counter}"
                documents.append(doc)
                document_counter += 1
        
        # Add to outputs if there are items
        if final_call_tasks:
            final_call_output["employees"].append({
                "employeeId": employee_id,
                "name": employee_name,
                "role": employee_role,
                "risk": emp.get("risk", "medium"),
                "status": emp.get("status", "active"),
                "lastDay": emp.get("lastDay"),
                "tasks": {
                    "ai": final_call_tasks,
                    "manager": tasks.get("manager", [])
                }
            })
        
        if handovers:
            handover_output["employees"].append({
                "employeeId": employee_id,
                "handovers": handovers
            })
        
        if documents:
            documentation_output["employees"].append({
                "employeeId": employee_id,
                "documents": documents
            })
    
    # Set totals
    final_call_output["total_employees"] = len(final_call_output["employees"])
    handover_output["total_employees"] = len(handover_output["employees"])
    documentation_output["total_employees"] = len(documentation_output["employees"])
    
    # Write outputs
    print("\n💾 Writing output files...")
    
    FINAL_CALL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    FINAL_CALL_OUTPUT.write_text(
        json.dumps(final_call_output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"✓ Final Call: {FINAL_CALL_OUTPUT}")
    
    HANDOVER_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    HANDOVER_OUTPUT.write_text(
        json.dumps(handover_output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"✓ Handover: {HANDOVER_OUTPUT}")
    
    DOCUMENTATION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DOCUMENTATION_OUTPUT.write_text(
        json.dumps(documentation_output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"✓ Documentation: {DOCUMENTATION_OUTPUT}")
    
    # Print summary
    print("\n✅ Processing completed successfully!")
    print("\n📊 Summary:")
    
    # Final Call summary
    total_final_call_tasks = sum(len(emp["tasks"]["ai"]) for emp in final_call_output["employees"])
    print(f"\n📞 Final Call Section:")
    print(f"   Employees: {final_call_output['total_employees']}")
    print(f"   Tasks: {total_final_call_tasks}")
    
    # Handover summary
    total_handovers = sum(len(emp["handovers"]) for emp in handover_output["employees"])
    print(f"\n🔄 Handover Section:")
    print(f"   Employees: {handover_output['total_employees']}")
    print(f"   Handovers: {total_handovers}")
    
    # Documentation summary
    total_documents = sum(len(emp["documents"]) for emp in documentation_output["employees"])
    all_docs = [d for emp in documentation_output["employees"] for d in emp["documents"]]
    missing = sum(1 for d in all_docs if d["status"] == "Missing")
    partial = sum(1 for d in all_docs if d["status"] == "Partial")
    complete = sum(1 for d in all_docs if d["status"] == "Complete")
    
    print(f"\n📄 Documentation Section:")
    print(f"   Employees: {documentation_output['total_employees']}")
    print(f"   Documents: {total_documents}")
    print(f"   Missing: {missing}, Partial: {partial}, Complete: {complete}")
    
    print(f"\n📈 Total tasks processed: {total_tasks}")


if __name__ == "__main__":
    main()
